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


def test_create_entry_with_text_content_and_readback(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    created = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id), "text_content": "hello"},
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )

    assert created.status_code == 200
    assert created.json()["text_content"] == "hello"

    entry_id = created.json()["id"]
    fetched = client.get(f"{API_PREFIX}/entries/{entry_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["text_content"] == "hello"


def test_create_entry_text_only_ok(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id), "text": "hello"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["text_content"] == "hello"
    assert response.json()["audio_mime"] is None
    assert response.json()["audio_size"] is None


def test_create_entry_audio_only_ok(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/mpeg"


def test_create_entry_text_and_audio_ok(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id), "text": "hello"},
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["text_content"] == "hello"
    assert response.json()["audio_mime"] == "audio/mpeg"
    assert response.json()["audio_size"] == len(VALID_MP3_BYTES)


def test_create_entry_rejects_empty(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "entry_empty",
            "message": "Either text or audio_file is required",
        }
    }


def test_create_entry_prefers_first_non_empty_text_field(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id), "text_content": "", "text": "hello"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["text_content"] == "hello"


def test_create_entry_does_not_store_empty_text(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id), "text": "   "},
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["text_content"] is None


def test_text_content_length_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("MAX_TEXT_CHARS", "5")
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id), "text_content": "bonjour"},
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "text_content_too_long",
            "message": "text_content length exceeds MAX_TEXT_CHARS (5)",
        }
    }


def test_get_entry_includes_assets(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    created_body, headers = _create_entry(client)

    from app import db as app_db
    from app.models import EntryAsset, User

    with app_db.SessionLocal() as session:
        user = session.query(User).filter(User.email == "admin@example.com").one()
        session.add(
            EntryAsset(
                entry_id=created_body["id"],
                user_id=user.id,
                asset_type="image",
                path="images/test.jpg",
                mime="image/jpeg",
                size=1234,
                sha256="a" * 64,
                width=320,
                height=240,
            )
        )
        session.commit()

    response = client.get(f"{API_PREFIX}/entries/{created_body['id']}", headers=headers)
    assert response.status_code == 200
    assets = response.json()["assets"]
    assert len(assets) == 1
    assert assets[0]["asset_type"] == "image"
    assert assets[0]["path"] == "images/test.jpg"
    assert assets[0]["mime"] == "image/jpeg"
    assert assets[0]["size"] == 1234
    assert assets[0]["sha256"] == "a" * 64
    assert assets[0]["width"] == 320
    assert assets[0]["height"] == 240

    listed = client.get(f"{API_PREFIX}/entries", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1
    listed_assets = listed.json()["items"][0]["assets"]
    assert len(listed_assets) == 1
    assert listed_assets[0]["path"] == "images/test.jpg"
