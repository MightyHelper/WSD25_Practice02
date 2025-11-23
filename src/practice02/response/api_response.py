from http import HTTPStatus
from typing import Self

from pydantic import BaseModel

from ..errors import APIError


class APIResponse[T](BaseModel):
    """Standard API response format."""
    status: str
    data: T

    @classmethod
    def success(cls, data: T, status_code: int = HTTPStatus.OK) -> Self:
        """Create a successful API response."""
        return cls(status=str(status_code), data=data)

def get_error_api_response(error: APIError) -> APIResponse[dict[str, str]]:
    return APIResponse(
        status=str(error.status_code),
        data={"error": error.detail}
    )