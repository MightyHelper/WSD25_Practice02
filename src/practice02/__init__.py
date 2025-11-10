"""Practice 02 package."""

from .main import real_app
from .errors import (
    APIError,
    MethodNotAllowedError,
    NumberTooLargeError,
    NumberNotIntegerError,
    ResourceExistsError,
    ResourceNotFoundError,
)

__all__ = [
    "real_app",
    "APIError",
    "MethodNotAllowedError",
    "NumberTooLargeError",
    "NumberNotIntegerError",
    "ResourceExistsError",
    "ResourceNotFoundError",
]