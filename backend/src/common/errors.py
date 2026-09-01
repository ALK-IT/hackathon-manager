from enum import StrEnum
from typing import ClassVar

from fastapi import status
from pydantic import BaseModel


class ErrorCode(StrEnum):
    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    HTTP_ERROR = "HTTP_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"

    HACKATHON_ERROR = "HACKATHON_ERROR"
    ADMIN_REQUIRED = "ADMIN_REQUIRED"
    HACKATHON_NOT_FOUND = "HACKATHON_NOT_FOUND"
    CO_ORGANIZER_USER_NOT_FOUND = "CO_ORGANIZER_USER_NOT_FOUND"
    CO_ORGANIZER_ALREADY_ASSIGNED = "CO_ORGANIZER_ALREADY_ASSIGNED"
    ORGANIZER_CANNOT_BE_CO_ORGANIZER = "ORGANIZER_CANNOT_BE_CO_ORGANIZER"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    INVALID_REGISTRATION_DEADLINE = "INVALID_REGISTRATION_DEADLINE"
    INVALID_REGISTRATION_WINDOW = "INVALID_REGISTRATION_WINDOW"
    INVALID_TEAM_SIZE = "INVALID_TEAM_SIZE"
    INVALID_CONFIRM_NAME = "INVALID_CONFIRM_NAME"
    REGISTRATION_ALREADY_OPEN = "REGISTRATION_ALREADY_OPEN"
    REGISTRATION_ALREADY_CLOSED = "REGISTRATION_ALREADY_CLOSED"
    REGISTRATION_DEADLINE_PASSED = "REGISTRATION_DEADLINE_PASSED"

    REGISTRATION_ERROR = "REGISTRATION_ERROR"
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"
    REGISTRATION_QUESTIONS_LOCKED = "REGISTRATION_QUESTIONS_LOCKED"
    INVALID_REGISTRATION_QUESTION = "INVALID_REGISTRATION_QUESTION"
    MISSING_REQUIRED_ANSWERS = "MISSING_REQUIRED_ANSWERS"
    ALREADY_REGISTERED = "ALREADY_REGISTERED"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    REGISTRATION_NOT_FOUND = "REGISTRATION_NOT_FOUND"

    TEAM_ERROR = "TEAM_ERROR"
    TEAM_NOT_FOUND = "TEAM_NOT_FOUND"
    TEAM_FULL = "TEAM_FULL"
    TEAMS_DISABLED = "TEAMS_DISABLED"
    TEAM_NAME_TAKEN = "TEAM_NAME_TAKEN"
    TEAM_JOIN_CODE_GENERATION_FAILED = "TEAM_JOIN_CODE_GENERATION_FAILED"

    CAPACITY_FULL = "CAPACITY_FULL"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    TEAM_CONFIRMATION_REQUIRED = "TEAM_CONFIRMATION_REQUIRED"
    NOT_TEAM_MEMBER = "NOT_TEAM_MEMBER"

    RESOURCE_ERROR = "RESOURCE_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ITEM_NOT_FOUND = "RESOURCE_ITEM_NOT_FOUND"
    RESOURCE_RECIPIENT_NOT_FOUND = "RESOURCE_RECIPIENT_NOT_FOUND"
    RESOURCE_ITEM_UNAVAILABLE = "RESOURCE_ITEM_UNAVAILABLE"
    RESOURCE_TARGET_MISMATCH = "RESOURCE_TARGET_MISMATCH"


class ErrorResponse(BaseModel):
    error_code: ErrorCode
    detail: str


class ValidationErrorItem(BaseModel):
    location: list[str | int]
    message: str
    type: str


class ValidationErrorResponse(ErrorResponse):
    errors: list[ValidationErrorItem]


class APIError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.BAD_REQUEST
    detail = "API operation failed."
    headers: dict[str, str] | None = None

    def __init__(
        self,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.detail = detail if detail is not None else type(self).detail
        self.headers = headers if headers is not None else type(self).headers
        super().__init__(self.detail)


class DomainError(APIError):
    def __init__(
        self,
        error_code: ErrorCode,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(detail=detail, headers=headers)


class AuthenticationRequiredError(APIError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.AUTHENTICATION_REQUIRED
    detail = "Invalid email, password, or access token."
    headers: ClassVar[dict[str, str]] = {"WWW-Authenticate": "Bearer"}
