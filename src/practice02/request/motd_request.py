from pydantic import BaseModel, Field

from .. import constants as const


class MOTDUpdate(BaseModel):
    """Model for updating the Message of the Day."""
    message: str = Field(
        ...,
        min_length=const.MOTD_MIN_LENGTH,
        max_length=const.MOTD_MAX_LENGTH,
        description="The message to display as the Message of the Day"
    )
