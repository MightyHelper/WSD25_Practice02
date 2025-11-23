from http import HTTPStatus
from typing import Final

from . import constants as const

ENHANCE_YOUR_CALM: Final[int] = 420

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
        super().__init__(HTTPStatus.PAYMENT_REQUIRED, "Payment Required", detail)

class ResourceExistsError(APIError):
    """Raised when trying to create a resource that already exists."""
    def __init__(self, resource: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, "Conflict", f"{resource} already exists")

class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, "Not Found", f"{resource} not found")

class MethodNotAllowedError(APIError):
    """Raised when an unsupported HTTP method is used."""
    def __init__(self, method: str) -> None:
        super().__init__(
            HTTPStatus.METHOD_NOT_ALLOWED,
            "Method Not Allowed",
            f"{method} method not allowed"
        )
