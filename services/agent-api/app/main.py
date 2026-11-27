"""OSMA FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.agent.mentor import MentorAgent
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimiter
from app.db.session import init_db, make_engine, session_factory
from app.github.client import GitHubClient
from app.llm.client import OpenAICompatibleClient
from app.tools.registry import build_registry

logger = get_logger(__name__)
_MAX_BODY = 100_000


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        length = request.headers.get("content-length")
        if length:
            try:
                if int(length) > _MAX_BODY:
                    return JSONResponse({"detail": "Request too large"}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "Invalid content length"}, status_code=400)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = make_engine(settings.database_url)
    init_db(engine)
    github = GitHubClient(token=settings.github_token)
    llm = OpenAICompatibleClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
    )
    tools = build_registry(github)
    app.state.settings = settings
    app.state.engine = engine
    app.state.Session = session_factory(engine)
    app.state.github = github
    app.state.llm = llm
    app.state.tools = tools
    app.state.agent = MentorAgent(llm, tools, max_rounds=settings.max_tool_rounds)
    app.state.chat_limiter = RateLimiter(settings.rate_limit_chat_per_minute, 60)
    app.state.read_limiter = RateLimiter(settings.rate_limit_read_per_minute, 60)
    logger.info(
        "osma api ready llm_configured=%s github_token_configured=%s",
        settings.llm_configured,
        bool(settings.github_token),
    )
    yield
    llm.close()
    github.close()
    engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="OSMA",
        summary="Open Source Mentor for Bitcoin contributors",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    app.include_router(router)
    return app


app = create_app()
