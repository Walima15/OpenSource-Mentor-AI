"""Repository discovery, tracking, indexing, structure and docs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, github_token
from app.core.queue import enqueue_ingestion
from app.core.security import AuthUser
from app.db.crud import bump_skill, get_or_create_profile, get_user_repo
from app.db.models import IndexStatus, RepoIndexChunk, TrackedRepo
from app.db.session import SessionLocal
from app.schemas.models import (
    IndexStatusOut,
    RepoDocsOut,
    RepoSearchResult,
    RepoStructureNode,
    RepoStructureOut,
    RepoTrackIn,
    TrackedRepoOut,
)
from app.services.github_service import GitHubError, GitHubService
from app.services.ingestion_service import ingest_repository

router = APIRouter(prefix="/repos", tags=["repos"])


def _gh(token: str | None) -> GitHubService:
    return GitHubService(token=token)


@router.get("/search", response_model=list[RepoSearchResult])
async def search_repos(
    q: str = Query(min_length=1),
    token: str | None = Depends(github_token),
    _: AuthUser = Depends(current_user),
) -> list[RepoSearchResult]:
    try:
        results = await _gh(token).search_repositories(q)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return [RepoSearchResult(**r) for r in results]


@router.get("", response_model=list[TrackedRepoOut])
def list_tracked(
    db: Session = Depends(db_session), user: AuthUser = Depends(current_user)
) -> list[TrackedRepoOut]:
    repos = db.scalars(
        select(TrackedRepo)
        .where(TrackedRepo.user_id == user.id)
        .order_by(TrackedRepo.created_at.desc())
    ).all()
    return [TrackedRepoOut.model_validate(r) for r in repos]


@router.post("/track", response_model=TrackedRepoOut)
async def track_repo(
    payload: RepoTrackIn,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> TrackedRepoOut:
    existing = db.scalar(
        select(TrackedRepo).where(
            TrackedRepo.user_id == user.id,
            TrackedRepo.owner == payload.owner,
            TrackedRepo.name == payload.name,
        )
    )
    if existing:
        return TrackedRepoOut.model_validate(existing)

    try:
        meta = await _gh(token).get_repo(payload.owner, payload.name)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    repo = TrackedRepo(
        user_id=uuid.UUID(user.id),
        owner=payload.owner,
        name=payload.name,
        default_branch=meta.get("default_branch", "main"),
        description=meta.get("description"),
        primary_language=meta.get("language"),
        stars=meta.get("stargazers_count", 0),
        index_status=IndexStatus.pending,
    )
    db.add(repo)
    db.flush()

    # Passively grow the user's skill for this repo's primary language.
    get_or_create_profile(db, user)
    bump_skill(db, user.id, meta.get("language"), delta=5)

    return TrackedRepoOut.model_validate(repo)


@router.get("/{repo_id}", response_model=TrackedRepoOut)
def get_repo(
    repo_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> TrackedRepoOut:
    repo = get_user_repo(db, user.id, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")
    return TrackedRepoOut.model_validate(repo)


def _run_ingestion(repo_id: uuid.UUID, token: str | None) -> None:
    """Background task: uses its own DB session."""
    import asyncio

    db = SessionLocal()
    try:
        repo = db.get(TrackedRepo, repo_id)
        if repo is not None:
            asyncio.run(ingest_repository(db, repo, token))
    finally:
        db.close()


@router.post("/{repo_id}/index", response_model=IndexStatusOut)
async def index_repo(
    repo_id: uuid.UUID,
    background: BackgroundTasks,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> IndexStatusOut:
    repo = get_user_repo(db, user.id, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")
    repo.index_status = IndexStatus.pending
    db.flush()

    # Prefer the durable Arq/Redis queue; fall back to in-process background task.
    enqueued = await enqueue_ingestion(str(repo.id), token)
    if not enqueued:
        background.add_task(_run_ingestion, repo.id, token)

    return IndexStatusOut(
        repo_id=repo.id,
        index_status=IndexStatus.pending,
        indexed_chunks=0,
        last_indexed_at=repo.last_indexed_at,
    )


@router.get("/{repo_id}/index/status", response_model=IndexStatusOut)
def index_status(
    repo_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> IndexStatusOut:
    repo = get_user_repo(db, user.id, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")
    count = db.scalar(
        select(func.count())
        .select_from(RepoIndexChunk)
        .where(RepoIndexChunk.repo_id == repo.id)
    )
    return IndexStatusOut(
        repo_id=repo.id,
        index_status=repo.index_status,
        indexed_chunks=count or 0,
        last_indexed_at=repo.last_indexed_at,
    )


@router.get("/{repo_id}/structure", response_model=RepoStructureOut)
async def repo_structure(
    repo_id: uuid.UUID,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> RepoStructureOut:
    repo = get_user_repo(db, user.id, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")
    try:
        tree, truncated = await _gh(token).get_tree(
            repo.owner, repo.name, repo.default_branch
        )
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return RepoStructureOut(
        default_branch=repo.default_branch,
        tree=[RepoStructureNode(**n) for n in tree],
        truncated=truncated,
    )


@router.get("/{repo_id}/docs", response_model=RepoDocsOut)
async def repo_docs(
    repo_id: uuid.UUID,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> RepoDocsOut:
    repo = get_user_repo(db, user.id, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")
    try:
        docs = await _gh(token).get_docs(repo.owner, repo.name, repo.default_branch)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return RepoDocsOut(**docs)
