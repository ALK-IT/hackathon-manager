import logging.config
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import src.all_models  # noqa: F401
from src.api import api_router
from src.auth.config import get_frontend_origins, validate_configuration
from src.common.observability import RequestLoggingMiddleware
from src.hackathons.exceptions import HackathonError
from src.registration.exceptions import RegistrationError
from src.resources.config import validate_resource_configuration
from src.resources.exceptions import ResourceError
from src.teams.exceptions import TeamError

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": "src.common.observability.JsonFormatter"},
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["stdout"],
            "level": os.environ.get("LOG_LEVEL", "INFO").upper(),
        },
        "loggers": {
            "uvicorn": {"handlers": ["stdout"], "propagate": False},
            "uvicorn.error": {"handlers": ["stdout"], "propagate": False},
            "uvicorn.access": {"handlers": ["stdout"], "propagate": False},
        },
    }
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_configuration()
    validate_resource_configuration()
    yield


app = FastAPI(title="hackathon-manager API", lifespan=lifespan)
app.include_router(api_router)


@app.exception_handler(HackathonError)
async def handle_hackathon_error(_request: Request, exc: HackathonError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )


@app.exception_handler(RegistrationError)
async def handle_registration_error(
    _request: Request,
    exc: RegistrationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )


@app.exception_handler(TeamError)
async def handle_team_error(_request: Request, exc: TeamError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )


@app.exception_handler(ResourceError)
async def handle_resource_error(_request: Request, exc: ResourceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "location": list(error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "detail": "Request validation failed.",
            "errors": errors,
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestLoggingMiddleware)
