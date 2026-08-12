import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from src.auth.models import User, UserRole
from src.hackathons.exceptions import (
    HackathonNotFoundError,
    InvalidConfirmNameError,
    RegistrationAlreadyOpenError,
    RegistrationDeadlinePassedError,
)
from src.hackathons.service import HackathonService
from tests.hackathons.factories import HackathonFactory, UserFactory


def create_payload() -> dict:
    return {
        "name": "Hackathon AI",
        "description": "Build something useful",
        "start_date": "2026-09-02T10:00:00Z",
        "end_date": "2026-09-03T10:00:00Z",
        "registration_opens_at": "2026-08-01T10:00:00Z",
        "capacity": 100,
        "max_team_size": 4,
    }


async def test_create_endpoint_returns_hackathon_without_internal_ids(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    mock_hackathon_service.create_hackathon.return_value = hackathon
    requested_deadline = "2026-09-01T10:00:00Z"

    response = await hackathon_client.post(
        "/api/hackathons",
        json=create_payload() | {"registration_deadline": requested_deadline},
    )

    assert response.status_code == 201
    assert response.json()["public_id"] == str(hackathon.public_id)
    assert response.json()["access_level"] == "owner"
    assert datetime.fromisoformat(response.json()["registration_opens_at"]) == (
        hackathon.registration_opens_at
    )
    assert datetime.fromisoformat(response.json()["registration_deadline"]) == (
        hackathon.registration_deadline
    )
    assert response.json()["organizer"] == {
        "public_id": str(admin_user.public_id),
        "name": admin_user.name,
    }
    assert "id" not in response.json()
    assert "organizer_id" not in response.json()
    created_data, created_by = mock_hackathon_service.create_hackathon.await_args.args
    assert created_data.name == "Hackathon AI"
    assert created_data.registration_deadline == datetime.fromisoformat(requested_deadline)
    assert created_by is admin_user


async def test_regular_user_cannot_create_hackathon(
    hackathon_client: AsyncClient,
    force_authenticate,
    regular_user: User,
    mock_hackathon_service: HackathonService,
):
    force_authenticate(regular_user)

    response = await hackathon_client.post("/api/hackathons", json=create_payload())

    assert response.status_code == 403
    assert response.json() == {
        "error_code": "ADMIN_REQUIRED",
        "detail": "Only an administrator can create a hackathon.",
    }
    mock_hackathon_service.create_hackathon.assert_not_awaited()


async def test_list_endpoint_returns_all_access_levels(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    owner = user_factory(user_id=2, role=UserRole.ADMIN)
    other_owner = user_factory(user_id=3, role=UserRole.ADMIN)
    owned_hackathon = hackathon_factory(organizer=admin_user)
    co_organized_hackathon = hackathon_factory(
        organizer=owner,
        co_organizers=[admin_user],
    )
    co_organized_hackathon.id = 2
    viewed_hackathon = hackathon_factory(organizer=other_owner)
    viewed_hackathon.id = 3
    mock_hackathon_service.list_hackathons.return_value = [
        owned_hackathon,
        co_organized_hackathon,
        viewed_hackathon,
    ]

    response = await hackathon_client.get("/api/hackathons")

    assert response.status_code == 200
    assert [item["access_level"] for item in response.json()] == [
        "owner",
        "co_organizer",
        "viewer",
    ]
    mock_hackathon_service.list_hackathons.assert_awaited_once_with()


async def test_list_endpoint_is_public(
    hackathon_client: AsyncClient,
    force_authenticate,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(
        organizer=admin_user,
        registration_opens_at=datetime.now(UTC) - timedelta(hours=1),
    )
    mock_hackathon_service.list_hackathons.return_value = [hackathon]
    force_authenticate(None)

    response = await hackathon_client.get("/api/hackathons")

    assert response.status_code == 200
    assert response.json()[0]["public_id"] == str(hackathon.public_id)
    assert response.json()[0]["access_level"] == "viewer"
    mock_hackathon_service.list_hackathons.assert_awaited_once_with()


async def test_list_endpoint_reports_registration_closed_after_deadline(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(
        organizer=admin_user,
        registration_open=True,
        registration_deadline=datetime.now(UTC) - timedelta(seconds=1),
    )
    mock_hackathon_service.list_hackathons.return_value = [hackathon]

    response = await hackathon_client.get("/api/hackathons")

    assert response.status_code == 200
    assert response.json()[0]["registration_open"] is False


async def test_managed_endpoint_returns_only_owned_and_co_organized_hackathons(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    other_owner = user_factory(user_id=2, role=UserRole.ADMIN)
    owned_hackathon = hackathon_factory(organizer=admin_user)
    co_organized_hackathon = hackathon_factory(
        organizer=other_owner,
        co_organizers=[admin_user],
    )
    mock_hackathon_service.list_managed_hackathons.return_value = [
        owned_hackathon,
        co_organized_hackathon,
    ]

    response = await hackathon_client.get("/api/hackathons/managed")

    assert response.status_code == 200
    assert [item["access_level"] for item in response.json()] == [
        "owner",
        "co_organizer",
    ]
    mock_hackathon_service.list_managed_hackathons.assert_awaited_once_with(admin_user)


async def test_get_endpoint_returns_details_to_regular_viewer(
    hackathon_client: AsyncClient,
    force_authenticate,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    co_organizer = user_factory(user_id=2)
    viewer = user_factory(user_id=3)
    hackathon = hackathon_factory(
        organizer=admin_user,
        co_organizers=[co_organizer],
    )
    mock_hackathon_service.get_hackathon.return_value = hackathon
    force_authenticate(viewer)

    response = await hackathon_client.get(f"/api/hackathons/{hackathon.public_id}")

    assert response.status_code == 200
    assert response.json()["access_level"] == "viewer"
    assert response.json()["description"] == hackathon.description
    assert response.json()["co_organizers"] == [
        {
            "public_id": str(co_organizer.public_id),
            "name": co_organizer.name,
        }
    ]
    mock_hackathon_service.get_hackathon.assert_awaited_once_with(hackathon.public_id)


async def test_get_endpoint_is_public(
    hackathon_client: AsyncClient,
    force_authenticate,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    mock_hackathon_service.get_hackathon.return_value = hackathon
    force_authenticate(None)

    response = await hackathon_client.get(f"/api/hackathons/{hackathon.public_id}")

    assert response.status_code == 200
    assert response.json()["public_id"] == str(hackathon.public_id)
    assert response.json()["description"] == hackathon.description
    assert response.json()["access_level"] == "viewer"
    mock_hackathon_service.get_hackathon.assert_awaited_once_with(hackathon.public_id)


async def test_patch_endpoint_updates_only_sent_fields(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    hackathon.name = "Updated Hackathon"
    mock_hackathon_service.update_hackathon.return_value = hackathon

    response = await hackathon_client.patch(
        f"/api/hackathons/{hackathon.public_id}",
        json={"name": "  Updated Hackathon  "},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Hackathon"
    public_id, update, current_user = mock_hackathon_service.update_hackathon.await_args.args
    assert public_id == hackathon.public_id
    assert update.model_dump(exclude_unset=True) == {"name": "Updated Hackathon"}
    assert current_user is admin_user


async def test_delete_endpoint_passes_confirmed_name_and_returns_no_content(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
    admin_user: User,
):
    public_id = uuid.uuid4()

    response = await hackathon_client.request(
        "DELETE",
        f"/api/hackathons/{public_id}",
        json={"confirm_name": "  Hackathon AI  "},
    )

    assert response.status_code == 204
    assert response.content == b""
    mock_hackathon_service.delete_hackathon.assert_awaited_once_with(
        public_id,
        "Hackathon AI",
        admin_user,
    )


async def test_registration_endpoints_return_current_state(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(
        organizer=admin_user,
        registration_opens_at=datetime.now(UTC) - timedelta(hours=1),
    )
    hackathon.registration_open = True
    mock_hackathon_service.open_registration.return_value = hackathon

    open_response = await hackathon_client.post(
        f"/api/hackathons/{hackathon.public_id}/open-registration"
    )

    hackathon.registration_open = False
    mock_hackathon_service.close_registration.return_value = hackathon
    close_response = await hackathon_client.post(
        f"/api/hackathons/{hackathon.public_id}/close-registration"
    )

    assert open_response.status_code == 200
    assert open_response.json() == {
        "public_id": str(hackathon.public_id),
        "registration_opens_at": hackathon.registration_opens_at.isoformat().replace("+00:00", "Z"),
        "registration_deadline": hackathon.registration_deadline.isoformat().replace("+00:00", "Z"),
        "registration_open": True,
    }
    assert close_response.status_code == 200
    assert close_response.json() == {
        "public_id": str(hackathon.public_id),
        "registration_opens_at": hackathon.registration_opens_at.isoformat().replace("+00:00", "Z"),
        "registration_deadline": hackathon.registration_deadline.isoformat().replace("+00:00", "Z"),
        "registration_open": False,
    }


async def test_management_endpoints_require_access_token(
    hackathon_client: AsyncClient,
    force_authenticate,
    mock_hackathon_service: HackathonService,
):
    public_id = uuid.uuid4()
    force_authenticate(None)

    responses = [
        await hackathon_client.get("/api/hackathons/managed"),
        await hackathon_client.post("/api/hackathons", json=create_payload()),
        await hackathon_client.patch(
            f"/api/hackathons/{public_id}",
            json={"name": "Updated"},
        ),
        await hackathon_client.request(
            "DELETE",
            f"/api/hackathons/{public_id}",
            json={"confirm_name": "Hackathon AI"},
        ),
        await hackathon_client.post(f"/api/hackathons/{public_id}/open-registration"),
        await hackathon_client.post(f"/api/hackathons/{public_id}/close-registration"),
    ]

    assert [response.status_code for response in responses] == [401] * len(responses)
    mock_hackathon_service.list_managed_hackathons.assert_not_awaited()
    mock_hackathon_service.create_hackathon.assert_not_awaited()
    mock_hackathon_service.update_hackathon.assert_not_awaited()
    mock_hackathon_service.delete_hackathon.assert_not_awaited()
    mock_hackathon_service.open_registration.assert_not_awaited()
    mock_hackathon_service.close_registration.assert_not_awaited()


async def test_request_rejects_fields_managed_by_backend(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
):
    payload = create_payload() | {"organizer_id": 123}

    response = await hackathon_client.post("/api/hackathons", json=payload)

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    assert response.json()["errors"][0]["location"] == ["body", "organizer_id"]
    mock_hackathon_service.create_hackathon.assert_not_awaited()


async def test_domain_errors_have_stable_http_contract(
    hackathon_client: AsyncClient,
    mock_hackathon_service: HackathonService,
):
    public_id = uuid.uuid4()
    cases = [
        (
            mock_hackathon_service.get_hackathon,
            HackathonNotFoundError,
            "GET",
            f"/api/hackathons/{public_id}",
            None,
            404,
            "HACKATHON_NOT_FOUND",
        ),
        (
            mock_hackathon_service.update_hackathon,
            HackathonNotFoundError,
            "PATCH",
            f"/api/hackathons/{public_id}",
            {"name": "Updated"},
            404,
            "HACKATHON_NOT_FOUND",
        ),
        (
            mock_hackathon_service.delete_hackathon,
            InvalidConfirmNameError,
            "DELETE",
            f"/api/hackathons/{public_id}",
            {"confirm_name": "Wrong name"},
            400,
            "INVALID_CONFIRM_NAME",
        ),
        (
            mock_hackathon_service.open_registration,
            RegistrationAlreadyOpenError,
            "POST",
            f"/api/hackathons/{public_id}/open-registration",
            None,
            409,
            "REGISTRATION_ALREADY_OPEN",
        ),
        (
            mock_hackathon_service.open_registration,
            RegistrationDeadlinePassedError,
            "POST",
            f"/api/hackathons/{public_id}/open-registration",
            None,
            409,
            "REGISTRATION_DEADLINE_PASSED",
        ),
    ]

    for service_method, error, method, path, body, status_code, error_code in cases:
        service_method.side_effect = error
        response = await hackathon_client.request(method, path, json=body)

        assert response.status_code == status_code
        assert response.json()["error_code"] == error_code
        service_method.side_effect = None
