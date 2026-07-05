"""Tests for issue scanning into the cache (no DB or network required)."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.services import scanning_service


class _FakeGH:
    """Stand-in for GitHubService that returns the same issues for any label."""

    def __init__(self, issues):
        self._issues = issues

    async def list_issues(self, owner, name, labels=None):
        return self._issues


class _FakeDB:
    def __init__(self, existing=None):
        self.existing = existing or {}
        self.added = []

    def scalar(self, _stmt):
        # Simplest possible behavior: nothing pre-existing in the cache.
        return None

    def add(self, obj):
        self.added.append(obj)


def _repo():
    return SimpleNamespace(
        id=uuid.uuid4(), owner="o", name="r", full_name="o/r"
    )


@pytest.mark.asyncio
async def test_scan_repo_issues_dedupes_and_inserts(monkeypatch):
    issues = [
        {"number": 1, "title": "A", "labels": ["good first issue"], "state": "open"},
        {"number": 2, "title": "B", "labels": ["help wanted"], "state": "open"},
    ]
    monkeypatch.setattr(
        scanning_service, "GitHubService", lambda token=None: _FakeGH(issues)
    )
    db = _FakeDB()
    count = await scanning_service.scan_repo_issues(db, _repo(), token=None)
    # Two unique issue numbers despite being returned for each label.
    assert count == 2
    assert len(db.added) == 2


@pytest.mark.asyncio
async def test_scan_repo_issues_handles_empty(monkeypatch):
    monkeypatch.setattr(
        scanning_service, "GitHubService", lambda token=None: _FakeGH([])
    )
    db = _FakeDB()
    count = await scanning_service.scan_repo_issues(db, _repo(), token=None)
    assert count == 0
    assert db.added == []
