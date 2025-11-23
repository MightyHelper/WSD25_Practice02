"""Constants and configuration for the API."""
from typing import Final

# Rate limiting constants
RATE_LIMIT_WINDOW_SECONDS: Final[float] = 5.0
RATE_LIMIT_WINDOW_MAX_REQUESTS: Final[int] = 10  # Max requests before blacklisting
RATE_LIMIT_MIN_INTERVAL: Final[float] = 0.5  # 500ms between requests
BLACKLIST_DURATION: Final[float] = 10.0  # seconds
MAX_TIMESTAMPS_STORED: Final[int] = 1000  # Max timestamps to store per IP

# Error messages
ERROR_METHOD_NOT_ALLOWED: Final[str] = "Method Not Allowed"
ERROR_RATE_LIMIT_EXCEEDED: Final[str] = "Rate limit exceeded"
ERROR_BLACKLISTED_IP: Final[str] = "This IP is temporarily blacklisted"
ERROR_NUMBER_TOO_LARGE: Final[str] = "Number is too large for current payment plan. Do you think electricity is free?"
ERROR_VALIDATION: Final[str] = "Validation error"

# Default values
DEFAULT_MOTD: Final[str] = "Welcome to our API!"

# API Configuration
API_TITLE: Final[str] = "Practice 02 API"
API_DESCRIPTION: Final[str] = "API for Practice 02 - Web Services Development"
API_VERSION: Final[str] = "1.0.0"

# Prime number limits
PRIME_NUMBER_MAX: Final[int] = 1000

# MOTD constraints
MOTD_MIN_LENGTH: Final[int] = 1
MOTD_MAX_LENGTH: Final[int] = 100
