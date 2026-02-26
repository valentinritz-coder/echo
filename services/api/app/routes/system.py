from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.settings import settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(db: Session = Depends(get_db)) -> JSONResponse:
    checks: dict[str, dict[str, object]] = {}

    # DB check
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = {"ok": True}
    except Exception as e:  # noqa: BLE001
        checks["db"] = {"ok": False, "error": str(e)}

    # Audio dir check: exists, is dir, writable
    audio_dir = settings.audio_dir
    try:
        if audio_dir.exists() and not audio_dir.is_dir():
            raise RuntimeError(f"{audio_dir} exists but is not a directory")
        audio_dir.mkdir(parents=True, exist_ok=True)
        probe = audio_dir / f".readyz_{uuid.uuid4().hex}.tmp"
        probe.write_bytes(b"ok")
        probe.unlink(missing_ok=True)
        checks["audio_dir"] = {"ok": True, "path": str(audio_dir)}
    except Exception as e:  # noqa: BLE001
        checks["audio_dir"] = {"ok": False, "path": str(audio_dir), "error": str(e)}

    ok = all(v.get("ok") is True for v in checks.values())
    status = "ok" if ok else "fail"
    code = 200 if ok else 503
    return JSONResponse(status_code=code, content={"status": status, "checks": checks})
