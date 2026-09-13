import json
import logging
import re
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
ACCESS_LOGGER = logging.getLogger("hackathon_manager.http")


class JsonFormatter(logging.Formatter):
    """Serialize application logs as one JSON object per line."""

    standard_attributes = frozenset(logging.makeLogRecord({}).__dict__) | {
        "asctime",
        "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in self.standard_attributes and _is_json_serializable(value)
            }
        )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _is_json_serializable(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


def get_request_id(scope: Scope) -> str:
    supplied_request_id = Headers(scope=scope).get(REQUEST_ID_HEADER, "").strip()
    if REQUEST_ID_PATTERN.fullmatch(supplied_request_id):
        return supplied_request_id
    return str(uuid.uuid4())


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = get_request_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id
        method = scope.get("method", "")
        path = scope.get("path", "")
        started_at = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            status_code = 500
            ACCESS_LOGGER.exception(
                "Unhandled request exception",
                extra={
                    "method": method,
                    "path": path,
                    "status": status_code,
                    "request_id": request_id,
                },
            )
            if response_started:
                raise
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
                headers={REQUEST_ID_HEADER: request_id},
            )
            await response(scope, receive, send)
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            ACCESS_LOGGER.info(
                "Request completed",
                extra={
                    "method": method,
                    "path": path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
            )
