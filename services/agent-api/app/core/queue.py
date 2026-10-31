"""Optional durable background queue (Arq + Redis).

When ``REDIS_URL`` is configured, jobs are enqueued to a separate Arq worker so
they survive web-process restarts. When it is not configured, callers fall back
to FastAPI ``BackgroundTasks`` (see the repos router).
"""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def queue_enabled() -> bool:
    return bool(settings.redis_url)


def _redis_settings():
    from arq.connections import RedisSettings

    return RedisSettings.from_dsn(settings.redis_url)


async def enqueue_ingestion(repo_id: str) -> bool:
    """Enqueue a repo ingestion job. Returns True if enqueued, False otherwise.

    The job argument is only the repository id. The worker loads the GitHub
    token from the database so the secret is not written to Redis.
    """
    if not queue_enabled():
        return False
    try:
        from arq import create_pool

        pool = await create_pool(_redis_settings())
        await pool.enqueue_job("ingest_repo_task", repo_id)
        await pool.close()
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Failed to enqueue ingestion; will fall back in-process")
        return False
