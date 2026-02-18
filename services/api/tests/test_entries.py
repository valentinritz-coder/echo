from io import BytesIO

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient


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
    question = client.get("/questions/today")
    assert question.status_code == 200

    payload = {
        "user_id": user_id,
        "question_id": str(question.json()["id"]),
    }
    files = {"audio_file": ("voice.mp3", BytesIO(b"fake-audio"), "audio/mpeg")}

    created = client.post("/entries", data=payload, files=files)
    assert created.status_code == 200
    return created.json()


def test_create_list_delete_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    created_body = _create_entry(client)

    listed = client.get("/entries", params={"user_id": "alice"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    audio = client.get(f"/entries/{created_body['id']}/audio")
    assert audio.status_code == 200

    deleted = client.delete(f"/entries/{created_body['id']}")
    assert deleted.status_code == 200

    listed_again = client.get("/entries", params={"user_id": "alice"})
    assert listed_again.status_code == 200
    assert listed_again.json() == []


def test_404_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    response = client.get("/entries/not-found")
    assert response.status_code == 404


def test_mime_validation(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question = client.get("/questions/today")

    payload = {
        "user_id": "bob",
        "question_id": str(question.json()["id"]),
    }
    files = {"audio_file": ("voice.txt", BytesIO(b"not-audio"), "text/plain")}

    response = client.post("/entries", data=payload, files=files)
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "unsupported_mime",
            "message": "Unsupported audio MIME type",
        }
    }


def test_upload_accepts_audio_x_m4a(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question_id = client.get("/questions/today").json()["id"]

    response = client.post(
        "/entries",
        data={"user_id": "eve", "question_id": str(question_id)},
        files={"audio_file": ("voice.m4a", BytesIO(b"m4a"), "audio/x-m4a")},
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/x-m4a"


def test_upload_accepts_audio_webm(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question_id = client.get("/questions/today").json()["id"]

    response = client.post(
        "/entries",
        data={"user_id": "eve", "question_id": str(question_id)},
        files={"audio_file": ("voice.webm", BytesIO(b"webm"), "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/webm"


def test_upload_accepts_audio_3gpp(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    question_id = client.get("/questions/today").json()["id"]

    response = client.post(
        "/entries",
        data={"user_id": "eve", "question_id": str(question_id)},
        files={"audio_file": ("voice.3gp", BytesIO(b"3gpp"), "audio/3gpp")},
    )

    assert response.status_code == 200
    assert response.json()["audio_mime"] == "audio/3gpp"


def test_ai_process_creates_pending_run(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    entry = _create_entry(client, user_id="ai-user")

    response = client.post(f"/entries/{entry['id']}/ai/process", json={})
    assert response.status_code == 202
    body = response.json()
    assert body["entry_id"] == entry["id"]
    assert body["status"] == "pending"
    assert body["reused"] is False
    assert isinstance(body["run_id"], int)

    status = client.get(f"/entries/{entry['id']}/ai")
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["ai_status"] == "pending"
    assert status_body["ai_last_run_id"] == body["run_id"]
    assert status_body["last_run"]["status"] == "pending"
    assert status_body["last_run"]["tasks"] == ["transcribe", "summarize"]


def test_ai_process_reuses_done_run(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    entry = _create_entry(client, user_id="reuse-user")

    first = client.post(
        f"/entries/{entry['id']}/ai/process",
        json={"tasks": ["transcribe"], "pipeline_version": "v3.a"},
    )
    assert first.status_code == 202
    run_id = first.json()["run_id"]

    from app.db import SessionLocal
    from app.models import AiRun, Entry

    db = SessionLocal()
    run = db.get(AiRun, run_id)
    run.status = "done"
    run.summary_text = "done"
    entry_db = db.get(Entry, entry["id"])
    entry_db.ai_status = "done"
    entry_db.ai_last_run_id = run_id
    db.add(run)
    db.add(entry_db)
    db.commit()
    db.close()

    second = client.post(
        f"/entries/{entry['id']}/ai/process",
        json={"tasks": ["transcribe"], "pipeline_version": "v3.a", "force": False},
    )
    assert second.status_code == 200
    body = second.json()
    assert body == {
        "entry_id": entry["id"],
        "status": "done",
        "last_run_id": run_id,
        "reused": True,
    }


def test_get_ai_run_by_id(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    entry = _create_entry(client, user_id="run-user")
    created = client.post(f"/entries/{entry['id']}/ai/process", json={})
    run_id = created.json()["run_id"]

    response = client.get(f"/ai/runs/{run_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == run_id
    assert body["entry_id"] == entry["id"]
    assert body["status"] == "pending"
