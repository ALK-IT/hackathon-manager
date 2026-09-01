import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.common.errors import (
    APIError,
    ErrorCode,
    ErrorResponse,
    ValidationErrorItem,
    ValidationErrorResponse,
)

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: ErrorCode.BAD_REQUEST,
    status.HTTP_401_UNAUTHORIZED: ErrorCode.AUTHENTICATION_REQUIRED,
    status.HTTP_403_FORBIDDEN: ErrorCode.PERMISSION_DENIED,
    status.HTTP_404_NOT_FOUND: ErrorCode.NOT_FOUND,
    status.HTTP_405_METHOD_NOT_ALLOWED: ErrorCode.METHOD_NOT_ALLOWED,
}

HTTP_ERROR_DETAILS = {
    status.HTTP_401_UNAUTHORIZED: "Authentication is required.",
    status.HTTP_403_FORBIDDEN: "You do not have permission to perform this operation.",
    status.HTTP_404_NOT_FOUND: "The requested resource was not found.",
    status.HTTP_405_METHOD_NOT_ALLOWED: "The requested method is not allowed.",
}


def _error_response(
    status_code: int,
    error_code: ErrorCode,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response = ErrorResponse(error_code=error_code, detail=detail)
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
        headers=headers,
    )


async def handle_api_error(_request: Request, exc: APIError) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        detail=exc.detail,
        headers=exc.headers,
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


async def handle_http_exception(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    error_code = HTTP_ERROR_CODES.get(exc.status_code, ErrorCode.HTTP_ERROR)
    detail = HTTP_ERROR_DETAILS.get(exc.status_code)
    if detail is None:
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP request failed."
    return _error_response(
        status_code=exc.status_code,
        error_code=error_code,
        detail=detail,
        headers=exc.headers,
    )


async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled API exception",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCode.INTERNAL_ERROR,
        detail="An unexpected server error occurred.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(APIError, handle_api_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_error)
