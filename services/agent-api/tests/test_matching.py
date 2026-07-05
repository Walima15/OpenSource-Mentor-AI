"""Tests for the issue-to-skill matching heuristic."""

from __future__ import annotations

from app.services.matching_service import (
    BASE_SCORE,
    SkillInfo,
    score_issue,
)


def _issue(labels=None, comments=0):
    return {
        "number": 1,
        "title": "t",
        "labels": labels or [],
        "comments": comments,
    }


def test_known_language_scores_higher_than_unknown():
    skills = {"Python": SkillInfo("advanced", 80)}
    known, _ = score_issue(_issue(), "Python", skills)
    unknown, _ = score_issue(_issue(), "Rust", skills)
    assert known > unknown


def test_good_first_issue_adds_bonus_and_reason():
    skills: dict[str, SkillInfo] = {}
    score, reasons = score_issue(
        _issue(labels=["good first issue"]), None, skills
    )
    assert score > BASE_SCORE
    assert any("Beginner-friendly" in r for r in reasons)


def test_help_wanted_and_unclaimed_reasons():
    score, reasons = score_issue(
        _issue(labels=["help wanted"], comments=0), None, {}
    )
    assert any("help" in r.lower() for r in reasons)
    assert any("Unclaimed" in r for r in reasons)


def test_crowded_issue_is_penalized():
    quiet, _ = score_issue(_issue(comments=0), None, {})
    crowded, _ = score_issue(_issue(comments=50), None, {})
    assert crowded < quiet


def test_score_is_capped_at_100():
    skills = {"Python": SkillInfo("advanced", 100)}
    labels = ["good first issue", "help wanted", "bug", "documentation"]
    score, _ = score_issue(_issue(labels=labels), "Python", skills)
    assert score <= 100.0


def test_known_language_reason_mentions_language_and_level():
    skills = {"TypeScript": SkillInfo("intermediate", 40)}
    _, reasons = score_issue(_issue(), "TypeScript", skills)
    assert any("TypeScript" in r and "intermediate" in r for r in reasons)
