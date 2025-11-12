import logging
import math
import time
from typing import Any, Callable, Optional, Self, Awaitable

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from . import constants as const

# In-memory storage
motd: Optional[str] = const.DEFAULT_MOTD
special_numbers: set[int] = set()

# Rate limiting storage
request_timestamps: dict[str, list[float]] = {}
blacklisted_ips: dict[str, float] = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger: logging.Logger = logging.getLogger(__name__)

# Custom exceptions
from .errors import (
    APIError,
    NumberTooLargeError,
    NumberNotIntegerError,
    ResourceExistsError,
    ResourceNotFoundError,
    MethodNotAllowedError,
    RateLimitExceededError,
    EnhanceYourCalmError,
    TeapotError,
)


# Response Models

class APIResponse[T](BaseModel):
    """Standard API response format."""
    status: str
    data: T

    @classmethod
    def success(cls, data: T, status_code: int = const.HTTP_200_OK) -> Self:
        """Create a successful API response."""
        return cls(status=str(status_code), data=data)

    @classmethod
    def error(cls, error: APIError) -> 'APIResponse[dict[str, APIError]]':
        """Create an error API response."""
        return cls(  # type: ignore
            status=str(error.status_code),
            data={"error": error.detail}  # type: ignore
        )


class JSONProblem(BaseModel):
    """Standard error response format following RFC 7807."""
    status: str
    title: str
    detail: str
    detail_obj: Any
    type: str = "about:blank"

    @classmethod
    def from_exception(cls, exc: Exception) -> 'JSONProblem':
        """Create a JSON problem from an exception."""
        if isinstance(exc, APIError):
            return cls(
                status=str(exc.status_code),
                title=exc.title,
                detail=exc.detail,
                detail_obj=exc.detail,
                type=f"https://http.cat/{exc.status_code}"
            )
        return cls(
            status=str(const.HTTP_500_INTERNAL_SERVER_ERROR),
            title="Internal Server Error",
            detail=const.ERROR_INTERNAL_SERVER,
            detail_obj=const.ERROR_INTERNAL_SERVER,
            type="https://http.cat/500"
        )


# Request Models
class MOTDUpdate(BaseModel):
    """Model for updating the Message of the Day."""
    message: str = Field(
        ...,
        min_length=const.MOTD_MIN_LENGTH,
        max_length=const.MOTD_MAX_LENGTH,
        description="The message to display as the Message of the Day"
    )


class NumberRequest(BaseModel):
    """Base model for number-based requests."""
    number: int = Field(..., gt=0, description="A positive integer")

    @field_validator('number')
    @classmethod
    def validate_number(cls, v: int) -> int:
        """Validate that the number is positive."""
        if v <= 0:
            raise ValueError('Number must be positive')
        return v


class PrimeCheckRequest(NumberRequest):
    """Model for prime number check requests."""

    @field_validator('number')
    @classmethod
    def validate_number_size(cls, v: int) -> int:
        """Validate that the number is within the allowed range."""
        if v > const.PRIME_NUMBER_MAX:
            raise NumberTooLargeError()
        return v


# Middleware
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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process the request with rate limiting."""
        client_ip: str = request.client.host if request.client else "unknown"
        current_time: float = time.time()

        # Clean up old blacklisted IPs
        self._cleanup_blacklisted_ips(current_time)

        if not self._should_apply_rate_limit(request):
            return await call_next(request)

        # Check if IP is blacklisted
        if client_ip in blacklisted_ips:
            return self._blacklisted_response()

        # Initialize request timestamps for this IP
        if client_ip not in request_timestamps:
            request_timestamps[client_ip] = []

        # Process rate limiting
        response = await self._process_rate_limit(client_ip, current_time, request, call_next)
        return response

    @staticmethod
    def _should_apply_rate_limit(request: Request) -> bool:
        """Determine if rate limiting should be applied to the request."""
        return request.url.path in ["/redoc", "/docs"]

    @staticmethod
    def _cleanup_blacklisted_ips(current_time: float) -> None:
        """Remove expired IPs from the blacklist."""
        expired_ips = [
            ip for ip, expiry in blacklisted_ips.items()
            if expiry < current_time
        ]
        for ip in expired_ips:
            del blacklisted_ips[ip]

    @staticmethod
    def _blacklisted_response() -> JSONResponse:
        """Create a response for blacklisted IPs."""
        return JSONResponse(
            status_code=const.HTTP_418_IM_A_TEAPOT,
            content=JSONProblem(
                status=str(const.HTTP_418_IM_A_TEAPOT),
                title="I'm a teapot",
                detail=const.ERROR_BLACKLISTED_IP,
                detail_obj=const.ERROR_BLACKLISTED_IP,
                type=f"https://http.cat/{const.HTTP_418_IM_A_TEAPOT}"
            ).model_dump()
        )

    async def _process_rate_limit(
            self,
            client_ip: str,
            current_time: float,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process rate limiting for the request."""
        timestamps = request_timestamps[client_ip]
        window_start = current_time - const.RATE_LIMIT_WINDOW_SECONDS

        # Remove old timestamps outside the current window
        recent_timestamps = [ts for ts in timestamps if ts > window_start]

        # Check for too many requests
        if len(recent_timestamps) >= const.RATE_LIMIT_MAX_REQUESTS:
            return self._handle_rate_limit_exceeded(client_ip, current_time)

        # Check for too frequent requests
        if self._is_too_frequent(recent_timestamps, current_time):
            return self._enhance_your_calm_response()

        # Check standard rate limit
        if recent_timestamps:
            response = self._check_standard_rate_limit(
                recent_timestamps[0],
                current_time
            )
            if response:
                return response

        # Update timestamps and process the request
        recent_timestamps.append(current_time)
        request_timestamps[client_ip] = recent_timestamps[-const.MAX_TIMESTAMPS_STORED:]

        return await call_next(request)

    @staticmethod
    def _is_too_frequent(timestamps: list[float], current_time: float) -> bool:
        """Check if requests are coming in too quickly."""
        return (
                len(timestamps) > 0 and
                (current_time - timestamps[-1]) < const.RATE_LIMIT_MIN_INTERVAL
        )

    @staticmethod
    def _enhance_your_calm_response() -> JSONResponse:
        """Create a 420 Enhance Your Calm response."""
        return JSONResponse(
            status_code=const.HTTP_420_ENHANCE_YOUR_CALM,
            content=JSONProblem(
                status=str(const.HTTP_420_ENHANCE_YOUR_CALM),
                title="Enhance Your Calm",
                detail="You are being rate limited",
                detail_obj="You are being rate limited",
                type=f"https://http.cat/{const.HTTP_420_ENHANCE_YOUR_CALM}"
            ).model_dump()
        )

    @staticmethod
    def _handle_rate_limit_exceeded(
            client_ip: str,
            current_time: float
    ) -> JSONResponse:
        """Handle rate limit exceeded by blacklisting the IP."""
        blacklisted_ips[client_ip] = current_time + const.BLACKLIST_DURATION
        return JSONResponse(
            status_code=const.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(int(const.BLACKLIST_DURATION))},
            content=JSONProblem(
                status=str(const.HTTP_429_TOO_MANY_REQUESTS),
                title="Too Many Requests",
                detail=(
                    f"Rate limit exceeded. You have been blacklisted for "
                    f"{int(const.BLACKLIST_DURATION)} seconds."
                ),
                detail_obj=(
                    f"Rate limit exceeded. You have been blacklisted for "
                    f"{int(const.BLACKLIST_DURATION)} seconds."
                ),
                type=f"https://http.cat/{const.HTTP_429_TOO_MANY_REQUESTS}"
            ).model_dump()
        )

    @staticmethod
    def _check_standard_rate_limit(
            first_timestamp: float,
            current_time: float
    ) -> Optional[JSONResponse]:
        """Check standard rate limit (1 request per second)."""
        time_since_first = current_time - first_timestamp

        if time_since_first < const.RATE_LIMIT_WINDOW_SECONDS:
            retry_after = int(const.RATE_LIMIT_WINDOW_SECONDS - time_since_first) + 1
            return JSONResponse(
                status_code=const.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(retry_after)},
                content=JSONProblem(
                    status=str(const.HTTP_429_TOO_MANY_REQUESTS),
                    title="Too Many Requests",
                    detail=(
                        f"Rate limit exceeded. Try again in {retry_after} seconds."
                    ),
                    detail_obj=(
                        f"Rate limit exceeded. Try again in {retry_after} seconds."
                    ),
                    type=f"https://http.cat/{const.HTTP_429_TOO_MANY_REQUESTS}"
                ).model_dump()
            )
        return None


# Helper functions
def is_prime(n: int) -> bool:
    """Check if a number is prime.

    Args:
        n: The number to check.

    Returns:
        bool: True if the number is prime, False otherwise.
    """
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2

    # Check odd divisors up to square root
    sqrt_n = int(math.isqrt(n)) + 1
    for i in range(3, sqrt_n, 2):
        if n % i == 0:
            return False
    return True


def create_app(enable_rate_limiting: bool = True) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=const.API_TITLE,
        description=const.API_DESCRIPTION,
        version=const.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add middleware
    app.add_middleware(LoggingMiddleware)
    if enable_rate_limiting:
        app.add_middleware(RateLimitMiddleware)

    # Exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        """Handle API errors."""
        problem = JSONProblem.from_exception(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump()
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
            request: Request,
            exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        problem = JSONProblem(
            status=str(exc.status_code),
            title=exc.detail,
            detail=str(exc.detail),
            detail_obj=exc.detail,
            type=f"https://http.cat/{exc.status_code}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
            request: Request,
            exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        problem = JSONProblem(
            status=str(const.HTTP_422_UNPROCESSABLE_CONTENT),
            title="Unprocessable Entity",
            detail=str(exc.errors()),
            detail_obj=exc.errors(),
            type=f"https://http.cat/{const.HTTP_422_UNPROCESSABLE_CONTENT}"
        )
        return JSONResponse(
            status_code=const.HTTP_422_UNPROCESSABLE_CONTENT,
            content=problem.model_dump()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
            request: Request,
            exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions."""
        logger.error("Unhandled exception: %s", str(exc), exc_info=True)
        problem = JSONProblem(
            status=str(const.HTTP_500_INTERNAL_SERVER_ERROR),
            title="Internal Server Error",
            detail=const.ERROR_INTERNAL_SERVER,
            detail_obj=const.ERROR_INTERNAL_SERVER,
            type=f"https://http.cat/{const.HTTP_500_INTERNAL_SERVER_ERROR}"
        )
        return JSONResponse(
            status_code=const.HTTP_500_INTERNAL_SERVER_ERROR,
            content=problem.model_dump()
        )

    # Root endpoint
    @app.get("/", response_model=APIResponse[dict[str, Any]])
    async def motd_get() -> dict[str, Any]:
        """Root endpoint that returns a welcome message and the current MOTD.

        Returns:
            Dict containing a welcome message and the current MOTD.
        """
        return APIResponse[dict[str, Any]].success(
            data={
                "Hello": "World",
                "last_motd": motd
            }
        ).model_dump()

    # Block other HTTP methods on root
    @app.delete("/", response_model=APIResponse[dict[str, str]], include_in_schema=False)
    @app.post("/", response_model=APIResponse[dict[str, str]], include_in_schema=False)
    @app.put("/", response_model=APIResponse[dict[str, str]], include_in_schema=False)
    async def method_not_allowed() -> dict[str, Any]:
        """Handle unsupported HTTP methods on the root endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error for unsupported methods.
        """
        raise MethodNotAllowedError(const.ERROR_METHOD_NOT_ALLOWED)

    # MOTD endpoints
    @app.put(
        "/motd",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK
    )
    async def motd_put(update: MOTDUpdate) -> dict[str, Any]:
        """Update the Message of the Day.

        Args:
            update: The new MOTD message.

        Returns:
            A success response if the MOTD was updated.
        """
        global motd
        motd = update.message
        return APIResponse[dict[str, bool]].success(
            data={"ok": True},
            status_code=status.HTTP_200_OK
        ).model_dump()

    @app.delete(
        "/motd",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK
    )
    async def motd_delete() -> dict[str, Any]:
        """Delete the current Message of the Day.

        Returns:
            A success response if the MOTD was deleted.

        Raises:
            ResourceNotFoundError: If there is no MOTD to delete.
        """
        global motd
        if motd is None:
            raise ResourceNotFoundError("MOTD")
        motd = None
        return APIResponse[dict[str, bool]].success(
            data={"ok": True},
            status_code=status.HTTP_200_OK
        ).model_dump()

    @app.post(
        "/motd",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        include_in_schema=False
    )
    async def post_motd_not_allowed() -> None:
        """Handle POST requests to the MOTD endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error as POST is not allowed.
        """
        raise MethodNotAllowedError("POST")

    # IP endpoint
    @app.get(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_200_OK
    )
    async def ip_get(request: Request) -> dict[str, Any]:
        """Get the IP address of the client making the request.

        Args:
            request: The incoming request.

        Returns:
            A response containing the client's IP address.
        """
        client_host: str = request.client.host if request.client else "unknown"
        return APIResponse[dict[str, str]].success(
            data={"ip": client_host},
            status_code=status.HTTP_200_OK
        ).model_dump()

    # Block other HTTP methods on /my_ip
    @app.delete(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )
    @app.post(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )
    @app.put(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        include_in_schema=False
    )
    async def my_ip_method_not_allowed() -> None:
        """Handle unsupported HTTP methods on the /my_ip endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error for unsupported methods.
        """
        raise MethodNotAllowedError(const.ERROR_METHOD_NOT_ALLOWED)

    # Special number endpoints
    @app.post(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_201_CREATED
    )
    async def special_number_create(number_req: NumberRequest, response: Response) -> dict[str, Any]:
        """Add a new special number.

        Args:
            number_req: The number to add.

        Returns:
            A success response if the number was added.

        Raises:
            ResourceExistsError: If the number is already special.
        """
        if number_req.number in special_numbers:
            raise ResourceExistsError("Number")
        special_numbers.add(number_req.number)
        # Kinda sucks to have to do this and if the project was serious would probably have some better way to do this...
        response.status_code = status.HTTP_201_CREATED
        return APIResponse[dict[str, bool]].success(
            data={"ok": True},
            status_code=status.HTTP_201_CREATED
        ).model_dump()

    @app.put(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        responses={
            status.HTTP_200_OK: {"description": "Number was already special"},
            status.HTTP_201_CREATED: {"description": "Number was added to special numbers"}
        }
    )
    async def special_number_update(number_req: NumberRequest, response: Response) -> dict[str, Any]:
        """Add or update a special number.

        Args:
            number_req: The number to add or update.

        Returns:
            A success response with status 200 if the number was already special,
            or 201 if it was newly added.
        """
        if number_req.number in special_numbers:
            return APIResponse[dict[str, bool]].success(
                data={"ok": True},
                status_code=status.HTTP_200_OK
            ).model_dump()

        special_numbers.add(number_req.number)
        # Kinda sucks to have to do this and if the project was serious would probably have some better way to do this...
        response.status_code = status.HTTP_201_CREATED
        return APIResponse[dict[str, bool]].success(
            data={"ok": True},
            status_code=status.HTTP_201_CREATED
        ).model_dump()

    @app.delete(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK
    )
    async def special_number_delete(number_req: NumberRequest) -> dict[str, Any]:
        """Remove a number from the special numbers set.

        Args:
            number_req: The number to remove.

        Returns:
            A success response if the number was removed.

        Raises:
            ResourceNotFoundError: If the number was not special.
        """
        if number_req.number not in special_numbers:
            raise ResourceNotFoundError("Number")
        special_numbers.remove(number_req.number)
        return APIResponse[dict[str, bool]].success(
            data={"ok": True},
            status_code=status.HTTP_200_OK
        ).model_dump()

    @app.get(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK
    )
    async def special_number_get(number: int) -> dict[str, Any]:
        """Check if a number is special.

        Args:
            number: The number to check.

        Returns:
            A success response if the number is special.

        Raises:
            ResourceNotFoundError: If the number is not special.
        """
        if number not in special_numbers:
            raise ResourceNotFoundError("Number")
        return APIResponse[dict[str, bool]].success(
            data={"ok": True},
            status_code=status.HTTP_200_OK
        ).model_dump()

    # Prime number endpoints
    @app.post(
        "/is_prime",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_402_PAYMENT_REQUIRED: {
                "description": "Number is too large for current payment plan"
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Invalid number provided"
            }
        }
    )
    async def check_prime(prime_req: PrimeCheckRequest) -> dict[str, Any]:
        """Check if a number is prime.

        Args:
            prime_req: The number to check.

        Returns:
            A response indicating if the number is prime.

        Raises:
            NumberTooLargeError: If the number is too large to check.
        """
        return APIResponse[dict[str, bool]].success(
            data={"is_prime": is_prime(prime_req.number)},
            status_code=status.HTTP_200_OK
        ).model_dump()

    # Block other HTTP methods on /is_prime
    @app.get(
        "/is_prime",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        include_in_schema=False
    )
    async def get_prime_not_allowed() -> None:
        """Handle GET requests to the /is_prime endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error as GET is not allowed.
        """
        raise MethodNotAllowedError("GET")

    @app.put(
        "/is_prime",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        include_in_schema=False
    )
    async def put_prime_not_implemented() -> dict[str, Any]:
        """Handle PUT requests to the /is_prime endpoint.

        Returns:
            A response indicating that the operation is not implemented.
        """
        return APIResponse[dict[str, str]](
            status=str(status.HTTP_501_NOT_IMPLEMENTED),
            data={
                "error": (
                    "Not implemented, I am sure I can make any number you want a prime number, "
                    "but this HTTP response body is too small..."
                )
            }
        ).model_dump()

    @app.delete(
        "/is_prime",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        include_in_schema=False
    )
    async def delete_prime_not_implemented() -> dict[str, Any]:
        """Handle DELETE requests to the /is_prime endpoint.

        Returns:
            A response indicating that the operation is not implemented.
        """
        return APIResponse[dict[str, str]](
            status=str(status.HTTP_501_NOT_IMPLEMENTED),
            data={
                "error": (
                    "Not implemented, I am sure I can stop any number you want from being a prime number, "
                    "but this HTTP response body is too small..."
                )
            }
        ).model_dump()

    # Health check endpoint
    @app.get(
        "/health",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_200_OK
    )
    async def health_check() -> dict[str, Any]:
        """Health check endpoint.

        Returns:
            A response indicating the service is healthy.
        """
        return APIResponse[dict[str, str]].success(
            data={"status": "healthy"},
            status_code=status.HTTP_200_OK
        ).model_dump()

    return app


real_app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "practice02.main:real_app",
        host=const.DEFAULT_HOST,
        port=const.DEFAULT_PORT,
        reload=True
    )
