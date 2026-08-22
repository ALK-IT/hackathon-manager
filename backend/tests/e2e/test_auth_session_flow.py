from httpx import AsyncClient


async def test_user_completes_auth_session_flow(e2e_client: AsyncClient, account_factory):
    account = await account_factory(
        name="E2E Participant",
        email="e2e-participant@example.com",
    )

    me_response = await e2e_client.get("/api/auth/me", headers=account.headers)

    assert me_response.status_code == 200
    assert me_response.json()["public_id"] == account.public_id
    assert me_response.json()["email"] == account.email

    refresh_response = await e2e_client.post("/api/auth/refresh")

    assert refresh_response.status_code == 200
    refreshed_access_token = refresh_response.json()["access_token"]
    assert refreshed_access_token != account.access_token

    logout_response = await e2e_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {refreshed_access_token}"},
    )
    revoked_me_response = await e2e_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {refreshed_access_token}"},
    )
    refresh_after_logout_response = await e2e_client.post("/api/auth/refresh")

    assert logout_response.status_code == 204
    assert revoked_me_response.status_code == 401
    assert refresh_after_logout_response.status_code == 401
