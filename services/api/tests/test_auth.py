from pathlib import Path
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1"


def _build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-password")
    monkeypatch.setenv("APP_ENV", "development")

    import app.db
    import app.main
    import app.settings

    app.settings.settings = app.settings.Settings()
    app.db.settings = app.settings.settings
    app.main.settings = app.settings.settings

    app.db.engine.dispose()
    app.db.engine = app.db.create_engine(
        f"sqlite:///{app.settings.settings.data_dir / 'echo.db'}",
        connect_args={"check_same_thread": False},
    )
    app.db.SessionLocal.configure(bind=app.db.engine)
    app.main.engine = app.db.engine

    api_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(api_dir / "alembic.ini"))
    alembic_cfg.set_main_option(
        "sqlalchemy.url", f"sqlite:///{app.settings.settings.data_dir / 'echo.db'}"
    )
    command.upgrade(alembic_cfg, "head")

    from app.models import User
    from app.security import hash_password

    with app.db.SessionLocal() as db:
        if db.query(User).count() == 0:
            db.add(
                User(
                    email="admin@example.com",
                    password_hash=hash_password("admin-password"),
                    is_active=True,
                )
            )
            db.commit()

    return TestClient(app.main.app)


def test_login_returns_access_and_refresh_tokens(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "admin@example.com", "password": "admin-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_refresh_returns_new_access_token(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    login = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "admin@example.com", "password": "admin-password"},
    )

    refresh = client.post(
        f"{API_PREFIX}/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )

    assert refresh.status_code == 200
    assert refresh.json()["token_type"] == "bearer"
    assert refresh.json()["access_token"]


def test_login_fails_with_bad_password(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "admin@example.com", "password": "bad-password"},
    )

    assert response.status_code == 401


def test_refresh_fails_with_access_token(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    login = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "admin@example.com", "password": "admin-password"},
    )

    response = client.post(
        f"{API_PREFIX}/auth/refresh",
        json={"refresh_token": login.json()["access_token"]},
    )

    assert response.status_code == 401
