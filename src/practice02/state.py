from typing import Optional

from . import constants as const


class State:
    # In-memory storage
    motd: Optional[str] = const.DEFAULT_MOTD
    special_numbers: set[int] = set()

    # Rate limiting storage
    request_timestamps: dict[str, list[float]] = {}
    blacklisted_ips: dict[str, float] = {}

    def __init__(self) -> None:
        raise NotImplementedError()
