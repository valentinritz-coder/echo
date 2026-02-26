import re

import httpx
import pytest

pytestmark = pytest.mark.e2e


def _assert_request_id(value: str) -> None:
    assert value
    assert re.fullmatch(r"[0-9a-f]{32}|[A-Za-z0-9._-]{8,128}", value)


def test_health_endpoint(e2e_base_url: str):
    r = httpx.get(f"{e2e_base_url}/api/v1/health", timeout=5.0)

    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    _assert_request_id(r.headers.get("X-Request-Id", ""))


def test_readyz_endpoint(e2e_base_url: str):
    r = httpx.get(f"{e2e_base_url}/api/v1/readyz", timeout=10.0)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["checks"]["db"]["ok"] is True
    assert body["checks"]["audio_dir"]["ok"] is True
    _assert_request_id(r.headers.get("X-Request-Id", ""))
