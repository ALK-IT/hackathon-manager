from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello() -> None:
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert "message" in response.json()


def test_expected_routes_are_registered() -> None:
    paths = set(app.openapi()["paths"])

    assert {
        "/health",
        "/api/hello",
        "/api/hackathons",
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/auth/logout",
        "/api/auth/me",
    }.issubset(paths)
