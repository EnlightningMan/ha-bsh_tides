class BshApiError(Exception):
    """Base exception for all BSH-related errors."""

class BshCannotConnect(BshApiError):
    """Raised when the API is unreachable."""
    code = "cannot_connect"

class BshInvalidStation(BshApiError):
    """Raised when station response is invalid."""
    code = "invalid_station"