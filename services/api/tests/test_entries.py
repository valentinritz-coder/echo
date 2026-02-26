from io import BytesIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1"


VALID_MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x00payload"
VALID_M4A_BYTES = b"\x00\x00\x00\x18ftypM4A \x00\x00\x00\x00"
VALID_WEBM_BYTES = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01"
VALID_3GPP_BYTES = b"\x00\x00\x00\x14ftyp3gp5\x00\x00\x00\x00"


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


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "admin@example.com", "password": "admin-password"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_entry(client: TestClient) -> tuple[dict, dict[str, str]]:
    headers = _auth_headers(client)
    question = client.get(f"{API_PREFIX}/questions/today", headers=headers)
    assert question.status_code == 200

    payload = {"question_id": str(question.json()["id"])}
    files = {"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")}

    created = client.post(
        f"{API_PREFIX}/entries", data=payload, files=files, headers=headers
    )
    assert created.status_code == 200
    return created.json(), headers


def test_create_list_delete_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    created_body, headers = _create_entry(client)

    listed = client.get(f"{API_PREFIX}/entries", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    audio = client.get(
        f"{API_PREFIX}/entries/{created_body['id']}/audio", headers=headers
    )
    assert audio.status_code == 200

    deleted = client.delete(
        f"{API_PREFIX}/entries/{created_body['id']}", headers=headers
    )
    assert deleted.status_code == 200

    listed_again = client.get(f"{API_PREFIX}/entries", headers=headers)
    assert listed_again.status_code == 200
    assert listed_again.json()["items"] == []


def test_404_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    response = client.get(f"{API_PREFIX}/entries/not-found", headers=headers)
    assert response.status_code == 404


def test_mime_validation(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question = client.get(f"{API_PREFIX}/questions/today", headers=headers)

    payload = {"question_id": str(question.json()["id"])}
    files = {"audio_file": ("voice.txt", BytesIO(b"not-audio"), "text/plain")}

    response = client.post(
        f"{API_PREFIX}/entries", data=payload, files=files, headers=headers
    )
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "unsupported_mime",
            "message": "Unsupported audio MIME type",
        }
    }


def test_upload_accepts_audio_x_m4a(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.m4a", BytesIO(VALID_M4A_BYTES), "audio/x-m4a")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/x-m4a"


def test_upload_accepts_audio_webm(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.webm", BytesIO(VALID_WEBM_BYTES), "audio/webm")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/webm"


def test_upload_accepts_audio_3gpp(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.3gp", BytesIO(VALID_3GPP_BYTES), "audio/3gpp")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/3gpp"


def test_entries_require_auth(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    assert client.get(f"{API_PREFIX}/questions/today").status_code == 401
    assert client.get(f"{API_PREFIX}/entries").status_code == 401


def test_legacy_root_endpoints_removed(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    assert client.get("/health").status_code == 404
    assert client.get("/version").status_code == 404
    assert client.get("/questions/today").status_code == 404
    assert client.get("/entries").status_code == 404
    assert client.get("/entries/not-found").status_code == 404
