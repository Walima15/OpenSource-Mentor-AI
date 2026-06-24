"""Health and dependency-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

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
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    try:
        from app.services.vector_store import get_vector_store

        get_vector_store().client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["qdrant"] = f"error: {exc}"

    checks["anthropic"] = "configured" if settings.anthropic_api_key else "missing key"
    overall = "ok" if all(v == "ok" or v == "configured" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
