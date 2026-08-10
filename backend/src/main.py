from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.auth.config import get_frontend_origins, validate_configuration


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_configuration()
    yield


app = FastAPI(title="hackathon-manager API", lifespan=lifespan)
app.include_router(api_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
