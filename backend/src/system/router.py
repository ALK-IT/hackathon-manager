import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache import get_cache
from src.database import get_session

router = APIRouter(tags=["system"])


@router.get("/health")
async def health(
    session: Annotated[AsyncSession, Depends(get_session)],
    cache: Annotated[Redis, Depends(get_cache)],
) -> JSONResponse:
    database_status, redis_status = await asyncio.gather(
        _check_database(session),
        _check_redis(cache),
    )
    components = {"database": database_status, "redis": redis_status}
    healthy = all(component == "ok" for component in components.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ok" if healthy else "unhealthy",
            "components": components,
        },
    )


async def _check_database(session: AsyncSession) -> str:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return "unavailable"
    return "ok"


async def _check_redis(cache: Redis) -> str:
    try:
        await cache.ping()
    except RedisError:
        return "unavailable"
    return "ok"


@router.get("/")
def root() -> dict[str, str]:
    return {"message": "hackathon-manager API"}
