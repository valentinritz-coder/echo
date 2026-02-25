from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from sqlalchemy import update

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1"


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
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{app.settings.settings.data_dir / 'echo.db'}")
    command.upgrade(alembic_cfg, "head")

    from app.models import User
    from app.security import hash_password

    with app.db.SessionLocal() as db:
        db.add(User(email="user_a@example.com", password_hash=hash_password("password-a"), is_active=True))
        db.add(User(email="user_b@example.com", password_hash=hash_password("password-b"), is_active=True))
        db.commit()

    return TestClient(app.main.app)


def _auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(f"{API_PREFIX}/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_entry(client: TestClient, headers: dict[str, str]) -> dict:
    question_id = client.get(f"{API_PREFIX}/questions/today", headers=headers).json()["id"]
    response = client.post(
        f"{API_PREFIX}/entries",
        data={"question_id": str(question_id)},
        files={"audio_file": ("voice.mp3", BytesIO(b"audio"), "audio/mpeg")},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_default_pagination_wrapper(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")

    _create_entry(client, headers)

    response = client.get(f"{API_PREFIX}/entries", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert isinstance(body["items"], list)
    assert body["next_offset"] is None


def test_limit_clamped_to_200(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")

    response = client.get(f"{API_PREFIX}/entries?limit=999", headers=headers)
    assert response.status_code == 200
    assert response.json()["limit"] == 200


def test_limit_and_offset_validation(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")

    bad_offset = client.get(f"{API_PREFIX}/entries?offset=-1", headers=headers)
    assert bad_offset.status_code == 422

    bad_limit = client.get(f"{API_PREFIX}/entries?limit=0", headers=headers)
    assert bad_limit.status_code == 422


def test_sort_created_at_asc_desc(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")

    first = _create_entry(client, headers)
    second = _create_entry(client, headers)

    import app.db
    from app.models import Entry

    with app.db.SessionLocal() as db:
        db.execute(
            update(Entry).where(Entry.id == first["id"]).values(created_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
        )
        db.execute(
            update(Entry).where(Entry.id == second["id"]).values(created_at=datetime(2024, 1, 2, tzinfo=timezone.utc))
        )
        db.commit()

    desc = client.get(f"{API_PREFIX}/entries?sort=created_at_desc", headers=headers)
    asc = client.get(f"{API_PREFIX}/entries?sort=created_at_asc", headers=headers)

    assert desc.status_code == 200
    assert asc.status_code == 200
    assert desc.json()["items"][0]["id"] == second["id"]
    assert asc.json()["items"][0]["id"] == first["id"]


def test_stable_pagination_with_tiebreaker(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers = _auth_headers(client, "user_a@example.com", "password-a")

    created_ids = [_create_entry(client, headers)["id"] for _ in range(5)]

    import app.db
    from app.models import Entry

    with app.db.SessionLocal() as db:
        db.execute(
            update(Entry)
            .where(Entry.id.in_(created_ids))
            .values(created_at=datetime(2024, 2, 1, tzinfo=timezone.utc))
        )
        db.commit()

    page_1 = client.get(f"{API_PREFIX}/entries?sort=created_at_desc&limit=2&offset=0", headers=headers).json()
    page_2 = client.get(f"{API_PREFIX}/entries?sort=created_at_desc&limit=2&offset=2", headers=headers).json()
    page_3 = client.get(f"{API_PREFIX}/entries?sort=created_at_desc&limit=2&offset=4", headers=headers).json()

    seen_ids = [item["id"] for item in page_1["items"] + page_2["items"] + page_3["items"]]
    assert seen_ids == sorted(created_ids, reverse=True)
    assert len(seen_ids) == len(set(seen_ids))
    assert page_1["next_offset"] == 2
    assert page_2["next_offset"] == 4
    assert page_3["next_offset"] is None


def test_entries_list_acl_isolated_by_user(tmp_path, monkeypatch):
    client = _build_client(tmp_path, monkeypatch)
    headers_a = _auth_headers(client, "user_a@example.com", "password-a")
    headers_b = _auth_headers(client, "user_b@example.com", "password-b")

    entry_a1 = _create_entry(client, headers_a)["id"]
    entry_a2 = _create_entry(client, headers_a)["id"]
    entry_b1 = _create_entry(client, headers_b)["id"]

    list_a = client.get(f"{API_PREFIX}/entries?limit=10&offset=0", headers=headers_a)
    list_b = client.get(f"{API_PREFIX}/entries?limit=10&offset=0", headers=headers_b)

    assert list_a.status_code == 200
    assert list_b.status_code == 200
    ids_a = {item["id"] for item in list_a.json()["items"]}
    ids_b = {item["id"] for item in list_b.json()["items"]}
    assert ids_a == {entry_a1, entry_a2}
    assert ids_b == {entry_b1}
