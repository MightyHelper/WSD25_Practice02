from pydantic import BaseModel, Field, field_validator


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
