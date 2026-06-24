"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_env: str = Field(default="development")
    app_name: str = Field(default="OpenSource Mentor AI")
    cors_origins: str = Field(default="http://localhost:3000")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://osma:osma@localhost:5432/osma"
    )

    # Supabase
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    supabase_jwt_secret: str = Field(default="")

    # Anthropic
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-3-5-sonnet-latest")

    # GitHub
    github_client_id: str = Field(default="")
    github_client_secret: str = Field(default="")
    github_fallback_token: str = Field(default="")

    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str = Field(default="")
    qdrant_collection: str = Field(default="osma_repo_chunks")

    # Embeddings
    embedding_provider: str = Field(default="fastembed")
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_dim: int = Field(default=384)

    # Security
    token_encryption_key: str = Field(default="")

    # Background queue (optional). When unset, ingestion runs in-process via
    # FastAPI BackgroundTasks instead of a durable Arq/Redis worker.
    redis_url: str = Field(default="")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
