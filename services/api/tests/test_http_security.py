import importlib

from fastapi.testclient import TestClient

API_PREFIX = "/api/v1"


def _build_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8501")
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

    import app.db
    import app.main
    import app.settings

    importlib.reload(app.settings)

    app.db.settings = app.settings.settings
    app.db.engine.dispose()
    app.db.engine = app.db.create_engine(
        f"sqlite:///{app.settings.settings.data_dir / 'echo.db'}",
        connect_args={"check_same_thread": False},
    )
    app.db.SessionLocal.configure(bind=app.db.engine)

    importlib.reload(app.main)
    app.main.settings = app.settings.settings
    app.main.engine = app.db.engine

    return TestClient(app.main.app)


def test_security_headers_present_on_health(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    response = client.get(f"{API_PREFIX}/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert (
        response.headers["Permissions-Policy"]
        == "geolocation=(), microphone=(), camera=()"
    )
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-site"


def test_version_has_cache_control_no_store(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    response = client.get(f"{API_PREFIX}/version")

    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store"


def test_trusted_host_rejects_unknown_host(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    response = client.get(f"{API_PREFIX}/health", headers={"Host": "evil.com"})

    assert response.status_code == 400


def test_cors_allows_configured_origin(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    response = client.options(
        f"{API_PREFIX}/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in {200, 204}
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


def test_cors_rejects_unconfigured_origin(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    response = client.options(
        f"{API_PREFIX}/health",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers.get("Access-Control-Allow-Origin") != "http://evil.com"
