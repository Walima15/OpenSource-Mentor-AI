"""FastAPI application factory and entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routers import (
    contribute,
    health,
    issues,
    mentor,
    pr,
    profile,
    repos,
)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import enforce_production_security

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)
    # Best-effort: ensure the Qdrant collection exists.
    try:
        from app.services.vector_store import get_vector_store

        get_vector_store().ensure_collection()
    except Exception:  # noqa: BLE001
        logger.warning("Could not ensure Qdrant collection at startup", exc_info=True)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    enforce_production_security()
    show_docs = not settings.is_production
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI mentor that guides developers through open-source contributions.",
        lifespan=lifespan,
        docs_url="/docs" if show_docs else None,
        redoc_url="/redoc" if show_docs else None,
        openapi_url="/openapi.json" if show_docs else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_prefix = "/api/v1"
    app.include_router(health.router)
    app.include_router(profile.router, prefix=api_prefix)
    app.include_router(repos.router, prefix=api_prefix)
    app.include_router(issues.router, prefix=api_prefix)
    app.include_router(mentor.router, prefix=api_prefix)
    app.include_router(contribute.router, prefix=api_prefix)
    app.include_router(pr.router, prefix=api_prefix)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.get("/")
    def root() -> dict:
        body = {"name": settings.app_name, "health": "/health"}
        if app.docs_url:
            body["docs"] = app.docs_url
        return body

    return app


app = create_app()
