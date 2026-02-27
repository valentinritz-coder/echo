from io import BytesIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1"
VALID_MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x00payload"


def _build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
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
    alembic_cfg.set_main_option("script_location", str(api_dir / "alembic"))
    alembic_cfg.set_main_option(
        "sqlalchemy.url", f"sqlite:///{app.settings.settings.data_dir / 'echo.db'}"
    )
    command.upgrade(alembic_cfg, "head")

    from app.models import User
    from app.security import hash_password

    with app.db.SessionLocal() as db:
        db.add(
            User(
                email="user_a@example.com",
                password_hash=hash_password("password-a"),
                is_active=True,
            )
        )
        db.add(
            User(
                email="user_b@example.com",
                password_hash=hash_password("password-b"),
                is_active=True,
            )
        )
        db.commit()

    return TestClient(app.main.app)


def _auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_entry(client: TestClient, headers: dict[str, str]) -> str:
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]
    create = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )
    assert create.status_code == 200
    return str(create.json()["id"])


def test_freeze_then_delete_conflict(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")
    entry_id = _create_entry(client, headers)

    freeze = client.post(f"{API_PREFIX}/entries/{entry_id}/freeze", headers=headers)
    assert freeze.status_code == 200
    assert freeze.json() == {"status": "frozen", "id": entry_id, "is_frozen": True}

    delete = client.delete(f"{API_PREFIX}/entries/{entry_id}", headers=headers)
    assert delete.status_code == 409
    assert delete.json() == {
        "error_code": "ENTRY_FROZEN_IMMUTABLE",
        "detail": "Entry is frozen and cannot be modified",
    }


def test_freeze_idempotent_and_forbidden_for_non_owner(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers_a = _auth_headers(client, "user_a@example.com", "password-a")
    headers_b = _auth_headers(client, "user_b@example.com", "password-b")
    entry_id = _create_entry(client, headers_a)

    freeze_once = client.post(
        f"{API_PREFIX}/entries/{entry_id}/freeze", headers=headers_a
    )
    assert freeze_once.status_code == 200
    assert freeze_once.json()["is_frozen"] is True

    freeze_twice = client.post(
        f"{API_PREFIX}/entries/{entry_id}/freeze", headers=headers_a
    )
    assert freeze_twice.status_code == 200
    assert freeze_twice.json()["is_frozen"] is True

    freeze_other_user = client.post(
        f"{API_PREFIX}/entries/{entry_id}/freeze", headers=headers_b
    )
    assert freeze_other_user.status_code == 403
    assert freeze_other_user.json() == {
        "error": {"code": "forbidden", "message": "Not allowed"}
    }


def test_mutations_blocked_when_frozen(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")
    entry_id = _create_entry(client, headers)

    freeze = client.post(f"{API_PREFIX}/entries/{entry_id}/freeze", headers=headers)
    assert freeze.status_code == 200

    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()["id"]

    update = client.patch(
        f"{API_PREFIX}/entries/{entry_id}",
        json={"question_id": question_id},
        headers=headers,
    )
    assert update.status_code == 409
    assert update.json()["error_code"] == "ENTRY_FROZEN_IMMUTABLE"

    upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/audio",
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )
    assert upload.status_code == 409
    assert upload.json()["error_code"] == "ENTRY_FROZEN_IMMUTABLE"

    delete_audio = client.delete(f"{API_PREFIX}/entries/{entry_id}/audio", headers=headers)
    assert delete_audio.status_code == 409
    assert delete_audio.json()["error_code"] == "ENTRY_FROZEN_IMMUTABLE"


def test_mutation_404_has_priority_over_frozen(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")

    update = client.patch(
        f"{API_PREFIX}/entries/not-found",
        json={"question_id": 1},
        headers=headers,
    )
    assert update.status_code == 404

    upload = client.post(
        f"{API_PREFIX}/entries/not-found/audio",
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )
    assert upload.status_code == 404

    delete_audio = client.delete(f"{API_PREFIX}/entries/not-found/audio", headers=headers)
    assert delete_audio.status_code == 404


def test_mutation_403_remains_acl_for_non_owner_non_frozen(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers_a = _auth_headers(client, "user_a@example.com", "password-a")
    headers_b = _auth_headers(client, "user_b@example.com", "password-b")
    entry_id = _create_entry(client, headers_a)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers_b).json()["id"]

    update = client.patch(
        f"{API_PREFIX}/entries/{entry_id}",
        json={"question_id": question_id},
        headers=headers_b,
    )
    assert update.status_code == 403

    upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/audio",
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers_b,
    )
    assert upload.status_code == 403

    delete_audio = client.delete(f"{API_PREFIX}/entries/{entry_id}/audio", headers=headers_b)
    assert delete_audio.status_code == 403


def test_mutation_non_owner_frozen_returns_403(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers_a = _auth_headers(client, "user_a@example.com", "password-a")
    headers_b = _auth_headers(client, "user_b@example.com", "password-b")
    entry_id = _create_entry(client, headers_a)

    freeze = client.post(f"{API_PREFIX}/entries/{entry_id}/freeze", headers=headers_a)
    assert freeze.status_code == 200

    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers_b).json()["id"]

    update = client.patch(
        f"{API_PREFIX}/entries/{entry_id}",
        json={"question_id": question_id},
        headers=headers_b,
    )
    assert update.status_code == 403

    upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/audio",
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers_b,
    )
    assert upload.status_code == 403

    delete_audio = client.delete(f"{API_PREFIX}/entries/{entry_id}/audio", headers=headers_b)
    assert delete_audio.status_code == 403

    delete_entry = client.delete(f"{API_PREFIX}/entries/{entry_id}", headers=headers_b)
    assert delete_entry.status_code == 403
