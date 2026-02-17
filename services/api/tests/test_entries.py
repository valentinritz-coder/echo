from io import BytesIO

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
    app.main.Base.metadata.drop_all(bind=app.db.engine)
    app.main.Base.metadata.create_all(bind=app.db.engine)

    return TestClient(app.main.app)


def test_create_list_delete_entry(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)

    question = client.get("/questions/today")
    assert question.status_code == 200

    payload = {
        "user_id": "alice",
        "question_id": str(question.json()["id"]),
    }
    files = {"audio_file": ("voice.mp3", BytesIO(b"fake-audio"), "audio/mpeg")}

    created = client.post("/entries", data=payload, files=files)
    assert created.status_code == 200
    created_body = created.json()

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
