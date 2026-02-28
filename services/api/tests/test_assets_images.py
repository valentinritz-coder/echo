from io import BytesIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1"
PNG_1X1_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
    b"\xf6\x178U"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _build_client(tmp_path, monkeypatch, *, max_images_per_entry: int = 8):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("MAX_IMAGES_PER_ENTRY", str(max_images_per_entry))

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


def _create_text_entry(client: TestClient, headers: dict[str, str]) -> str:
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()[
        "id"
    ]
    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id), "text_content": "hello"},
        headers=headers,
    )
    assert response.status_code == 200
    return str(response.json()["id"])


def test_image_asset_upload_list_and_download(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")
    entry_id = _create_text_entry(client, headers)

    upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(PNG_1X1_BYTES), "image/png")},
        headers=headers,
    )
    assert upload.status_code == 200
    uploaded = upload.json()
    assert uploaded["asset_type"] == "image"
    assert uploaded["mime"] == "image/png"
    assert uploaded["size"] == len(PNG_1X1_BYTES)
    assert uploaded["sha256"]
    assert uploaded["width"] == 1
    assert uploaded["height"] == 1

    disk_path = tmp_path / uploaded["path"]
    assert disk_path.exists()

    listed = client.get(f"{API_PREFIX}/entries/{entry_id}/assets", headers=headers)
    assert listed.status_code == 200
    assets = listed.json()
    assert len(assets) == 1
    assert assets[0]["id"] == uploaded["id"]

    downloaded = client.get(f"{API_PREFIX}/assets/{uploaded['id']}", headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "image/png"
    assert downloaded.content == PNG_1X1_BYTES


def test_image_asset_validation_rejects_bad_mime_and_signature(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")
    entry_id = _create_text_entry(client, headers)

    bad_mime = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.txt", BytesIO(PNG_1X1_BYTES), "text/plain")},
        headers=headers,
    )
    assert bad_mime.status_code == 422
    assert bad_mime.json() == {
        "error": {
            "code": "unsupported_image_mime",
            "message": "Unsupported image MIME type",
        }
    }

    bad_signature = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(b"not-a-png"), "image/png")},
        headers=headers,
    )
    assert bad_signature.status_code == 422
    assert bad_signature.json() == {
        "error": {
            "code": "invalid_image_signature",
            "message": "Image signature does not match MIME type",
        }
    }


def test_image_asset_acl_and_freeze(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers_a = _auth_headers(client, "user_a@example.com", "password-a")
    headers_b = _auth_headers(client, "user_b@example.com", "password-b")
    entry_id = _create_text_entry(client, headers_a)

    upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(PNG_1X1_BYTES), "image/png")},
        headers=headers_a,
    )
    assert upload.status_code == 200
    asset_id = upload.json()["id"]

    forbidden_upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(PNG_1X1_BYTES), "image/png")},
        headers=headers_b,
    )
    assert forbidden_upload.status_code == 403

    forbidden_list = client.get(
        f"{API_PREFIX}/entries/{entry_id}/assets", headers=headers_b
    )
    assert forbidden_list.status_code == 403

    forbidden_download = client.get(
        f"{API_PREFIX}/assets/{asset_id}", headers=headers_b
    )
    assert forbidden_download.status_code == 403

    freeze = client.post(f"{API_PREFIX}/entries/{entry_id}/freeze", headers=headers_a)
    assert freeze.status_code == 200

    frozen_upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(PNG_1X1_BYTES), "image/png")},
        headers=headers_a,
    )
    assert frozen_upload.status_code == 409
    assert frozen_upload.json() == {
        "error_code": "ENTRY_FROZEN_IMMUTABLE",
        "detail": "Entry is frozen and cannot be modified",
    }


def test_image_asset_max_per_entry_limit(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch, max_images_per_entry=1)
    headers = _auth_headers(client, "user_a@example.com", "password-a")
    entry_id = _create_text_entry(client, headers)

    first = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(PNG_1X1_BYTES), "image/png")},
        headers=headers,
    )
    assert first.status_code == 200

    second = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(PNG_1X1_BYTES), "image/png")},
        headers=headers,
    )
    assert second.status_code == 422
    assert second.json() == {
        "error": {
            "code": "too_many_assets",
            "message": "Entry reached MAX_IMAGES_PER_ENTRY (1)",
        }
    }


def test_get_entry_audio_returns_no_audio_for_text_only_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")
    entry_id = _create_text_entry(client, headers)

    response = client.get(f"{API_PREFIX}/entries/{entry_id}/audio", headers=headers)
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "no_audio",
            "message": "Entry has no audio",
        }
    }


def test_download_asset_rejects_non_image_asset_type(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")
    entry_id = _create_text_entry(client, headers)

    upload = client.post(
        f"{API_PREFIX}/entries/{entry_id}/assets",
        files={"file": ("pixel.png", BytesIO(PNG_1X1_BYTES), "image/png")},
        headers=headers,
    )
    assert upload.status_code == 200
    asset_id = upload.json()["id"]

    import app.db
    from app.models import EntryAsset

    with app.db.SessionLocal() as db:
        asset = db.get(EntryAsset, asset_id)
        assert asset is not None
        asset.asset_type = "document"
        db.commit()

    response = client.get(f"{API_PREFIX}/assets/{asset_id}", headers=headers)
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "asset_not_image",
            "message": "Asset is not an image",
        }
    }
