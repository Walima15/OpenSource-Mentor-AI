"""Issue recommendation endpoints (issue-to-skill matching)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, github_token
from app.core.security import AuthUser
from app.db.models import TrackedRepo
from app.schemas.models import RecommendationOut, ScanResultOut
from app.services.github_service import GitHubError
from app.services.matching_service import recommend_for_user
from app.services.scanning_service import scan_repo_issues

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationOut])
async def list_recommendations(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> list[RecommendationOut]:
    """Ranked contribution opportunities from already-cached issues."""
    recs = await run_in_threadpool(recommend_for_user, db, user.id, limit)
    return [RecommendationOut(**r) for r in recs]


@router.post("/scan", response_model=ScanResultOut)
async def scan_and_cache(
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> ScanResultOut:
    """On-demand scan of the user's tracked repos to refresh cached issues.

    This is the synchronous fallback for the (optional) background cron worker,
    so recommendations work even without Redis configured.
    """
    repos = db.scalars(
        select(TrackedRepo).where(TrackedRepo.user_id == uuid.UUID(user.id))
    ).all()
    scanned = 0
    cached = 0
    for repo in repos:
        try:
            cached += await scan_repo_issues(db, repo, token)
            scanned += 1
        except GitHubError:
            continue
    return ScanResultOut(scanned_repos=scanned, cached_issues=cached)
