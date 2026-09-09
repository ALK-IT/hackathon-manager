from fastapi import status

from src.common.errors import APIError, ErrorCode


class InvalidAccessTokenError(Exception):
    pass


class EmailAlreadyRegisteredError(APIError):
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.EMAIL_ALREADY_REGISTERED
    detail = "An account with this email already exists."


class InvalidActionTokenError(Exception):
    pass


class RateLimitError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
