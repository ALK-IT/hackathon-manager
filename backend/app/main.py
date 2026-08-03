from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import api_router

app = FastAPI(title="hackathon-manager API")
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
