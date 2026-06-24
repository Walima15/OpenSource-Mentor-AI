"""Tests for pull-request service helpers."""

from __future__ import annotations

import importlib.util

import pytest

from app.services.pr_service import _plan_markdown, apply_unified_diff

_HAS_WHATTHEPATCH = importlib.util.find_spec("whatthepatch") is not None


def test_apply_empty_diff_returns_none():
    assert apply_unified_diff("hello\n", "") is None


def test_plan_markdown_contains_sections():
    md = _plan_markdown(
        "Do the thing",
        [{"order": 1, "title": "Step", "detail": "details"}],
        [{"path": "a.py", "reason": "because"}],
    )
    assert "# OSMA contribution plan" in md
    assert "## Steps" in md
    assert "## Files to change" in md
    assert "`a.py`" in md


@pytest.mark.skipif(not _HAS_WHATTHEPATCH, reason="whatthepatch not installed")
def test_apply_unified_diff_modifies_content():
    original = "line1\nline2\nline3\n"
    diff = (
        "--- a/f.txt\n"
        "+++ b/f.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line1\n"
        "-line2\n"
        "+line2-changed\n"
        " line3\n"
    )
    result = apply_unified_diff(original, diff)
    assert result is not None
    assert "line2-changed" in result
