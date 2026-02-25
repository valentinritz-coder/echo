import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import httpx
import pytest


def _repo_root() -> Path:
    # .../repo/services/api/tests_e2e/conftest.py -> parents[3] == repo
    return Path(__file__).resolve().parents[3]


def _upsert_env_var(env_path: Path, key: str, value: str) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    found = False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)

    if not found:
        out.append(f"{key}={value}")

    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _compose_cmd(repo: Path) -> list[str]:
    # Use same compose files as the sandbox PowerShell workflow
    return [
        "docker",
        "compose",
        "-f",
        str(repo / "docker-compose.yml"),
        "-f",
        str(repo / "docker-compose.sandbox.yml"),
    ]


def _run(repo: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    cp = subprocess.run(
        args,
        cwd=str(repo),
        text=True,
        capture_output=True,
    )
    if check and cp.returncode != 0:
        raise RuntimeError(
            f"Command failed ({cp.returncode}): {' '.join(args)}\n"
            f"--- stdout ---\n{cp.stdout}\n"
            f"--- stderr ---\n{cp.stderr}\n"
        )
    return cp


def _wait_health(base_url: str, timeout_s: int = 60) -> None:
    deadline = time.time() + timeout_s
    last_err: object | None = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/api/v1/health", timeout=5.0)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(2)
    raise RuntimeError(f"API never became healthy. Last error: {last_err!r}")


def _seed_user_b(repo: Path, email: str, password: str) -> None:
    # Run python inside api container to create/activate user_b
    py = f"""
from app.db import SessionLocal
from app.models import User
from app.security import hash_password

email = {email!r}.lower()
pwd = {password!r}

db = SessionLocal()
try:
    u = db.query(User).filter(User.email == email).first()
    hashed = hash_password(pwd)
    if u:
        u.is_active = True
        u.password_hash = hashed
        db.commit()
        print("user_b updated")
    else:
        db.add(User(email=email, is_active=True, password_hash=hashed))
        db.commit()
        print("user_b created")
finally:
    db.close()
"""
    cmd = _compose_cmd(repo) + ["exec", "-T", "api", "python", "-c", py]
    _run(repo, cmd, check=True)


@pytest.fixture(scope="session")
def e2e_base_url() -> str:
    # Allow override for non-default ports
    return os.environ.get("E2E_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session", autouse=True)
def e2e_stack(e2e_base_url: str):
    """
    Session-scoped: bring stack up once for all E2E tests, tear down at end.
    """
    repo = _repo_root()

    # Ensure .env has required runtime config
    env_path = repo / ".env"
    _upsert_env_var(env_path, "APP_ENV", "development")
    _upsert_env_var(env_path, "JWT_SECRET_KEY", uuid.uuid4().hex)
    _upsert_env_var(env_path, "JWT_REFRESH_SECRET_KEY", uuid.uuid4().hex)
    _upsert_env_var(env_path, "ADMIN_EMAIL", "admin@example.com")
    _upsert_env_var(env_path, "ADMIN_PASSWORD", "admin-password")

    if shutil.which("docker") is None:
        pytest.skip("docker not found in PATH; skipping E2E tests")

    cp = subprocess.run(["docker", "info"], text=True, capture_output=True)
    if cp.returncode != 0:
        pytest.skip("docker daemon not running; start Docker Desktop to run E2E tests")

    # Clean start
    _run(repo, _compose_cmd(repo) + ["down"], check=False)

    # Reset sandbox dir (best effort; avoids state leakage across runs)
    sandbox_dir = repo / "data_sandbox"
    if sandbox_dir.exists():
        try:
            shutil.rmtree(sandbox_dir)
        except Exception:
            # Windows can lock directories; best-effort file cleanup
            for p in sandbox_dir.rglob("*"):
                try:
                    if p.is_file():
                        p.unlink(missing_ok=True)
                except Exception:
                    pass
    (sandbox_dir / "audio").mkdir(parents=True, exist_ok=True)

    # Optional build (can be skipped for speed)
    no_build = os.environ.get("E2E_NO_BUILD", "").lower() in {"1", "true", "yes"}
    if not no_build:
        _run(repo, _compose_cmd(repo) + ["build"], check=True)

    # Migrate before up
    _run(
        repo,
        _compose_cmd(repo)
        + ["run", "--rm", "--no-deps", "api", "alembic", "upgrade", "head"],
        check=True,
    )

    # Up
    _run(repo, _compose_cmd(repo) + ["up", "-d", "--force-recreate"], check=True)

    # Wait API
    _wait_health(e2e_base_url, timeout_s=60)

    # Seed user_b (for ACL tests)
    _seed_user_b(repo, "user_b@example.com", "password-b")

    yield

    # Tear down
    _run(repo, _compose_cmd(repo) + ["down"], check=False)
