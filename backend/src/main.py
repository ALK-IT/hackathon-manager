from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.errors import APIError, handle_api_error, handle_request_validation_error

app = FastAPI(title="hackathon-manager API")
app.include_router(api_router)
app.add_exception_handler(APIError, handle_api_error)
app.add_exception_handler(RequestValidationError, handle_request_validation_error)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
