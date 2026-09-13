import logging.config
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.all_models  # noqa: F401
from src.api import api_router
from src.auth.config import get_frontend_origins, validate_configuration
from src.common.exception_handlers import register_exception_handlers
from src.common.observability import RequestLoggingMiddleware
from src.resources.config import validate_resource_configuration

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
register_exception_handlers(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestLoggingMiddleware)
