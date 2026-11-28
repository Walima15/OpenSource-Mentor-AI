"""Test environment. Must run before the application imports settings."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_DIR = Path(tempfile.mkdtemp(prefix="osma-test-"))
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{_DIR / 'test.db'}"
# The suite pins an empty key and a cloud URL so tests never dial a local daemon.
# Product defaults (empty key, local Ollama, llama3.2) are asserted separately.
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
os.environ["OPENAI_MODEL"] = "gpt-4o-mini"
os.environ["GITHUB_TOKEN"] = ""
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["RATE_LIMIT_CHAT_PER_MINUTE"] = "1000"
os.environ["RATE_LIMIT_READ_PER_MINUTE"] = "1000"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OSMA_WORKSPACE_ROOT"] = str(_DIR / "workspaces")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
