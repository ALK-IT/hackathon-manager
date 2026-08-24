from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.all_models  # noqa: F401
from src.api import api_router
from src.auth.config import get_frontend_origins, validate_configuration
from src.common.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_configuration()
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
)
