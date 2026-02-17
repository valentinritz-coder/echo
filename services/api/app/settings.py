from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "echo-mvp"
    app_version: str = "0.1.0"
    app_env: str = "development"
    data_dir: Path = Path("/app/data")
    max_upload_size_mb: int = 25

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


settings = Settings()
