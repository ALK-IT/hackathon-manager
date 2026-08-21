from httpx import AsyncClient

from tests.e2e.helpers import E2EAccount, hackathon_payload


async def test_users_complete_registration_and_team_flow(
    e2e_client: AsyncClient,
    admin_account: E2EAccount,
    account_factory,
):
    hackathon_response = await e2e_client.post(
        "/api/hackathons",
        headers=admin_account.headers,
        json=hackathon_payload(),
    )
    assert hackathon_response.status_code == 201
    hackathon_id = hackathon_response.json()["public_id"]

    questions_response = await e2e_client.post(
        f"/api/hackathons/{hackathon_id}/questions/bulk",
        headers=admin_account.headers,
        json={
            "questions": [
                {"content": "Why do you want to participate?", "is_required": True},
                {"content": "Anything else?", "is_required": False},
            ]
        },
    )
    assert questions_response.status_code == 201
    required_question_id = questions_response.json()[0]["public_id"]

    open_registration_response = await e2e_client.post(
        f"/api/hackathons/{hackathon_id}/open-registration",
        headers=admin_account.headers,
    )
    assert open_registration_response.status_code == 200

    first_participant = await account_factory(
        name="First Participant",
        email="first-participant@example.com",
    )
    second_participant = await account_factory(
        name="Second Participant",
        email="second-participant@example.com",
    )

    public_list_response = await e2e_client.get("/api/hackathons")
    participant_questions_response = await e2e_client.get(
        f"/api/hackathons/{hackathon_id}/questions",
        headers=first_participant.headers,
    )

    assert public_list_response.status_code == 200
    assert [item["public_id"] for item in public_list_response.json()] == [hackathon_id]
    assert participant_questions_response.status_code == 200
    assert len(participant_questions_response.json()) == 2

    first_registration_response = await e2e_client.post(
        f"/api/hackathons/{hackathon_id}/registrations",
        headers=first_participant.headers,
        json={
            "answers": [
                {
                    "question_public_id": required_question_id,
                    "content": "I want to build and learn.",
                }
            ],
            "team": {"action": "create", "name": "E2E Team"},
        },
    )
    assert first_registration_response.status_code == 201
    first_registration = first_registration_response.json()
    join_code = first_registration["team"]["join_code"]

    second_registration_response = await e2e_client.post(
        f"/api/hackathons/{hackathon_id}/registrations",
        headers=second_participant.headers,
        json={
            "answers": [
                {
                    "question_public_id": required_question_id,
                    "content": "I want to collaborate.",
                }
            ],
            "team": {"action": "join", "join_code": join_code},
        },
    )
    assert second_registration_response.status_code == 201
    second_registration = second_registration_response.json()
    assert second_registration["team"]["public_id"] == first_registration["team"]["public_id"]

    organizer_list_response = await e2e_client.get(
        f"/api/hackathons/{hackathon_id}/registrations",
        headers=admin_account.headers,
    )

    assert organizer_list_response.status_code == 200
    assert {item["user"]["email"] for item in organizer_list_response.json()} == {
        first_participant.email,
        second_participant.email,
    }

    accept_response = await e2e_client.patch(
        f"/api/registrations/{first_registration['public_id']}/status",
        headers=admin_account.headers,
        json={"status": "accepted"},
    )
    reject_response = await e2e_client.patch(
        f"/api/registrations/{second_registration['public_id']}/status",
        headers=admin_account.headers,
        json={"status": "rejected"},
    )

    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "accepted"
    assert accept_response.json()["status_changed_by"]["public_id"] == admin_account.public_id
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    first_own_response = await e2e_client.get(
        f"/api/hackathons/{hackathon_id}/registrations/me",
        headers=first_participant.headers,
    )
    second_own_response = await e2e_client.get(
        f"/api/hackathons/{hackathon_id}/registrations/me",
        headers=second_participant.headers,
    )

    assert first_own_response.status_code == 200
    assert first_own_response.json()["status"] == "accepted"
    assert first_own_response.json()["team"]["join_code"] == join_code
    assert second_own_response.status_code == 200
    assert second_own_response.json()["status"] == "rejected"
    assert second_own_response.json()["team"]["join_code"] == join_code
