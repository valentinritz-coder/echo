import httpx


def _login(base_url: str, email: str, password: str) -> dict[str, str]:
    r = httpx.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=10.0,
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload_entry(base_url: str, headers: dict[str, str], question_id: int) -> dict:
    # Minimal MP3 signature accepted by backend (ID3...)
    mp3_bytes = b"ID3\x04\x00\x00\x00\x00\x00\x00payload"
    files = {"audio_file": ("voice.mp3", mp3_bytes, "audio/mpeg")}
    data = {"question_id": str(question_id)}
    r = httpx.post(
        f"{base_url}/api/v1/entries",
        headers=headers,
        data=data,
        files=files,
        timeout=20.0,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_e2e_full_flow(e2e_base_url: str):
    base = e2e_base_url

    # Health
    r = httpx.get(f"{base}/api/v1/health", timeout=5.0)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # Auth required
    assert httpx.get(f"{base}/api/v1/questions/today", timeout=5.0).status_code == 401
    assert httpx.get(f"{base}/api/v1/entries", timeout=5.0).status_code == 401

    # Login admin
    admin_headers = _login(base, "admin@example.com", "admin-password")

    # Get question
    q = httpx.get(f"{base}/api/v1/questions/today", headers=admin_headers, timeout=10.0)
    assert q.status_code == 200, q.text
    qid = int(q.json()["id"])

    # Create entry (upload)
    entry = _upload_entry(base, admin_headers, qid)
    entry_id = entry["id"]

    # Audio endpoint
    audio = httpx.get(
        f"{base}/api/v1/entries/{entry_id}/audio",
        headers=admin_headers,
        timeout=10.0,
    )
    assert audio.status_code == 200

    # Login user B (seeded by conftest)
    user_b_headers = _login(base, "user_b@example.com", "password-b")

    # ACL: user B cannot access admin entry (403)
    for path in [f"/api/v1/entries/{entry_id}", f"/api/v1/entries/{entry_id}/audio"]:
        rr = httpx.get(f"{base}{path}", headers=user_b_headers, timeout=10.0)
        assert rr.status_code == 403, rr.text

    rr = httpx.delete(
        f"{base}/api/v1/entries/{entry_id}", headers=user_b_headers, timeout=10.0
    )
    assert rr.status_code == 403, rr.text

    # Missing stays 404
    missing = "00000000-0000-0000-0000-000000000000"
    assert (
        httpx.get(
            f"{base}/api/v1/entries/{missing}", headers=user_b_headers, timeout=10.0
        ).status_code
        == 404
    )
    assert (
        httpx.get(
            f"{base}/api/v1/entries/{missing}/audio",
            headers=user_b_headers,
            timeout=10.0,
        ).status_code
        == 404
    )
    assert (
        httpx.delete(
            f"{base}/api/v1/entries/{missing}", headers=user_b_headers, timeout=10.0
        ).status_code
        == 404
    )

    # Listing wrapper + clamp basic
    lst = httpx.get(
        f"{base}/api/v1/entries", headers=admin_headers, timeout=10.0
    ).json()
    assert (
        "items" in lst and "limit" in lst and "offset" in lst and "next_offset" in lst
    )

    clamped = httpx.get(
        f"{base}/api/v1/entries?limit=999", headers=admin_headers, timeout=10.0
    ).json()
    assert clamped["limit"] == 200

    # Cleanup
    d = httpx.delete(
        f"{base}/api/v1/entries/{entry_id}", headers=admin_headers, timeout=10.0
    )
    assert d.status_code == 200, d.text

    lst2 = httpx.get(
        f"{base}/api/v1/entries", headers=admin_headers, timeout=10.0
    ).json()
    assert lst2["items"] == []
