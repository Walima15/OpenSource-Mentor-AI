"""Health and dependency-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import engine

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@router.get("/health/deps")
def health_deps() -> dict:
    checks: dict[str, str] = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # noqa: BLE001
        logger.exception("Database health check failed")
        checks["database"] = "error"

    try:
        from app.services.vector_store import get_vector_store

        get_vector_store().client.get_collections()
        checks["qdrant"] = "ok"
    except Exception:  # noqa: BLE001
        logger.exception("Qdrant health check failed")
        checks["qdrant"] = "error"

    checks["anthropic"] = "configured" if settings.anthropic_api_key else "missing key"
    overall = "ok" if all(v == "ok" or v == "configured" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
