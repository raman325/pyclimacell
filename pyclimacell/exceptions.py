"""Exceptions for pyclimacell."""


class ClimaCellException(Exception):
    """Base Exception class for pyclimacell."""


class MalformedRequestException(ClimaCellException):
    """Raised when request was malformed."""


class InvalidAPIKeyException(ClimaCellException):
    """Raised when API key is invalid."""


class RateLimitedException(ClimaCellException):
    """Raised when API rate limit has been exceeded."""


class UnknownException(ClimaCellException):
    """Raised when unknown error occurs."""


class CantConnectException(ClimaCellException):
    """Raise when client can't connect to ClimaCell API."""
