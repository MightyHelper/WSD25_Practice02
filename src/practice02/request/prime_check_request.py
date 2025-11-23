from pydantic import field_validator

from .. import constants as const
from ..errors import NumberTooLargeError
from ..request.number_request import NumberRequest


class PrimeCheckRequest(NumberRequest):
    """Model for prime number check requests."""

    @field_validator('number')
    @classmethod
    def validate_number_size(cls, v: int) -> int:
        """Validate that the number is within the allowed range."""
        if v > const.PRIME_NUMBER_MAX:
            raise NumberTooLargeError()
        return v
