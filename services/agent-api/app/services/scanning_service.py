"""Repository issue scanning.

Fetches beginner-friendly open issues (good first issue / help wanted) for
tracked repositories via the GitHub API and mirrors them into the
``issues_cache`` table. The cache decouples issue matching/recommendations from
live GitHub calls and powers the (optional) continuous background scan.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.crud import get_github_token
from app.db.models import IssueCache, TrackedRepo
from app.services.github_service import GOOD_FIRST_LABELS, GitHubError, GitHubService

logger = get_logger(__name__)


def _upsert_issue(db: Session, repo_id, issue: dict) -> None:
    existing = db.scalar(
        select(IssueCache).where(
            IssueCache.repo_id == repo_id,
            IssueCache.github_issue_number == issue["number"],
        )
    )
    payload = {
        "title": issue.get("title", ""),
        "labels": list(issue.get("labels", [])),
        "state": issue.get("state", "open"),
        "raw": {
            "url": issue.get("url", ""),
            "body": issue.get("body"),
            "comments": issue.get("comments", 0),
            "created_at": issue.get("created_at", ""),
        },
        "fetched_at": datetime.now(UTC),
    }
    if existing is None:
        db.add(
            IssueCache(
                repo_id=repo_id,
                github_issue_number=issue["number"],
                **payload,
            )
        )
    else:
        for key, value in payload.items():
            setattr(existing, key, value)


async def scan_repo_issues(
    db: Session, repo: TrackedRepo, token: str | None
) -> int:
    """Fetch beginner-friendly issues for a repo and cache them. Returns count."""
    seen: dict[int, dict] = {}
    async with GitHubService(token=token) as gh:
        for label in GOOD_FIRST_LABELS:
            for issue in await gh.list_issues(repo.owner, repo.name, labels=[label]):
                seen[issue["number"]] = issue

    for issue in seen.values():
        _upsert_issue(db, repo.id, issue)
    logger.info("Scanned %s: cached %d issues", repo.full_name, len(seen))
    return len(seen)


async def scan_repos_for_user(db: Session, user_id, token: str | None) -> int:
    """Scan every repo tracked by a single user. Returns total issues cached."""
    repos = db.scalars(
        select(TrackedRepo).where(TrackedRepo.user_id == user_id)
    ).all()
    total = 0
    for repo in repos:
        try:
            total += await scan_repo_issues(db, repo, token)
        except GitHubError:
            logger.warning("Scan failed for %s", repo.full_name, exc_info=True)
    return total


async def scan_all_tracked_repos(db: Session) -> int:
    """Scan all tracked repos across all users (used by the background cron).

    Uses each repo owner's stored GitHub token when available, otherwise the
    configured fallback token. Commits per repo so a single failure does not
    discard prior progress.
    """
    repos = db.scalars(select(TrackedRepo)).all()
    total = 0
    for repo in repos:
        try:
            token = get_github_token(db, str(repo.user_id))
        except Exception:  # noqa: BLE001 - fall back to unauthenticated/fallback token
            token = None
        try:
            total += await scan_repo_issues(db, repo, token)
            db.commit()
        except GitHubError:
            db.rollback()
            logger.warning("Background scan failed for %s", repo.full_name)
        except Exception:
            db.rollback()
            logger.exception("Unexpected error scanning %s", repo.full_name)
    return total
