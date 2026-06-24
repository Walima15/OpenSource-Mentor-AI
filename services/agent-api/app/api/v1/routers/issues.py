"""Issue discovery endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, github_token
from app.core.security import AuthUser
from app.db.crud import get_user_repo
from app.schemas.models import IssueOut
from app.services.github_service import (
    GOOD_FIRST_LABELS,
    GitHubError,
    GitHubService,
)

router = APIRouter(prefix="/repos", tags=["issues"])


@router.get("/{repo_id}/issues", response_model=list[IssueOut])
async def list_issues(
    repo_id: uuid.UUID,
    labels: str | None = Query(
        default=None,
        description="Comma-separated labels. Defaults to good-first-issue/help-wanted.",
    ),
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> list[IssueOut]:
    repo = get_user_repo(db, user.id, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")

    label_list = (
        [label.strip() for label in labels.split(",") if label.strip()]
        if labels
        else None
    )

    gh = GitHubService(token=token)
    try:
        if label_list:
            issues = await gh.list_issues(repo.owner, repo.name, labels=label_list)
        else:
            # Aggregate across the beginner-friendly labels.
            seen: dict[int, dict] = {}
            for label in GOOD_FIRST_LABELS:
                for issue in await gh.list_issues(
                    repo.owner, repo.name, labels=[label]
                ):
                    seen[issue["number"]] = issue
            issues = sorted(seen.values(), key=lambda i: i["number"], reverse=True)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return [IssueOut(**i) for i in issues]


@router.get("/{repo_id}/issues/{number}", response_model=IssueOut)
async def get_issue(
    repo_id: uuid.UUID,
    number: int,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> IssueOut:
    repo = get_user_repo(db, user.id, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")
    gh = GitHubService(token=token)
    try:
        issue = await gh.get_issue(repo.owner, repo.name, number)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return IssueOut(**issue)
