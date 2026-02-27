from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "echo-mvp"
    app_version: str = "0.1.0"
    app_env: str = "development"
    data_dir: Path = Path("/app/data")
    max_upload_size_mb: int = 25
    # Maximum allowed size for optional entry text content.
    max_text_chars: int = 10_000

    jwt_secret_key: str = ""
    jwt_refresh_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_minutes: int = 60 * 24 * 7

    admin_email: str | None = None
    admin_password: str | None = None

    allowed_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://localhost:8000",
    ]
    allowed_hosts: Annotated[list[str], NoDecode] = [
        "localhost",
        "127.0.0.1",
        "testserver",
    ]
    enable_hsts: bool = False
    hsts_max_age: int = 31536000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    @field_validator("allowed_origins", "allowed_hosts", mode="before")
    @classmethod
    def _parse_csv_list(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
