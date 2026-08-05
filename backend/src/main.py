from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.auth.config import validate_configuration

app = FastAPI(title="hackathon-manager API")
app.include_router(api_router)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_configuration()
    yield


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
