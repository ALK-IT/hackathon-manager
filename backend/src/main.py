<<<<<<< HEAD
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
=======
from contextlib import asynccontextmanager

from fastapi import FastAPI
>>>>>>> 1d053c36603fd8af12b15712f512814a82231af1
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import api_router
<<<<<<< HEAD
from src.hackathons.exceptions import HackathonError
from src.registration.exceptions import RegistrationError
=======
from src.auth.config import validate_configuration
>>>>>>> 1d053c36603fd8af12b15712f512814a82231af1

app = FastAPI(title="hackathon-manager API")
app.include_router(api_router)


<<<<<<< HEAD
@app.exception_handler(HackathonError)
async def handle_hackathon_error(_request: Request, exc: HackathonError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )


@app.exception_handler(RegistrationError)
async def handle_registration_error(
    _request: Request,
    exc: RegistrationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "location": list(error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "detail": "Request validation failed.",
            "errors": errors,
        },
    )
=======
@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_configuration()
    yield
>>>>>>> 1d053c36603fd8af12b15712f512814a82231af1


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
