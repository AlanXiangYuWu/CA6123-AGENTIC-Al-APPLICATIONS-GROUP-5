"""Settings loaded from .env via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    google_api_key: str | None = None
    llm_provider: str = "google"
    llm_model: str = "gemini-2.0-flash"
    bailian_api_key: str | None = None
    bailian_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    kb_store_path: str = "./kb_store"
    enable_rag: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
