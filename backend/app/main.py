from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Response, status
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cache
from app.db import get_session
from app.repositories.hackathon_repository import HackathonRepository
from app.schemas import HackathonCreate, HackathonResponse, HackathonUpdate
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


@app.get("/api/hackathons", response_model=list[HackathonResponse])
async def list_hackathons(
    service: HackathonService = Depends(get_hackathon_service),
) -> list[dict]:
    return await service.list_hackathons()


@app.post(
    "/api/hackathons",
    response_model=HackathonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hackathon(
    payload: HackathonCreate,
    service: HackathonService = Depends(get_hackathon_service),
) -> dict:
    return await service.create_hackathon(payload.name)


@app.patch("/api/hackathons/{hackathon_id}", response_model=HackathonResponse)
async def update_hackathon(
    hackathon_id: Annotated[int, Path(gt=0)],
    payload: HackathonUpdate,
    service: HackathonService = Depends(get_hackathon_service),
) -> dict:
    update_data = payload.model_dump(exclude_unset=True)
    hackathon = await service.update_hackathon(hackathon_id, update_data["name"])
    if hackathon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    return hackathon


@app.delete("/api/hackathons/{hackathon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hackathon(
    hackathon_id: Annotated[int, Path(gt=0)],
    service: HackathonService = Depends(get_hackathon_service),
) -> Response:
    deleted = await service.delete_hackathon(hackathon_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
