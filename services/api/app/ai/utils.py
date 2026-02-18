import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def compute_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads_json(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)
