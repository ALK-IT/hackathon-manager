from fastapi import APIRouter

from src.attendance.router import router as attendance_router
from src.auth.router import router as auth_router
from src.hackathons.router import router as hackathons_router
from src.registration.router import router as registration_router
from src.resources.router import router as resources_router
from src.system.router import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(auth_router)
api_router.include_router(hackathons_router)
api_router.include_router(registration_router)
api_router.include_router(resources_router)
api_router.include_router(attendance_router)
