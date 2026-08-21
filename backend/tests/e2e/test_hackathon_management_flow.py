from httpx import AsyncClient

from tests.e2e.helpers import E2EAccount, hackathon_payload


async def test_admin_completes_hackathon_management_flow(
    e2e_client: AsyncClient,
    admin_account: E2EAccount,
):
    create_response = await e2e_client.post(
        "/api/hackathons",
        headers=admin_account.headers,
        json=hackathon_payload(),
    )

    assert create_response.status_code == 201
    hackathon_id = create_response.json()["public_id"]
    assert create_response.json()["registration_open"] is False

    managed_response = await e2e_client.get(
        "/api/hackathons/managed",
        headers=admin_account.headers,
    )
    public_before_open_response = await e2e_client.get("/api/hackathons?open=true")

    assert managed_response.status_code == 200
    assert [item["public_id"] for item in managed_response.json()] == [hackathon_id]
    assert public_before_open_response.status_code == 200
    assert public_before_open_response.json() == []

    update_response = await e2e_client.patch(
        f"/api/hackathons/{hackathon_id}",
        headers=admin_account.headers,
        json={"description": "Updated through the E2E API flow"},
    )
    open_response = await e2e_client.post(
        f"/api/hackathons/{hackathon_id}/open-registration",
        headers=admin_account.headers,
    )
    public_after_open_response = await e2e_client.get("/api/hackathons?open=true")

    assert update_response.status_code == 200
    assert update_response.json()["description"] == "Updated through the E2E API flow"
    assert open_response.status_code == 200
    assert open_response.json()["registration_open"] is True
    assert [item["public_id"] for item in public_after_open_response.json()] == [hackathon_id]

    close_response = await e2e_client.post(
        f"/api/hackathons/{hackathon_id}/close-registration",
        headers=admin_account.headers,
    )
    public_after_close_response = await e2e_client.get("/api/hackathons?open=true")
    delete_response = await e2e_client.request(
        "DELETE",
        f"/api/hackathons/{hackathon_id}",
        headers=admin_account.headers,
        json={"confirm_name": "E2E Hackathon"},
    )
    deleted_response = await e2e_client.get(f"/api/hackathons/{hackathon_id}")

    assert close_response.status_code == 200
    assert close_response.json()["registration_open"] is False
    assert public_after_close_response.json() == []
    assert delete_response.status_code == 204
    assert deleted_response.status_code == 404
    assert deleted_response.json()["error_code"] == "HACKATHON_NOT_FOUND"
