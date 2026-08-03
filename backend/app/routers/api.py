from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.hackathons import router as hackathons_router
from app.routers.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(auth_router)
api_router.include_router(hackathons_router)
