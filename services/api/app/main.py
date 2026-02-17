from fastapi import FastAPI

from app.settings import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version}
