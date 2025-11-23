import logging
import time
from http import HTTPStatus
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from .. import constants as const
from ..errors import ENHANCE_YOUR_CALM
from ..response.json_response import JSONProblem
from ..state import State

logger: logging.Logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request with rate limiting."""
        client_ip: str = request.client.host if request.client else "unknown"
        current_time: float = time.time()

        # Clean up old blacklisted IPs
        self._cleanup_blacklisted_ips(current_time)

        if not self._should_apply_rate_limit(request):
            return await call_next(request)

        # Check if IP is blacklisted
        if client_ip in State.blacklisted_ips:
            return self._blacklisted_response()

        # Initialize request timestamps for this IP
        if client_ip not in State.request_timestamps:
            State.request_timestamps[client_ip] = []

        # Process rate limiting
        response = await self._process_rate_limit(
            client_ip, current_time, request, call_next
        )
        return response

    @staticmethod
    def _should_apply_rate_limit(request: Request) -> bool:
        """Determine if rate limiting should be applied to the request."""
        return request.url.path not in ["/redoc", "/docs", "/openapi.json"]

    @staticmethod
    def _cleanup_blacklisted_ips(current_time: float) -> None:
        """Remove expired IPs from the blacklist."""
        expired_ips = [
            ip for ip, expiry in State.blacklisted_ips.items() if expiry < current_time
        ]
        for ip in expired_ips:
            del State.blacklisted_ips[ip]

    @staticmethod
    def _blacklisted_response() -> JSONResponse:
        """Create a response for blacklisted IPs."""
        return JSONResponse(
            status_code=HTTPStatus.IM_A_TEAPOT,
            content=JSONProblem(
                status=str(HTTPStatus.IM_A_TEAPOT),
                title="I'm a teapot",
                detail=HTTPStatus.IM_A_TEAPOT.description
                + "\n"
                + const.ERROR_BLACKLISTED_IP,
                detail_obj=HTTPStatus.IM_A_TEAPOT.description
                + "\n"
                + const.ERROR_BLACKLISTED_IP,
                type=f"https://http.cat/{HTTPStatus.IM_A_TEAPOT}",
            ).model_dump(),
        )

    async def _process_rate_limit(
        self,
        client_ip: str,
        current_time: float,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process rate limiting for the request."""
        timestamps = State.request_timestamps[client_ip]
        window_start = current_time - const.RATE_LIMIT_WINDOW_SECONDS

        # Remove old timestamps outside the current window
        recent_timestamps = [ts for ts in timestamps if ts > window_start]
        logger.info(f"{len(recent_timestamps)} / ({len(timestamps)}) recent requests by {client_ip}")
        # Check for too many requests
        should_blacklist = len(recent_timestamps) >= const.RATE_LIMIT_WINDOW_MAX_REQUESTS
        requests_too_frequent = self._is_too_frequent(recent_timestamps, current_time)
        # Update timestamps and process the request
        recent_timestamps.append(current_time)
        State.request_timestamps[client_ip] = recent_timestamps[
            -const.MAX_TIMESTAMPS_STORED:
        ]
        if should_blacklist:
            return self._blacklist_ip(client_ip, current_time)
        if requests_too_frequent:
            return self._request_too_frequent_response()

        return await call_next(request)

    @staticmethod
    def _is_too_frequent(timestamps: list[float], current_time: float) -> bool:
        """Check if requests are coming in too quickly."""
        return (
            len(timestamps) > 0
            and (current_time - timestamps[-1]) < const.RATE_LIMIT_MIN_INTERVAL
        )

    @staticmethod
    def _request_too_frequent_response() -> JSONResponse:
        """Create a 420 Enhance Your Calm response."""
        return JSONResponse(
            status_code=ENHANCE_YOUR_CALM,
            content=JSONProblem(
                status=str(ENHANCE_YOUR_CALM),
                title="Enhance Your Calm",
                detail="You are being rate limited",
                detail_obj="You are being rate limited",
                type=f"https://http.cat/{ENHANCE_YOUR_CALM}",
            ).model_dump(),
        )

    @staticmethod
    def _blacklist_ip(
        client_ip: str, current_time: float
    ) -> JSONResponse:
        """Handle rate limit exceeded by blacklisting the IP."""
        State.blacklisted_ips[client_ip] = current_time + const.BLACKLIST_DURATION
        logger.warning(f"Blacklisted IP: {client_ip}")
        return JSONResponse(
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            headers={"Retry-After": str(int(const.BLACKLIST_DURATION))},
            content=JSONProblem(
                status=str(HTTPStatus.TOO_MANY_REQUESTS),
                title="Too Many Requests",
                detail=(
                    f"Rate limit exceeded. You have been blacklisted for "
                    f"{int(const.BLACKLIST_DURATION)} seconds."
                ),
                detail_obj=(
                    f"Rate limit exceeded. You have been blacklisted for "
                    f"{int(const.BLACKLIST_DURATION)} seconds."
                ),
                type=f"https://http.cat/{HTTPStatus.TOO_MANY_REQUESTS}",
            ).model_dump(),
        )
