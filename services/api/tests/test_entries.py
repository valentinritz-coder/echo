from io import BytesIO

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient


API_PREFIX = "/api/v1"


def _build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

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

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{app.settings.settings.data_dir / 'echo.db'}")
    command.upgrade(alembic_cfg, "head")

    return TestClient(app.main.app)


def _create_entry(client: TestClient, user_id: str = "alice") -> dict:
    question = client.get(f"{API_PREFIX}/questions/today")
    assert question.status_code == 200

    payload = {
        "user_id": user_id,
        "question_id": str(question.json()["id"]),
    }
    files = {"audio_file": ("voice.mp3", BytesIO(b"fake-audio"), "audio/mpeg")}

    created = client.post(f"{API_PREFIX}/entries", data=payload, files=files)
    assert created.status_code == 200
    return created.json()


def test_create_list_delete_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    created_body = _create_entry(client)

    listed = client.get(f"{API_PREFIX}/entries", params={"user_id": "alice"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    audio = client.get(f"{API_PREFIX}/entries/{created_body['id']}/audio")
    assert audio.status_code == 200

    deleted = client.delete(f"{API_PREFIX}/entries/{created_body['id']}")
    assert deleted.status_code == 200

    listed_again = client.get(f"{API_PREFIX}/entries", params={"user_id": "alice"})
    assert listed_again.status_code == 200
    assert listed_again.json() == []


def test_404_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    response = client.get(f"{API_PREFIX}/entries/not-found")
    assert response.status_code == 404


def test_mime_validation(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question = client.get(f"{API_PREFIX}/questions/today")

    payload = {
        "user_id": "bob",
        "question_id": str(question.json()["id"]),
    }
    files = {"audio_file": ("voice.txt", BytesIO(b"not-audio"), "text/plain")}

    response = client.post(f"{API_PREFIX}/entries", data=payload, files=files)
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "unsupported_mime",
            "message": "Unsupported audio MIME type",
        }
    }


def test_upload_accepts_audio_x_m4a(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question_id = client.get(f"{API_PREFIX}/questions/today").json()["id"]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"user_id": "eve", "question_id": str(question_id)},
        files={"audio_file": ("voice.m4a", BytesIO(b"m4a"), "audio/x-m4a")},
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/x-m4a"


def test_upload_accepts_audio_webm(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question_id = client.get(f"{API_PREFIX}/questions/today").json()["id"]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"user_id": "eve", "question_id": str(question_id)},
        files={"audio_file": ("voice.webm", BytesIO(b"webm"), "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/webm"


def test_upload_accepts_audio_3gpp(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question_id = client.get(f"{API_PREFIX}/questions/today").json()["id"]

    response = client.post(
        f"{API_PREFIX}/entries",
        data={"user_id": "eve", "question_id": str(question_id)},
        files={"audio_file": ("voice.3gp", BytesIO(b"3gpp"), "audio/3gpp")},
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/3gpp"


def test_legacy_root_endpoints_removed(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    assert client.get("/health").status_code == 404
    assert client.get("/version").status_code == 404
    assert client.get("/questions/today").status_code == 404
    assert client.get("/entries", params={"user_id": "alice"}).status_code == 404
    assert client.get("/entries/not-found").status_code == 404
