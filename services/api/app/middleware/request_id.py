from __future__ import annotations

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Iterable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")

STANDARD_LOG_RECORD_ATTRS: set[str] = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}


def get_request_id() -> str | None:
    return _request_id_var.get()


def _normalize_request_id(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().replace("\r", "").replace("\n", "")
    if not v:
        return None
    if len(v) > 128:
        v = v[:128]
    if not _REQUEST_ID_RE.fullmatch(v):
        return None
    return v


class RequestIdLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }

        items: Iterable[tuple[str, Any]] = record.__dict__.items()
        extras = {
            k: v
            for k, v in items
            if k not in STANDARD_LOG_RECORD_ATTRS and not k.startswith("_")
        }
        payload.update(extras)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_json_logging(level: int = logging.INFO) -> None:
    base = logging.getLogger("app")
    base.setLevel(level)

    if base.handlers:
        return

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(RequestIdLogFilter())
    handler.setFormatter(JsonFormatter())

    base.addHandler(handler)
    base.propagate = False


class RequestIdMiddleware:
    header_name = "X-Request-Id"

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = logging.getLogger("app.http")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        incoming = headers.get(b"x-request-id", b"").decode("latin-1")
        rid = _normalize_request_id(incoming) or uuid.uuid4().hex

        token = _request_id_var.set(rid)
        start = time.perf_counter()
        status_code = 500

        raw_query = scope.get("query_string", b"").decode("latin-1")
        query_keys = sorted(
            {
                chunk.split("=", 1)[0]
                for chunk in raw_query.split("&")
                if chunk and chunk.split("=", 1)[0]
            }
        )

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                mutable_headers = MutableHeaders(scope=message)
                mutable_headers[self.header_name] = rid
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self.logger.info(
                "request",
                extra={
                    "method": scope.get("method", ""),
                    "path": scope.get("path", ""),
                    "query_keys": query_keys,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            _request_id_var.reset(token)
