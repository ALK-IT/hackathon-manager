from enum import StrEnum

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(StrEnum):
    BAD_REQUEST = "BAD_REQUEST"
    HACKATHON_ERROR = "HACKATHON_ERROR"
    ADMIN_REQUIRED = "ADMIN_REQUIRED"
    HACKATHON_NOT_FOUND = "HACKATHON_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    INVALID_TEAM_SIZE = "INVALID_TEAM_SIZE"
    INVALID_CONFIRM_NAME = "INVALID_CONFIRM_NAME"
    REGISTRATION_ALREADY_OPEN = "REGISTRATION_ALREADY_OPEN"
    REGISTRATION_ALREADY_CLOSED = "REGISTRATION_ALREADY_CLOSED"
    VALIDATION_ERROR = "VALIDATION_ERROR"


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

    def __init__(self, detail: str | None = None):
        self.detail = detail if detail is not None else type(self).detail
        super().__init__(self.detail)


async def handle_api_error(_request: Request, exc: APIError) -> JSONResponse:
    response = ErrorResponse(
        error_code=exc.error_code,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )


async def handle_request_validation_error(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    response = ValidationErrorResponse(
        error_code=ErrorCode.VALIDATION_ERROR,
        detail="Request validation failed.",
        errors=[
            ValidationErrorItem(
                location=list(error["loc"]),
                message=error["msg"],
                type=error["type"],
            )
            for error in exc.errors()
        ],
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response.model_dump(mode="json"),
    )
