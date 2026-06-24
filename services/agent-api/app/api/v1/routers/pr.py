"""Pull request assistant endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.graph import run_intent
from app.agents.llm import LLMNotConfigured
from app.agents.state import AgentState
from app.api.deps import current_user, db_session, github_token
from app.core.security import AuthUser
from app.db.crud import bump_skill, get_user_plan
from app.db.models import (
    CodeSuggestion,
    ContributionPlan,
    MentorSession,
    PullRequestDraft,
    TrackedRepo,
)
from app.schemas.models import (
    AgentTextOut,
    PullRequestCreateIn,
    PullRequestCreateOut,
    PullRequestDraftOut,
)
from app.services.github_service import GitHubError
from app.services.pr_service import create_pull_request_for_plan

router = APIRouter(prefix="/pr", tags=["pull-request"])


def _load_plan(db: Session, user: AuthUser, plan_id: uuid.UUID) -> ContributionPlan:
    plan = get_user_plan(db, user.id, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


def _aggregate_diff(db: Session, plan: ContributionPlan) -> str:
    suggestions = db.scalars(
        select(CodeSuggestion).where(CodeSuggestion.plan_id == plan.id)
    ).all()
    return "\n\n".join(s.diff for s in suggestions if s.diff)


def _repo(db: Session, plan: ContributionPlan) -> TrackedRepo | None:
    session = db.get(MentorSession, plan.session_id)
    return db.get(TrackedRepo, session.repo_id) if session else None


def _run(state: AgentState) -> AgentState:
    try:
        return run_intent(state)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _get_or_create_draft(db: Session, plan_id: uuid.UUID) -> PullRequestDraft:
    draft = db.scalar(
        select(PullRequestDraft).where(PullRequestDraft.plan_id == plan_id)
    )
    if draft is None:
        draft = PullRequestDraft(plan_id=plan_id)
        db.add(draft)
        db.flush()
    return draft


@router.post("/{plan_id}/commit-message", response_model=PullRequestDraftOut)
def commit_message(
    plan_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> PullRequestDraftOut:
    plan = _load_plan(db, user, plan_id)
    state: AgentState = {
        "intent": "commit_message",
        "plan_summary": plan.summary,
        "diff": _aggregate_diff(db, plan),
    }
    result = _run(state)
    draft = _get_or_create_draft(db, plan.id)
    draft.commit_message = result.get("output", "")
    db.flush()
    return PullRequestDraftOut.model_validate(draft)


@router.post("/{plan_id}/description", response_model=PullRequestDraftOut)
def description(
    plan_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> PullRequestDraftOut:
    plan = _load_plan(db, user, plan_id)
    repo = _repo(db, plan)
    session = db.get(MentorSession, plan.session_id)
    issue_title = f"Issue #{session.issue_number}" if session and session.issue_number else ""
    state: AgentState = {
        "intent": "pr_description",
        "repo_full_name": repo.full_name if repo else "",
        "issue_title": issue_title,
        "plan_summary": plan.summary,
        "diff": _aggregate_diff(db, plan),
    }
    result = _run(state)
    draft = _get_or_create_draft(db, plan.id)
    draft.body = result.get("output", "")
    if not draft.title:
        draft.title = plan.summary[:72] if plan.summary else "Contribution"
    if not draft.branch_name:
        draft.branch_name = f"osma/plan-{str(plan.id)[:8]}"
    db.flush()
    return PullRequestDraftOut.model_validate(draft)


@router.post("/{plan_id}/summarize", response_model=AgentTextOut)
def summarize(
    plan_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> AgentTextOut:
    plan = _load_plan(db, user, plan_id)
    state: AgentState = {"intent": "summarize", "diff": _aggregate_diff(db, plan)}
    result = _run(state)
    return AgentTextOut(content=result.get("output", ""))


@router.post("/{plan_id}/create", response_model=PullRequestCreateOut)
async def create_pr(
    plan_id: uuid.UUID,
    payload: PullRequestCreateIn,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> PullRequestCreateOut:
    if not token:
        raise HTTPException(
            status_code=400,
            detail="No GitHub token on file. Sign in with GitHub again to grant repo access.",
        )

    plan = _load_plan(db, user, plan_id)
    repo = _repo(db, plan)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    draft = _get_or_create_draft(db, plan.id)
    title = draft.title or (plan.summary[:72] if plan.summary else "Contribution via OSMA")
    branch = draft.branch_name or f"osma/plan-{str(plan.id)[:8]}"
    body = draft.body or plan.summary or "Contribution drafted with OpenSource Mentor AI."
    commit_message = draft.commit_message or title

    suggestions = db.scalars(
        select(CodeSuggestion).where(CodeSuggestion.plan_id == plan.id)
    ).all()

    try:
        result = await create_pull_request_for_plan(
            token=token,
            upstream_owner=repo.owner,
            upstream_name=repo.name,
            base_branch=repo.default_branch,
            branch_name=branch,
            title=title,
            body=body,
            commit_message=commit_message,
            summary=plan.summary,
            steps=plan.steps or [],
            recommended_files=plan.recommended_files or [],
            suggestions=list(suggestions),
        )
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    # Persist resolved branch back to the draft.
    draft.branch_name = result["branch"]
    # Opening a PR is the strongest contribution signal: grow the language skill.
    bump_skill(db, user.id, repo.primary_language, delta=15)
    db.flush()

    return PullRequestCreateOut(**result)
