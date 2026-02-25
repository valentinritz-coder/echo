import hashlib
from io import BytesIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1"

VALID_MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x00streamed-audio"


class GeneratedMP3Stream:
    def __init__(self, total_size: int) -> None:
        self._header = b"ID3\x04\x00\x00\x00\x00\x00\x00"
        self._total_size = total_size
        self._sent = 0

    def read(self, size: int = -1) -> bytes:
        if self._sent >= self._total_size:
            return b""
        if size is None or size < 0:
            size = 64 * 1024
        end = min(self._total_size, self._sent + size)
        start = self._sent
        self._sent = end

        chunk_size = end - start
        chunk = bytearray(b"A" * chunk_size)
        header_start = max(start, 0)
        header_end = min(end, len(self._header))
        if header_end > header_start:
            for pos in range(header_start, header_end):
                chunk[pos - start] = self._header[pos]
        return bytes(chunk)


def _build_client(tmp_path, monkeypatch, *, max_upload_size_mb: int = 25):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-password")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", str(max_upload_size_mb))

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


def _question_id(client: TestClient, headers: dict[str, str]) -> int:
    question = client.get(f"{API_PREFIX}/questions/today", headers=headers)
    assert question.status_code == 200
    return int(question.json()["id"])


def test_upload_rejects_payload_too_large_without_creating_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch, max_upload_size_mb=1)
    headers = _auth_headers(client)

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(_question_id(client, headers))},
        files={
            "audio_file": (
                "voice.mp3",
                GeneratedMP3Stream(total_size=1024 * 1024 + 1),
                "audio/mpeg",
            )
        },
        headers=headers,
    )

    assert response.status_code == 413
    assert response.json() == {
        "error": {
            "code": "payload_too_large",
            "message": "Audio file exceeds upload size limit",
        }
    }

    listed = client.get(f"{API_PREFIX}/entries", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["items"] == []


def test_upload_persists_stream_sha256(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(_question_id(client, headers))},
        files={"audio_file": ("voice.mp3", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )
    assert response.status_code == 200
    entry_id = response.json()["id"]

    import app.db
    from app.models import Entry

    with app.db.SessionLocal() as db:
        stored = db.get(Entry, entry_id)
        assert stored is not None
        assert stored.audio_sha256 == hashlib.sha256(VALID_MP3_BYTES).hexdigest()
        assert stored.audio_size == len(VALID_MP3_BYTES)
        assert stored.audio_duration_ms is None


def test_upload_rejects_invalid_extension_and_signature(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)
    question_id = _question_id(client, headers)

    bad_extension = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.wav", BytesIO(VALID_MP3_BYTES), "audio/mpeg")},
        headers=headers,
    )
    assert bad_extension.status_code == 422
    assert bad_extension.json() == {
        "error": {
            "code": "invalid_extension",
            "message": "Filename extension does not match MIME type",
        }
    }

    bad_signature = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.mp3", BytesIO(b"NOT-MP3"), "audio/mpeg")},
        headers=headers,
    )
    assert bad_signature.status_code == 422
    assert bad_signature.json() == {
        "error": {
            "code": "invalid_signature",
            "message": "Audio signature does not match MIME type",
        }
    }


def test_upload_accepts_audio_mp4_extension(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client)

    mp4_bytes = b"\x00\x00\x00\x18ftypM4A \x00\x00\x00\x00"
    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(_question_id(client, headers))},
        files={"audio_file": ("voice.mp4", BytesIO(mp4_bytes), "audio/mp4")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/mp4"
