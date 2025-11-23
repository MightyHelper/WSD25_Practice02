import logging
import time
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger: logging.Logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process the request and log relevant information."""
        client_host: str = request.client.host if request.client else "unknown"
        logger.info("%s - %s %s", client_host, request.method, request.url.path)

        start_time: float = time.time()
        try:
            response: Response = await call_next(request)
            process_time: float = (time.time() - start_time) * 1000
            logger.info(
                "%s - %s %s - %d - %.2fms",
                client_host,
                request.method,
                request.url.path,
                response.status_code,
                process_time
            )
            return response
        except Exception as e:
            logger.error("Error processing request: %s", str(e), exc_info=True)
            raise
