from datetime import date
import logging
from pathlib import Path
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.models import Entry, Question
from app.schemas import EntryOut, QuestionOut
from app.settings import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/aac": ".aac",
    "audio/3gpp": ".3gp",
    "audio/3gpp2": ".3g2",
    "audio/webm": ".webm",
    "audio/aiff": ".aiff",
}

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


@app.on_event("startup")
def startup() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    if not inspect(engine).has_table("entries"):
        logger.warning("Database not initialized. Run: alembic upgrade head")


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
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
        content={"error": {"code": "422", "message": "Validation error", "details": exc.errors()}},
    )


@app.exception_handler(Exception)
def generic_exception_handler(_, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "500", "message": "Internal server error"}},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version}


def _ensure_questions_seeded(db: Session) -> None:
    count = db.query(Question).count()
    if count:
        return
    for idx, (text, category) in enumerate(SEED_QUESTIONS, start=1):
        db.add(Question(id=idx, text=text, category=category, is_active=True))
    db.commit()


@app.get("/questions/today", response_model=QuestionOut)
def get_question_today(db: Session = Depends(get_db)) -> Question:
    _ensure_questions_seeded(db)
    questions = db.execute(select(Question).where(Question.is_active.is_(True)).order_by(Question.id)).scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail="No active question")
    selected = questions[date.today().toordinal() % len(questions)]
    return selected


@app.post("/entries", response_model=EntryOut)
async def create_entry(
    user_id: str = Form(...),
    question_id: int = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Entry:
    _ensure_questions_seeded(db)
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    content_type = audio_file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail={"code": "unsupported_mime", "message": "Unsupported audio MIME type"},
        )

    file_bytes = await audio_file.read()
    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Audio file exceeds 25 MB")

    entry_id = str(uuid.uuid4())
    ext = ALLOWED_MIME_TYPES[content_type]
    relative_path = Path("audio") / f"{entry_id}{ext}"
    absolute_path = settings.data_dir / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(file_bytes)

    entry = Entry(
        id=entry_id,
        user_id=user_id,
        question_id=question_id,
        audio_path=str(relative_path),
        audio_mime=content_type,
        audio_size=len(file_bytes),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/entries", response_model=list[EntryOut])
def list_entries(user_id: str = Query(...), db: Session = Depends(get_db)) -> list[Entry]:
    entries = (
        db.execute(select(Entry).where(Entry.user_id == user_id).order_by(Entry.created_at.desc()))
        .scalars()
        .all()
    )
    return entries


@app.get("/entries/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: str, db: Session = Depends(get_db)) -> Entry:
    entry = db.get(Entry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@app.get("/entries/{entry_id}/audio")
def get_entry_audio(entry_id: str, db: Session = Depends(get_db)) -> FileResponse:
    entry = db.get(Entry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    path = settings.data_dir / entry.audio_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path=path, media_type=entry.audio_mime, filename=path.name)


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    entry = db.get(Entry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    path = settings.data_dir / entry.audio_path
    db.delete(entry)
    db.commit()
    path.unlink(missing_ok=True)
    return {"status": "deleted", "id": entry_id}
