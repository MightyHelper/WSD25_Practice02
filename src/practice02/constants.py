"""Constants and configuration for the API."""
from typing import Final

# Rate limiting constants
RATE_LIMIT_REQUESTS_PER_SECOND: Final[int] = 1
RATE_LIMIT_WINDOW_SECONDS: Final[float] = 1.0
RATE_LIMIT_MIN_INTERVAL: Final[float] = 0.1  # 100ms between requests
RATE_LIMIT_MAX_REQUESTS: Final[int] = 100  # Max requests before blacklisting
BLACKLIST_DURATION: Final[float] = 10.0  # seconds
MAX_TIMESTAMPS_STORED: Final[int] = 1000  # Max timestamps to store per IP

# HTTP status codes
HTTP_200_OK: Final[int] = 200
HTTP_201_CREATED: Final[int] = 201
HTTP_400_BAD_REQUEST: Final[int] = 400
HTTP_401_UNAUTHORIZED: Final[int] = 401
HTTP_402_PAYMENT_REQUIRED: Final[int] = 402
HTTP_403_FORBIDDEN: Final[int] = 403
HTTP_404_NOT_FOUND: Final[int] = 404
HTTP_405_METHOD_NOT_ALLOWED: Final[int] = 405
HTTP_409_CONFLICT: Final[int] = 409
HTTP_418_IM_A_TEAPOT: Final[int] = 418
HTTP_420_ENHANCE_YOUR_CALM: Final[int] = 420
HTTP_422_UNPROCESSABLE_CONTENT: Final[int] = 422
HTTP_429_TOO_MANY_REQUESTS: Final[int] = 429
HTTP_500_INTERNAL_SERVER_ERROR: Final[int] = 500
HTTP_501_NOT_IMPLEMENTED: Final[int] = 501

# Error messages
ERROR_METHOD_NOT_ALLOWED: Final[str] = "Method Not Allowed"
ERROR_RATE_LIMIT_EXCEEDED: Final[str] = "Rate limit exceeded"
ERROR_BLACKLISTED_IP: Final[str] = "This IP is temporarily blacklisted"
ERROR_NUMBER_TOO_LARGE: Final[str] = "Number is too large for current payment plan. Do you think electricity is free?"
ERROR_NUMBER_NOT_FOUND: Final[str] = "Number not found"
ERROR_NUMBER_EXISTS: Final[str] = "Number already exists"
ERROR_MOTD_NOT_FOUND: Final[str] = "MOTD not found"
ERROR_INTERNAL_SERVER: Final[str] = "Internal server error"
ERROR_VALIDATION: Final[str] = "Validation error"

# Default values
DEFAULT_MOTD: Final[str] = "Welcome to our API!"
DEFAULT_HOST: Final[str] = "0.0.0.0"
DEFAULT_PORT: Final[int] = 3500

# API Configuration
API_TITLE: Final[str] = "Practice 02 API"
API_DESCRIPTION: Final[str] = "API for Practice 02 - Web Services Development"
API_VERSION: Final[str] = "1.0.0"

# Headers
HEADER_RETRY_AFTER: Final[str] = "Retry-After"
HEADER_X_CONTENT_TYPE_OPTIONS: Final[str] = "X-Content-Type-Options"
HEADER_X_FRAME_OPTIONS: Final[str] = "X-Frame-Options"
HEADER_X_XSS_PROTECTION: Final[str] = "X-XSS-Protection"

# Security
CONTENT_SECURITY_POLICY: Final[str] = "default-src 'self'"
X_CONTENT_TYPE_OPTIONS: Final[str] = "nosniff"
X_FRAME_OPTIONS: Final[str] = "DENY"
X_XSS_PROTECTION: Final[str] = "1; mode=block"

# Prime number limits
PRIME_NUMBER_MAX: Final[int] = 1000

# MOTD constraints
MOTD_MIN_LENGTH: Final[int] = 1
MOTD_MAX_LENGTH: Final[int] = 100
