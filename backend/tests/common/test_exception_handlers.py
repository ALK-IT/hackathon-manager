import json

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from src.auth.exceptions import EmailAlreadyRegisteredError
from src.common.errors import (
    APIError,
    AuthenticationRequiredError,
    DomainError,
    ErrorCode,
)
from src.common.exception_handlers import handle_api_error, register_exception_handlers
from src.hackathons.exceptions import (
    AdminRequiredError,
    CoOrganizerAlreadyAssignedError,
    CoOrganizerUserNotFoundError,
    HackathonNotFoundError,
    InvalidConfirmNameError,
    InvalidDateRangeError,
    InvalidRegistrationDeadlineError,
    InvalidRegistrationWindowError,
    InvalidTeamSizeError,
    OrganizerCannotBeCoOrganizerError,
    RegistrationAlreadyClosedError,
    RegistrationAlreadyOpenError,
    RegistrationDeadlinePassedError,
)
from src.registration.exceptions import (
    InvalidPermission,
    InvalidRegistrationQuestionError,
    MissingRequiredAnswersError,
    QuestionNotFoundError,
    RegistrationAlreadyExistsError,
    RegistrationClosedError,
    RegistrationNotFoundError,
    RegistrationQuestionsLockedError,
)
from src.teams.exceptions import (
    TeamFullError,
    TeamJoinCodeGenerationError,
    TeamNameAlreadyExistsError,
    TeamNotFoundError,
    TeamsDisabledError,
)

DOMAIN_ERROR_CASES = [
    (AuthenticationRequiredError, 401, ErrorCode.AUTHENTICATION_REQUIRED),
    (EmailAlreadyRegisteredError, 409, ErrorCode.EMAIL_ALREADY_REGISTERED),
    (AdminRequiredError, 403, ErrorCode.ADMIN_REQUIRED),
    (HackathonNotFoundError, 404, ErrorCode.HACKATHON_NOT_FOUND),
    (CoOrganizerUserNotFoundError, 404, ErrorCode.CO_ORGANIZER_USER_NOT_FOUND),
    (CoOrganizerAlreadyAssignedError, 409, ErrorCode.CO_ORGANIZER_ALREADY_ASSIGNED),
    (OrganizerCannotBeCoOrganizerError, 409, ErrorCode.ORGANIZER_CANNOT_BE_CO_ORGANIZER),
    (InvalidDateRangeError, 422, ErrorCode.INVALID_DATE_RANGE),
    (InvalidRegistrationDeadlineError, 422, ErrorCode.INVALID_REGISTRATION_DEADLINE),
    (InvalidRegistrationWindowError, 422, ErrorCode.INVALID_REGISTRATION_WINDOW),
    (InvalidTeamSizeError, 422, ErrorCode.INVALID_TEAM_SIZE),
    (InvalidConfirmNameError, 400, ErrorCode.INVALID_CONFIRM_NAME),
    (RegistrationAlreadyOpenError, 409, ErrorCode.REGISTRATION_ALREADY_OPEN),
    (RegistrationAlreadyClosedError, 409, ErrorCode.REGISTRATION_ALREADY_CLOSED),
    (RegistrationDeadlinePassedError, 409, ErrorCode.REGISTRATION_DEADLINE_PASSED),
    (QuestionNotFoundError, 404, ErrorCode.QUESTION_NOT_FOUND),
    (RegistrationQuestionsLockedError, 409, ErrorCode.REGISTRATION_QUESTIONS_LOCKED),
    (InvalidPermission, 403, ErrorCode.PERMISSION_DENIED),
    (InvalidRegistrationQuestionError, 422, ErrorCode.INVALID_REGISTRATION_QUESTION),
    (MissingRequiredAnswersError, 422, ErrorCode.MISSING_REQUIRED_ANSWERS),
    (RegistrationAlreadyExistsError, 409, ErrorCode.ALREADY_REGISTERED),
    (RegistrationClosedError, 409, ErrorCode.REGISTRATION_CLOSED),
    (RegistrationNotFoundError, 404, ErrorCode.REGISTRATION_NOT_FOUND),
    (TeamNotFoundError, 404, ErrorCode.TEAM_NOT_FOUND),
    (TeamFullError, 409, ErrorCode.TEAM_FULL),
    (TeamsDisabledError, 409, ErrorCode.TEAMS_DISABLED),
    (TeamNameAlreadyExistsError, 409, ErrorCode.TEAM_NAME_TAKEN),
    (TeamJoinCodeGenerationError, 503, ErrorCode.TEAM_JOIN_CODE_GENERATION_FAILED),
]


@pytest.mark.parametrize(("error_type", "status_code", "error_code"), DOMAIN_ERROR_CASES)
async def test_domain_error_handler_returns_stable_contract(
    error_type: type[APIError],
    status_code: int,
    error_code: ErrorCode,
):
    error = error_type()

    response = await handle_api_error(None, error)  # type: ignore[arg-type]

    assert response.status_code == status_code
    assert json.loads(response.body) == {
        "error_code": error_code.value,
        "detail": error.detail,
    }


@pytest.mark.parametrize(
    ("error_code", "status_code"),
    [
        (ErrorCode.CAPACITY_FULL, 409),
        (ErrorCode.CONSENT_REQUIRED, 422),
        (ErrorCode.TEAM_CONFIRMATION_REQUIRED, 409),
        (ErrorCode.NOT_TEAM_MEMBER, 403),
        (ErrorCode.RESOURCE_ALREADY_ASSIGNED, 409),
        (ErrorCode.RESOURCE_REVOKED, 409),
        (ErrorCode.RESOURCE_NOT_ASSIGNED_TO_USER, 404),
        (ErrorCode.INVALID_QR_TOKEN, 422),
    ],
)
async def test_reserved_domain_codes_can_use_generic_domain_error(
    error_code: ErrorCode,
    status_code: int,
):
    error = DomainError(error_code, "Domain operation failed.", status_code)

    response = await handle_api_error(None, error)  # type: ignore[arg-type]

    assert response.status_code == status_code
    assert json.loads(response.body)["error_code"] == error_code.value


class ExamplePayload(BaseModel):
    name: str = Field(min_length=3)


@pytest.fixture
def error_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/payload")
    async def payload(_data: ExamplePayload) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/forbidden")
    async def forbidden() -> None:
        raise HTTPException(status_code=403, detail="Internal permission detail")

    @app.get("/unauthorized")
    async def unauthorized() -> None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.get("/failure")
    async def failure() -> None:
        raise RuntimeError("database password must never reach the response")

    return app


@pytest.fixture
async def error_client(error_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=error_app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client


async def test_validation_error_uses_common_contract(error_client: AsyncClient):
    response = await error_client.post("/payload", json={"name": "x"})

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["detail"] == "Request validation failed."
    assert body["errors"][0]["location"] == ["body", "name"]
    assert set(body["errors"][0]) == {"location", "message", "type"}


async def test_http_authentication_error_preserves_authenticate_header(
    error_client: AsyncClient,
):
    response = await error_client.get("/unauthorized")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error_code": "AUTHENTICATION_REQUIRED",
        "detail": "Authentication is required.",
    }


async def test_http_permission_error_uses_common_contract(error_client: AsyncClient):
    response = await error_client.get("/forbidden")

    assert response.status_code == 403
    assert response.json() == {
        "error_code": "PERMISSION_DENIED",
        "detail": "You do not have permission to perform this operation.",
    }


async def test_framework_404_and_405_use_common_contract(error_client: AsyncClient):
    not_found = await error_client.get("/missing")
    method_not_allowed = await error_client.get("/payload")

    assert not_found.status_code == 404
    assert not_found.json()["error_code"] == "NOT_FOUND"
    assert method_not_allowed.status_code == 405
    assert method_not_allowed.json()["error_code"] == "METHOD_NOT_ALLOWED"


async def test_unexpected_error_is_logged_without_leaking_detail(
    error_client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    response = await error_client.get("/failure")

    assert response.status_code == 500
    assert response.json() == {
        "error_code": "INTERNAL_ERROR",
        "detail": "An unexpected server error occurred.",
    }
    assert "database password" not in response.text
    assert "Unhandled API exception" in caplog.text
