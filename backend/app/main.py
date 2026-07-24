from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cache
from app.db import get_session
from app.repositories.hackathon_repository import HackathonRepository
from app.services.hackathon_service import HackathonService

app = FastAPI(title="hackathon-manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "hackathon-manager API"}


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello World z backendu hackathon-manager!"}


def get_hackathon_service(
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_cache),
) -> HackathonService:
    return HackathonService(HackathonRepository(session), cache)


@app.get("/api/hackathons")
async def list_hackathons(
    service: HackathonService = Depends(get_hackathon_service),
) -> list[dict]:
    return await service.list_hackathons()
