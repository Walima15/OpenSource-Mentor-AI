"""Offline tests for GitHub service helpers (no network required)."""

from __future__ import annotations

from app.services.github_service import (
    GOOD_FIRST_LABELS,
    GitHubError,
    GitHubService,
    _format_issue,
)


def test_format_issue_maps_expected_fields():
    raw = {
        "number": 42,
        "title": "Fix the thing",
        "body": "Details here",
        "labels": [{"name": "bug"}, {"name": "good first issue"}],
        "state": "open",
        "html_url": "https://github.com/o/r/issues/42",
        "comments": 3,
        "created_at": "2024-01-01T00:00:00Z",
    }
    out = _format_issue(raw)
    assert out["number"] == 42
    assert out["title"] == "Fix the thing"
    assert out["labels"] == ["bug", "good first issue"]
    assert out["url"] == "https://github.com/o/r/issues/42"
    assert out["comments"] == 3


def test_format_issue_handles_string_labels_and_missing_fields():
    out = _format_issue({"number": 1, "title": "t", "labels": ["help wanted"]})
    assert out["labels"] == ["help wanted"]
    assert out["body"] is None
    assert out["state"] == "open"
    assert out["url"] == ""
    assert out["comments"] == 0


def test_good_first_labels_are_configured():
    assert "good first issue" in GOOD_FIRST_LABELS
    assert "help wanted" in GOOD_FIRST_LABELS


def test_headers_include_auth_only_when_token_present():
    with_token = GitHubService(token="abc123")._headers()
    assert with_token["Authorization"] == "Bearer abc123"
    assert with_token["Accept"] == "application/vnd.github+json"

    without_token = GitHubService(token=None)
    without_token.token = None  # ignore any configured fallback token
    assert "Authorization" not in without_token._headers()


def test_github_error_carries_status_and_message():
    err = GitHubError(404, "not found")
    assert err.status_code == 404
    assert "404" in str(err)
