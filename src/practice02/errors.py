from . import constants as const

class APIError(Exception):
    """Base class for API errors."""
    status_code: int
    title: str
    detail: str

    def __init__(self, status_code: int, title: str, detail: str) -> None:
        self.status_code = status_code
        self.title = title
        self.detail = detail
        super().__init__(detail)

class NumberTooLargeError(APIError):
    """Raised when a number exceeds the allowed limit."""
    def __init__(self, detail: str = const.ERROR_NUMBER_TOO_LARGE) -> None:
        super().__init__(const.HTTP_402_PAYMENT_REQUIRED, "Payment Required", detail)

class NumberNotIntegerError(APIError):
    """Raised when a non-integer value is provided where an integer is expected."""
    def __init__(self, detail: str = const.ERROR_VALIDATION) -> None:
        super().__init__(const.HTTP_422_UNPROCESSABLE_CONTENT, "Unprocessable Entity", detail)

class ResourceExistsError(APIError):
    """Raised when trying to create a resource that already exists."""
    def __init__(self, resource: str) -> None:
        super().__init__(const.HTTP_409_CONFLICT, "Conflict", f"{resource} already exists")

class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource: str) -> None:
        super().__init__(const.HTTP_404_NOT_FOUND, "Not Found", f"{resource} not found")

class MethodNotAllowedError(APIError):
    """Raised when an unsupported HTTP method is used."""
    def __init__(self, method: str) -> None:
        super().__init__(
            const.HTTP_405_METHOD_NOT_ALLOWED,
            "Method Not Allowed",
            f"{method} method not allowed"
        )

class RateLimitExceededError(APIError):
    """Raised when the rate limit is exceeded."""
    def __init__(self, retry_after: int) -> None:
        super().__init__(
            const.HTTP_429_TOO_MANY_REQUESTS,
            "Too Many Requests",
            const.ERROR_RATE_LIMIT_EXCEEDED
        )
        self.retry_after = retry_after

class EnhanceYourCalmError(APIError):
    """Raised when requests are coming in too quickly."""
    def __init__(self) -> None:
        super().__init__(
            const.HTTP_420_ENHANCE_YOUR_CALM,
            "Enhance Your Calm",
            "You are being rate limited"
        )

class TeapotError(APIError):
    """Raised when an IP is blacklisted."""
    def __init__(self) -> None:
        super().__init__(
            const.HTTP_418_IM_A_TEAPOT,
            "I'm a teapot",
            const.ERROR_BLACKLISTED_IP
        )
