"""Environment configuration.

Secrets come from the environment or the repo-root `.env`. Nothing here has a
real default key.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.security import no_control_lines, validate_llm_base_url

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


def _env_file() -> str | None:
    if os.environ.get("APP_ENV") == "test":
        return None
    if _ROOT_ENV.is_file():
        return str(_ROOT_ENV)
    return None


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/osma.db"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    github_token: str = ""

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    rate_limit_chat_per_minute: int = Field(default=20, ge=1, le=10_000)
    rate_limit_read_per_minute: int = Field(default=120, ge=1, le=10_000)
    max_tool_rounds: int = Field(default=4, ge=1, le=8)

    model_config = SettingsConfigDict(
        env_file=_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("openai_api_key", "github_token", "openai_model")
    @classmethod
    def _no_newlines(cls, value: str, info) -> str:
        return no_control_lines(value, info.field_name)

    @field_validator("openai_base_url")
    @classmethod
    def _base_url(cls, value: str) -> str:
        return validate_llm_base_url(value)

    @field_validator("cors_origins")
    @classmethod
    def _cors(cls, value: str) -> str:
        origins = [item.strip() for item in value.split(",") if item.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must list at least one origin")
        if any(origin == "*" for origin in origins):
            raise ValueError("Wildcard CORS is not allowed")
        for origin in origins:
            if any(char in origin for char in "\r\n\x00") or not origin.startswith(
                ("http://", "https://")
            ):
                raise ValueError("CORS origin must be an http(s) origin")
        return ",".join(origins)

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
