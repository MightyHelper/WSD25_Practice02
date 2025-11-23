from http import HTTPStatus
from typing import Any

from pydantic import BaseModel

from ..errors import APIError


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
            status=str(HTTPStatus.INTERNAL_SERVER_ERROR),
            title="Internal Server Error",
            detail=HTTPStatus.INTERNAL_SERVER_ERROR.description,
            detail_obj=HTTPStatus.INTERNAL_SERVER_ERROR.description,
            type="https://http.cat/500"
        )
