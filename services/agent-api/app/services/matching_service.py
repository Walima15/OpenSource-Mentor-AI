"""Issue-to-skill matching.

Given a contributor's tracked repositories, their cached open issues, and the
contributor's per-language skill scores, rank the issues as contribution
opportunities. Scoring is a transparent, deterministic heuristic (no LLM call)
so results are fast, cheap, and explainable.
"""

from __future__ import annotations

import uuid
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IssueCache, Skill, TrackedRepo

# Scoring weights (kept as named constants so the heuristic is easy to tune).
BASE_SCORE = 40.0
KNOWN_LANGUAGE_BONUS = 25.0
KNOWN_LANGUAGE_SKILL_WEIGHT = 0.15  # up to +15 for a maxed-out skill
NEW_LANGUAGE_BONUS = 8.0
GOOD_FIRST_ISSUE_BONUS = 15.0
HELP_WANTED_BONUS = 8.0
BUG_BONUS = 5.0
DOCS_BONUS = 6.0
UNCLAIMED_BONUS = 5.0
CROWDED_PENALTY = 6.0
CROWDED_COMMENTS = 15


class SkillInfo(NamedTuple):
    level: str
    score: int


def _has_label(labels: list[str], *needles: str) -> bool:
    lowered = [label.lower() for label in labels]
    return any(needle in label for label in lowered for needle in needles)


def score_issue(
    issue: dict,
    repo_language: str | None,
    skills: dict[str, SkillInfo],
) -> tuple[float, list[str]]:
    """Return a 0-100 relevance score and human-readable reasons for an issue."""
    score = BASE_SCORE
    reasons: list[str] = []
    labels = [str(label) for label in issue.get("labels", [])]

    skill = skills.get(repo_language) if repo_language else None
    if repo_language and skill is not None:
        score += KNOWN_LANGUAGE_BONUS + skill.score * KNOWN_LANGUAGE_SKILL_WEIGHT
        reasons.append(
            f"Matches your {repo_language} experience ({skill.level})"
        )
    elif repo_language:
        score += NEW_LANGUAGE_BONUS
        reasons.append(f"A chance to grow your {repo_language} skills")

    if _has_label(labels, "good first issue", "good-first-issue"):
        score += GOOD_FIRST_ISSUE_BONUS
        reasons.append("Beginner-friendly (good first issue)")
    if _has_label(labels, "help wanted"):
        score += HELP_WANTED_BONUS
        reasons.append("Maintainers are asking for help")
    if _has_label(labels, "bug"):
        score += BUG_BONUS
        reasons.append("Bug fix")
    if _has_label(labels, "documentation", "docs"):
        score += DOCS_BONUS
        reasons.append("Documentation (great for a first PR)")

    comments = int(issue.get("comments", 0) or 0)
    if comments == 0:
        score += UNCLAIMED_BONUS
        reasons.append("Unclaimed - no discussion yet")
    elif comments >= CROWDED_COMMENTS:
        score -= CROWDED_PENALTY

    return min(round(score, 1), 100.0), reasons


def _issue_from_cache(row: IssueCache) -> dict:
    raw = row.raw if isinstance(row.raw, dict) else {}
    return {
        "number": row.github_issue_number,
        "title": row.title,
        "labels": list(row.labels or []),
        "state": row.state,
        "url": raw.get("url", ""),
        "comments": raw.get("comments", 0),
        "created_at": raw.get("created_at", ""),
        "body": raw.get("body"),
    }


def recommend_for_user(db: Session, user_id: str, limit: int = 20) -> list[dict]:
    """Rank cached issues from a user's tracked repos against their skills."""
    uid = uuid.UUID(user_id)
    repos = db.scalars(
        select(TrackedRepo).where(TrackedRepo.user_id == uid)
    ).all()
    if not repos:
        return []
    repo_by_id = {repo.id: repo for repo in repos}

    skills = {
        skill.language: SkillInfo(level=skill.level.value, score=skill.score)
        for skill in db.scalars(select(Skill).where(Skill.user_id == uid)).all()
    }

    cached = db.scalars(
        select(IssueCache)
        .where(IssueCache.repo_id.in_(list(repo_by_id.keys())))
        .where(IssueCache.state == "open")
    ).all()

    recommendations: list[dict] = []
    for row in cached:
        repo = repo_by_id.get(row.repo_id)
        if repo is None:
            continue
        issue = _issue_from_cache(row)
        score, reasons = score_issue(issue, repo.primary_language, skills)
        recommendations.append(
            {
                "repo_id": repo.id,
                "repo_full_name": repo.full_name,
                "issue_number": issue["number"],
                "title": issue["title"],
                "url": issue["url"],
                "labels": issue["labels"],
                "comments": issue["comments"],
                "language": repo.primary_language,
                "score": score,
                "reasons": reasons,
            }
        )

    recommendations.sort(
        key=lambda r: (r["score"], r["issue_number"]), reverse=True
    )
    return recommendations[:limit]
