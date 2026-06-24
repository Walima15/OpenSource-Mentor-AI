"""Arq worker entrypoint for durable background jobs.

Run with:
    arq app.worker.WorkerSettings

Requires REDIS_URL to be set. The web service enqueues jobs to this worker.
"""

from __future__ import annotations

import uuid

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.models import TrackedRepo
from app.db.session import SessionLocal
from app.services.ingestion_service import ingest_repository

logger = get_logger(__name__)


async def ingest_repo_task(ctx: dict, repo_id: str, token: str | None) -> int:
    """Index a repository in the background worker."""
    db = SessionLocal()
    try:
        repo = db.get(TrackedRepo, uuid.UUID(repo_id))
        if repo is None:
            logger.warning("Repo %s not found for ingestion", repo_id)
            return 0
        return await ingest_repository(db, repo, token)
    finally:
        db.close()


async def on_startup(ctx: dict) -> None:
    configure_logging()
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
