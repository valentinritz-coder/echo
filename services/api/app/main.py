from datetime import date
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import Literal
import uuid

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session, selectinload

from app.db import engine, get_db
from app.middleware.request_id import RequestIdMiddleware, configure_json_logging
from app.models import Entry, EntryAsset, Question, User
from app.routes.auth import router as auth_router
from app.routes.system import router as system_router
from app.schemas import (
    EntriesListResponse,
    EntryAssetOut,
    EntryOut,
    EntryUpdateIn,
    QuestionOut,
)
from app.security import get_current_user, hash_password
from app.settings import settings
from app.storage import (
    ALLOWED_IMAGE_MIME_TYPES,
    ALLOWED_MIME_TYPES,
    stream_upload_to_disk,
    validate_image_signature,
)

logger = logging.getLogger(__name__)
api_v1_router = APIRouter(prefix="/api/v1")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_json_logging()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    if not inspect(engine).has_table("entries"):
        logger.warning("Database not initialized. Run: alembic upgrade head")
        yield
        return

    with Session(engine) as db:
        _seed_admin_user(db)

    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)


FROZEN_ERROR = {
    "error_code": "ENTRY_FROZEN_IMMUTABLE",
    "detail": "Entry is frozen and cannot be modified",
}

if "*" in settings.allowed_origins:
    raise RuntimeError("Wildcard origin '*' is not allowed in ALLOWED_ORIGINS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(RequestIdMiddleware)


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-site"
    if request.url.path.startswith("/api/"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )
    if request.url.path == "/api/v1/version":
        response.headers["Cache-Control"] = "no-store"
    if settings.enable_hsts:
        response.headers["Strict-Transport-Security"] = (
            f"max-age={settings.hsts_max_age}; includeSubDomains"
        )
    return response


SEED_QUESTIONS: list[tuple[str, str]] = [
    ("Quel moment t'a fait sourire aujourd'hui ?", "gratitude"),
    ("Qu'as-tu appris de nouveau cette semaine ?", "apprentissage"),
    ("Quelle personne t'a inspiré récemment ?", "relations"),
    ("Quelle petite victoire veux-tu célébrer ?", "accomplissement"),
    ("Quel souvenir veux-tu garder de cette journée ?", "memoire"),
    ("Qu'est-ce qui t'a surpris positivement ?", "surprise"),
    ("Quel défi as-tu surmonté récemment ?", "resilience"),
    ("Comment prends-tu soin de toi en ce moment ?", "bien-etre"),
    ("Quel objectif te motive pour demain ?", "projection"),
    ("Quelle émotion as-tu le plus ressentie aujourd'hui ?", "emotion"),
]


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and {"error_code", "detail"}.issubset(exc.detail):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": str(exc.detail["error_code"]),
                "detail": str(exc.detail["detail"]),
            },
        )
    if isinstance(exc.detail, dict) and {"code", "message"}.issubset(exc.detail):
        error = {"code": str(exc.detail["code"]), "message": str(exc.detail["message"])}
    else:
        error = {"code": str(exc.status_code), "message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error},
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "422",
                "message": "Validation error",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
def generic_exception_handler(_, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "500", "message": "Internal server error"}},
    )


@api_v1_router.get("/version")
def version() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version}


def _ensure_questions_seeded(db: Session) -> None:
    count = db.query(Question).count()
    if count:
        return
    for idx, (text, category) in enumerate(SEED_QUESTIONS, start=1):
        db.add(Question(id=idx, text=text, category=category, is_active=True))
    db.commit()


def _seed_admin_user(db: Session) -> None:
    if settings.app_env != "development":
        return
    if not settings.admin_email or not settings.admin_password:
        return

    existing = db.query(User).filter(User.email == settings.admin_email).first()
    if existing is not None:
        return

    db.add(
        User(
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            is_active=True,
        )
    )
    db.commit()


def _get_entry_or_404(
    db: Session, entry_id: str, *, load_assets: bool = False
) -> Entry:
    query = select(Entry).where(Entry.id == entry_id)
    if load_assets:
        query = query.options(selectinload(Entry.assets))
    entry = db.execute(query).scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


def _ensure_owner(entry: Entry, current_user: User) -> None:
    if entry.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail={"code": "forbidden", "message": "Not allowed"}
        )


def _ensure_not_frozen(entry: Entry) -> None:
    if entry.is_frozen:
        raise HTTPException(status_code=409, detail=FROZEN_ERROR)


def _validate_text_content(text_content: str | None) -> None:
    if text_content is None:
        return
    if len(text_content) > settings.max_text_chars:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "text_content_too_long",
                "message": (
                    "text_content length exceeds "
                    f"MAX_TEXT_CHARS ({settings.max_text_chars})"
                ),
            },
        )


def _parse_image_dimensions(path: Path, mime: str) -> tuple[int | None, int | None]:
    try:
        data = path.read_bytes()
    except OSError:
        return None, None

    if (
        mime == "image/png"
        and len(data) >= 24
        and data.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return width, height

    if mime == "image/jpeg":
        idx = 2
        total = len(data)
        while idx + 9 < total:
            if data[idx] != 0xFF:
                idx += 1
                continue
            marker = data[idx + 1]
            idx += 2
            while marker == 0xFF and idx < total:
                marker = data[idx]
                idx += 1
            if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
                continue
            if idx + 1 >= total:
                break
            seg_len = (data[idx] << 8) + data[idx + 1]
            if seg_len < 2 or idx + seg_len > total:
                break
            if marker in {0xC0, 0xC2} and seg_len >= 7:
                height = (data[idx + 3] << 8) + data[idx + 4]
                width = (data[idx + 5] << 8) + data[idx + 6]
                return width, height
            idx += seg_len

    return None, None


def _asset_download_url(request: Request, asset_id: str) -> str:
    return str(request.url_for("download_asset", asset_id=asset_id))


def _entry_audio_url(request: Request, entry_id: str) -> str:
    return str(request.url_for("get_entry_audio", entry_id=entry_id))


def _serialize_asset(request: Request, asset: EntryAsset) -> EntryAssetOut:
    serialized = EntryAssetOut.model_validate(asset, from_attributes=True)
    return serialized.model_copy(
        update={"download_url": _asset_download_url(request, asset.id)}
    )


def _serialize_entry(request: Request, entry: Entry) -> EntryOut:
    serialized = EntryOut.model_validate(entry, from_attributes=True)
    assets = list(entry.assets or [])
    assets = [asset for asset in assets if asset.asset_type == "image"]
    return serialized.model_copy(
        update={
            "assets": [_serialize_asset(request, asset) for asset in assets],
            "audio_url": (
                _entry_audio_url(request, entry.id)
                if entry.audio_path is not None and entry.audio_mime is not None
                else None
            ),
        }
    )


@api_v1_router.get("/questions/today", response_model=QuestionOut)
def get_question_today(
    _: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Question:
    _ensure_questions_seeded(db)
    questions = (
        db.execute(
            select(Question).where(Question.is_active.is_(True)).order_by(Question.id)
        )
        .scalars()
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No active question")
    selected = questions[date.today().toordinal() % len(questions)]
    return selected


@api_v1_router.post("/entries", response_model=EntryOut)
async def create_entry(
    request: Request,
    question_id: int = Form(...),
    text_content: str | None = Form(default=None),
    text: str | None = Form(default=None),
    audio_file: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EntryOut:
    _ensure_questions_seeded(db)
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    candidates = [text_content, text]
    final_text = None
    for candidate in candidates:
        if candidate is None:
            continue
        normalized = candidate.strip()
        if normalized != "":
            final_text = normalized
            break

    if audio_file is None and final_text is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "entry_empty",
                "message": "Either text or audio_file is required",
            },
        )
    if final_text is not None:
        _validate_text_content(final_text)

    entry_id = str(uuid.uuid4())
    relative_path: Path | None = None
    content_type: str | None = None
    audio_size: int | None = None
    audio_sha256: str | None = None
    audio_duration_ms: int | None = None

    if audio_file is not None:
        content_type = audio_file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "unsupported_mime",
                    "message": "Unsupported audio MIME type",
                },
            )

        ext = ALLOWED_MIME_TYPES[content_type]
        relative_path = Path("audio") / f"{entry_id}{ext}"
        absolute_path = settings.data_dir / relative_path
        upload_info = await stream_upload_to_disk(
            upload=audio_file,
            dst_path=absolute_path,
            max_bytes=settings.max_upload_bytes,
            expected_mime=content_type,
            expected_ext=ext,
        )
        audio_size = int(upload_info["size"])
        audio_sha256 = str(upload_info["sha256"])
        audio_duration_ms = upload_info["duration_ms"]

    entry = Entry(
        id=entry_id,
        user_id=current_user.id,
        question_id=question_id,
        audio_path=str(relative_path) if relative_path is not None else None,
        audio_mime=content_type,
        audio_size=audio_size,
        audio_sha256=audio_sha256,
        audio_duration_ms=audio_duration_ms,
        text_content=final_text,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    entry = db.execute(
        select(Entry).options(selectinload(Entry.assets)).where(Entry.id == entry_id)
    ).scalar_one()
    return _serialize_entry(request, entry)


@api_v1_router.get("/entries", response_model=EntriesListResponse)
def list_entries(
    request: Request,
    limit: int = Query(
        default=50, ge=1, description="Page size. Values above 200 are clamped to 200."
    ),
    offset: int = Query(default=0, ge=0),
    sort: Literal[
        "created_at_desc", "created_at_asc", "id_asc", "id_desc"
    ] = "created_at_desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EntriesListResponse:
    order_by_map = {
        "created_at_desc": (Entry.created_at.desc(), Entry.id.desc()),
        "created_at_asc": (Entry.created_at.asc(), Entry.id.asc()),
        "id_asc": (Entry.id.asc(),),
        "id_desc": (Entry.id.desc(),),
    }
    clamped_limit = min(limit, 200)
    entries = (
        db.execute(
            select(Entry)
            .options(selectinload(Entry.assets))
            .where(Entry.user_id == current_user.id)
            .order_by(*order_by_map[sort])
            .offset(offset)
            .limit(clamped_limit)
        )
        .scalars()
        .all()
    )
    next_offset = offset + len(entries) if len(entries) == clamped_limit else None
    return EntriesListResponse(
        items=[_serialize_entry(request, entry) for entry in entries],
        next_offset=next_offset,
        limit=clamped_limit,
        offset=offset,
    )


@api_v1_router.get("/entries/{entry_id}", response_model=EntryOut)
def get_entry(
    request: Request,
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EntryOut:
    entry = _get_entry_or_404(db, entry_id, load_assets=True)
    _ensure_owner(entry, current_user)
    return _serialize_entry(request, entry)


@api_v1_router.post("/entries/{entry_id}/freeze")
def freeze_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str | bool]:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)

    if not entry.is_frozen:
        entry.is_frozen = True
        db.commit()

    return {"status": "frozen", "id": entry_id, "is_frozen": True}


@api_v1_router.post("/entries/{entry_id}/assets", response_model=EntryAssetOut)
async def upload_entry_asset(
    request: Request,
    entry_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EntryAssetOut:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)
    _ensure_not_frozen(entry)

    existing_assets_count = db.execute(
        select(func.count())
        .select_from(EntryAsset)
        .where(
            EntryAsset.entry_id == entry_id,
            EntryAsset.asset_type == "image",
        )
    ).scalar_one()
    if existing_assets_count >= settings.max_images_per_entry:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "too_many_assets",
                "message": (
                    "Entry reached MAX_IMAGES_PER_ENTRY "
                    f"({settings.max_images_per_entry})"
                ),
            },
        )

    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_image_mime",
                "message": "Unsupported image MIME type",
            },
        )

    asset_id = str(uuid.uuid4())
    ext = ALLOWED_IMAGE_MIME_TYPES[content_type]
    relative_path = Path("images") / entry_id / f"{asset_id}{ext}"
    absolute_path = settings.data_dir / relative_path

    upload_info = await stream_upload_to_disk(
        upload=file,
        dst_path=absolute_path,
        max_bytes=settings.max_upload_image_bytes,
        expected_mime=content_type,
        expected_ext=ext,
        signature_validator=validate_image_signature,
        invalid_signature_error_code="invalid_image_signature",
        invalid_signature_error_message="Image signature does not match MIME type",
        payload_too_large_error_message="Image file exceeds upload size limit",
    )

    width, height = _parse_image_dimensions(absolute_path, content_type)

    asset = EntryAsset(
        id=asset_id,
        entry_id=entry.id,
        user_id=current_user.id,
        asset_type="image",
        path=str(relative_path),
        mime=content_type,
        size=int(upload_info["size"]),
        sha256=str(upload_info["sha256"]),
        width=width,
        height=height,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _serialize_asset(request, asset)


@api_v1_router.get("/entries/{entry_id}/assets", response_model=list[EntryAssetOut])
def list_entry_assets(
    request: Request,
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EntryAssetOut]:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)
    assets = (
        db.execute(
            select(EntryAsset)
            .where(EntryAsset.entry_id == entry_id, EntryAsset.asset_type == "image")
            .order_by(EntryAsset.created_at.asc())
        )
        .scalars()
        .all()
    )
    return [_serialize_asset(request, asset) for asset in assets]


@api_v1_router.get("/assets/{asset_id}", name="download_asset")
def download_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    asset = db.get(EntryAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={"code": "forbidden", "message": "Not allowed"},
        )

    if asset.asset_type != "image":
        raise HTTPException(
            status_code=404,
            detail={"code": "asset_not_image", "message": "Asset is not an image"},
        )

    path = settings.data_dir / asset.path
    if not path.exists():
        raise HTTPException(status_code=404, detail="Asset file not found")
    return FileResponse(path=path, media_type=asset.mime, filename=path.name)


@api_v1_router.get("/entries/{entry_id}/audio", name="get_entry_audio")
def get_entry_audio(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)
    if entry.audio_path is None or entry.audio_mime is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "no_audio", "message": "Entry has no audio"},
        )

    path = settings.data_dir / entry.audio_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path=path, media_type=entry.audio_mime, filename=path.name)


@api_v1_router.patch("/entries/{entry_id}", response_model=EntryOut)
def update_entry(
    payload: EntryUpdateIn,
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Entry:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)
    _ensure_not_frozen(entry)

    if payload.question_id is None and payload.text_content is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "empty_update",
                "message": "At least one updatable field must be provided",
            },
        )

    if payload.question_id is not None:
        question = db.get(Question, payload.question_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")
        entry.question_id = payload.question_id

    if payload.text_content is not None:
        _validate_text_content(payload.text_content)
        entry.text_content = payload.text_content

    db.commit()
    db.refresh(entry)
    return entry


@api_v1_router.post("/entries/{entry_id}/audio", response_model=EntryOut)
async def upload_entry_audio(
    entry_id: str,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Entry:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)
    _ensure_not_frozen(entry)

    content_type = audio_file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_mime",
                "message": "Unsupported audio MIME type",
            },
        )

    ext = ALLOWED_MIME_TYPES[content_type]
    relative_path = Path("audio") / f"{entry_id}{ext}"
    absolute_path = settings.data_dir / relative_path
    upload_info = await stream_upload_to_disk(
        upload=audio_file,
        dst_path=absolute_path,
        max_bytes=settings.max_upload_bytes,
        expected_mime=content_type,
        expected_ext=ext,
    )
    entry.audio_path = str(relative_path)
    entry.audio_mime = content_type
    entry.audio_size = int(upload_info["size"])
    entry.audio_sha256 = str(upload_info["sha256"])
    entry.audio_duration_ms = upload_info["duration_ms"]
    db.commit()
    db.refresh(entry)
    return entry


@api_v1_router.delete("/entries/{entry_id}/audio")
def delete_entry_audio(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)
    _ensure_not_frozen(entry)

    path = settings.data_dir / entry.audio_path
    path.unlink(missing_ok=True)
    entry.audio_path = f"audio/deleted-{entry_id}.bin"
    entry.audio_mime = "application/octet-stream"
    entry.audio_size = 0
    entry.audio_sha256 = "0" * 64
    entry.audio_duration_ms = None
    db.commit()
    return {"status": "audio_deleted", "id": entry_id}


@api_v1_router.delete("/entries/{entry_id}")
def delete_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    entry = _get_entry_or_404(db, entry_id)
    _ensure_owner(entry, current_user)
    _ensure_not_frozen(entry)

    if entry.audio_path is not None:
        path = settings.data_dir / entry.audio_path
        path.unlink(missing_ok=True)
    db.delete(entry)
    db.commit()
    return {"status": "deleted", "id": entry_id}


api_v1_router.include_router(auth_router)
api_v1_router.include_router(system_router)
app.include_router(api_v1_router)
