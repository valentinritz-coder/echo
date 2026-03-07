import importlib
import re
import shutil
from pathlib import Path

from fastapi.testclient import TestClient


API_PREFIX = "/api/v1"


def _build_client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8501")
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

    import app.db
    import app.main
    import app.routes.system
    import app.settings

    importlib.reload(app.settings)
    importlib.reload(app.routes.system)

    if hasattr(app.db, "create_engine"):
        app.db.settings = app.settings.settings
        app.db.engine.dispose()
        app.db.engine = app.db.create_engine(
            f"sqlite:///{app.settings.settings.data_dir / 'echo.db'}",
            connect_args={"check_same_thread": False},
        )
        app.db.SessionLocal.configure(bind=app.db.engine)

    importlib.reload(app.main)
    app.main.settings = app.settings.settings
    if hasattr(app.db, "engine"):
        app.main.engine = app.db.engine

    return TestClient(app.main.app)


def test_version_returns_name_and_version(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    r = client.get(f"{API_PREFIX}/version")
    assert r.status_code == 200
    body = r.json()
    assert "name" in body
    assert "version" in body
    assert body["name"] == "echo-mvp"
    assert isinstance(body["version"], str)
    assert len(body["version"]) >= 1


def test_health_has_request_id_header(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    r = client.get(f"{API_PREFIX}/health")
    assert r.status_code == 200
    rid = r.headers.get("X-Request-Id")
    assert rid is not None
    assert len(rid) >= 8


def test_health_ignores_invalid_request_id_header(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    r = client.get(f"{API_PREFIX}/health", headers={"X-Request-Id": "bad value!"})
    assert r.status_code == 200
    rid = r.headers.get("X-Request-Id")
    assert rid is not None
    assert re.fullmatch(r"[0-9a-f]{32}", rid)


def test_readyz_ok(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    r = client.get(f"{API_PREFIX}/readyz")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"


def test_readyz_fails_if_audio_dir_becomes_file(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    import app.routes.system

    audio_path = app.routes.system.settings.audio_dir
    if audio_path.exists() and audio_path.is_dir():
        shutil.rmtree(audio_path)
    audio_path.write_text("not a dir", encoding="utf-8")

    r = client.get(f"{API_PREFIX}/readyz")
    assert r.status_code == 503, r.text
    body = r.json()
    assert body["status"] == "fail"
    assert body["checks"]["audio_dir"]["ok"] is False
