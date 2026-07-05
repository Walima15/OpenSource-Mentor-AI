"""Tests for concurrent, fault-tolerant file fetching during ingestion."""

from __future__ import annotations

import pytest

from app.services import ingestion_service as ing
from app.services.github_service import GitHubError


class _FakeRepo:
    owner = "o"
    name = "r"
    default_branch = "main"


class _FakeGH:
    def __init__(self, mapping, fail=()):
        self.mapping = mapping
        self.fail = set(fail)

    async def get_file_content(self, owner, name, path, branch):
        if path in self.fail:
            raise GitHubError(500, "boom")
        return self.mapping.get(path)


@pytest.mark.asyncio
async def test_fetch_files_preserves_order():
    gh = _FakeGH({"a.py": "A", "b.py": "B", "c.py": "C"})
    result = await ing._fetch_files(gh, _FakeRepo(), ["a.py", "b.py", "c.py"])
    assert result == [("a.py", "A"), ("b.py", "B"), ("c.py", "C")]


@pytest.mark.asyncio
async def test_fetch_files_tolerates_individual_failures():
    gh = _FakeGH({"a.py": "A", "b.py": "B"}, fail=["x.py"])
    result = await ing._fetch_files(gh, _FakeRepo(), ["a.py", "x.py", "b.py"])
    assert result == [("a.py", "A"), ("x.py", None), ("b.py", "B")]


@pytest.mark.asyncio
async def test_fetch_files_empty_list():
    gh = _FakeGH({})
    assert await ing._fetch_files(gh, _FakeRepo(), []) == []
