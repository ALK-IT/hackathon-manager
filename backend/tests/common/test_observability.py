import json
import logging
import sys
import uuid

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.common.observability import JsonFormatter, RequestLoggingMiddleware


def test_json_formatter_includes_structured_fields_and_traceback():
    formatter = JsonFormatter()
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = logging.getLogger("test").makeRecord(
            "test",
            logging.ERROR,
            __file__,
            1,
            "Request failed",
            (),
            exc_info=sys.exc_info(),
            extra={"request_id": "request-123", "status": 500},
        )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "ERROR"
    assert payload["message"] == "Request failed"
    assert payload["request_id"] == "request-123"
    assert payload["status"] == 500
    assert "RuntimeError: boom" in payload["exception"]


def make_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/ok")
    async def ok() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/failure")
    async def failure() -> None:
        raise RuntimeError("secret failure detail")

    app.add_middleware(RequestLoggingMiddleware)
    return app


async def test_middleware_reuses_request_id_and_logs_request(mocker):
    logger = mocker.patch("src.common.observability.ACCESS_LOGGER")
    async with AsyncClient(
        transport=ASGITransport(app=make_test_app()),
        base_url="http://test",
    ) as client:
        response = await client.get("/ok", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"
    log_fields = logger.info.call_args.kwargs["extra"]
    assert log_fields["method"] == "GET"
    assert log_fields["path"] == "/ok"
    assert log_fields["status"] == 200
    assert log_fields["duration_ms"] >= 0
    assert log_fields["request_id"] == "request-123"


async def test_middleware_generates_request_id():
    async with AsyncClient(
        transport=ASGITransport(app=make_test_app()),
        base_url="http://test",
    ) as client:
        response = await client.get("/ok")

    uuid.UUID(response.headers["X-Request-ID"])


async def test_middleware_logs_unhandled_exception_with_traceback(mocker):
    logger = mocker.patch("src.common.observability.ACCESS_LOGGER")
    async with AsyncClient(
        transport=ASGITransport(app=make_test_app()),
        base_url="http://test",
    ) as client:
        response = await client.get("/failure", headers={"X-Request-ID": "failure-123"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers["X-Request-ID"] == "failure-123"
    logger.exception.assert_called_once()
    assert logger.exception.call_args.kwargs["extra"] == {
        "method": "GET",
        "path": "/failure",
        "status": 500,
        "request_id": "failure-123",
    }
