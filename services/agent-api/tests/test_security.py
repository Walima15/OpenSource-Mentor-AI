"""Security controls: input limits, redirects' server twin, encryption, docs."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.github_input import validate_github_name, validate_repo_file_path
from app.core.rate_limit import SlidingWindowLimiter
from app.main import app, create_app
from app.schemas.models import (
    BIO_MAX,
    CHAT_MESSAGE_MAX,
    INSTRUCTION_MAX,
    ChatIn,
    ProfileUpdate,
    RepoTrackIn,
    SuggestCodeIn,
)

client = TestClient(app)


def test_ingestion_job_does_not_accept_a_token():
    import inspect

    from app.core.queue import enqueue_ingestion
    from app.worker import ingest_repo_task

    assert list(inspect.signature(enqueue_ingestion).parameters) == ["repo_id"]
    assert list(inspect.signature(ingest_repo_task).parameters) == ["ctx", "repo_id"]


def test_github_names_reject_traversal():
    RepoTrackIn(owner="octocat", name="hello-world")
    RepoTrackIn(owner="osma", name="Hello_World.js")
    for owner, name in (
        ("..", "repo"),
        ("foo", ".."),
        ("foo/bar", "repo"),
        ("foo", "bar/baz"),
        (".", "repo"),
        ("foo..bar", "repo"),
    ):
        with pytest.raises(ValidationError):
            RepoTrackIn(owner=owner, name=name)
    with pytest.raises(ValueError):
        validate_github_name("../etc")


def test_suggestion_paths_reject_sensitive_targets():
    SuggestCodeIn(file_path="src/app.py", instruction="tighten the check")
    for path in (
        "../etc/passwd",
        "/etc/passwd",
        "~/.ssh/id_rsa",
        "C:/Windows/system32",
        ".git/config",
        "src/.git/config",
        ".github/workflows/ci.yml",
        "pkg/.github/workflows/release.yml",
        "src/../../secret",
    ):
        with pytest.raises(ValidationError):
            SuggestCodeIn(file_path=path)
    with pytest.raises(ValueError):
        validate_repo_file_path(".github/workflows/ci.yml")


def test_expensive_inputs_are_capped():
    ChatIn(message="hello")
    with pytest.raises(ValidationError):
        ChatIn(message="x" * (CHAT_MESSAGE_MAX + 1))
    SuggestCodeIn(file_path="a.py", instruction="y" * INSTRUCTION_MAX)
    with pytest.raises(ValidationError):
        SuggestCodeIn(file_path="a.py", instruction="y" * (INSTRUCTION_MAX + 1))
    ProfileUpdate(bio="z" * BIO_MAX)
    with pytest.raises(ValidationError):
        ProfileUpdate(bio="z" * (BIO_MAX + 1))


def test_rate_limiter_blocks_after_the_budget():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    limiter.check("user-1")
    limiter.check("user-1")
    with pytest.raises(HTTPException) as exc:
        limiter.check("user-1")
    assert exc.value.status_code == 429
    limiter.check("user-2")


def test_health_deps_hides_exception_text():
    res = client.get("/health/deps")
    assert res.status_code == 200
    checks = res.json()["checks"]
    allowed = {"ok", "error", "configured", "missing key"}
    assert set(checks.values()) <= allowed


def test_production_refuses_to_boot_without_encryption_key(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "token_encryption_key", "  ")
    with pytest.raises(RuntimeError, match="TOKEN_ENCRYPTION_KEY"):
        create_app()


def test_dev_without_secrets_does_not_use_a_hardcoded_key(monkeypatch):
    from app.core import security

    monkeypatch.setattr(security.settings, "app_env", "development")
    monkeypatch.setattr(security.settings, "token_encryption_key", "")
    monkeypatch.setattr(security.settings, "supabase_jwt_secret", "")
    with pytest.raises(RuntimeError, match="TOKEN_ENCRYPTION_KEY"):
        security._fernet()


def test_encrypt_roundtrip_with_explicit_key(monkeypatch):
    from app.core import security

    monkeypatch.setattr(
        security.settings, "token_encryption_key", Fernet.generate_key().decode()
    )
    cipher = security.encrypt_token("ghp_example")
    assert security.decrypt_token(cipher) == "ghp_example"


def test_docs_disabled_in_production(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(
        settings, "token_encryption_key", Fernet.generate_key().decode()
    )
    secured = create_app()
    assert secured.docs_url is None
    assert secured.redoc_url is None
    assert secured.openapi_url is None
    prod = TestClient(secured)
    assert prod.get("/docs").status_code == 404
    assert prod.get("/openapi.json").status_code == 404
    assert "docs" not in prod.get("/").json()
