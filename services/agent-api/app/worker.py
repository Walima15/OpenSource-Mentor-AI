"""Arq worker entrypoint for durable background jobs.

Run with:
    arq app.worker.WorkerSettings

Requires REDIS_URL to be set. The web service enqueues jobs to this worker.
"""

from __future__ import annotations

import uuid

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import enforce_production_security
from app.db.crud import get_github_token
from app.db.models import IndexStatus, TrackedRepo
from app.db.session import SessionLocal
from app.services.ingestion_service import ingest_repository

logger = get_logger(__name__)


async def ingest_repo_task(ctx: dict, repo_id: str) -> int:
    """Index a repository. The GitHub token is loaded here, not from Redis."""
    db = SessionLocal()
    try:
        repo = db.get(TrackedRepo, uuid.UUID(repo_id))
        if repo is None:
            logger.warning("Repo %s not found for ingestion", repo_id)
            return 0
        try:
            token = get_github_token(db, str(repo.user_id))
        except Exception:
            logger.exception("Could not decrypt GitHub token for repo %s", repo_id)
            repo.index_status = IndexStatus.failed
            db.commit()
            raise
        return await ingest_repository(db, repo, token)
    finally:
        db.close()


async def on_startup(ctx: dict) -> None:
    configure_logging()
    enforce_production_security()
    logger.info("Arq worker started")


def _redis_settings():
    from arq.connections import RedisSettings

    return RedisSettings.from_dsn(settings.redis_url or "redis://localhost:6379")


class WorkerSettings:
    functions = [ingest_repo_task]
    on_startup = on_startup
    redis_settings = _redis_settings()
    max_jobs = 5
    job_timeout = 600
