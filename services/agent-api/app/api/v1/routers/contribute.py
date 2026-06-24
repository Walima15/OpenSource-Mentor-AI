"""Contribution assistant endpoints operating on a contribution plan."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.graph import run_intent
from app.agents.llm import LLMNotConfigured
from app.agents.state import AgentState
from app.agents.tools.retriever import retrieve_context
from app.api.deps import current_user, db_session, github_token
from app.core.security import AuthUser
from app.db.crud import get_user_plan
from app.db.models import CodeSuggestion, ContributionPlan, MentorSession, TrackedRepo
from app.schemas.models import (
    AgentTextOut,
    CodeSuggestionOut,
    ContributionPlanOut,
    SuggestCodeIn,
)
from app.services.github_service import GitHubService

router = APIRouter(prefix="/contribute", tags=["contribute"])


def _plan_repo(db: Session, plan: ContributionPlan) -> TrackedRepo:
    session = db.get(MentorSession, plan.session_id)
    repo = db.get(TrackedRepo, session.repo_id) if session else None
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


def _load_plan(db: Session, user: AuthUser, plan_id: uuid.UUID) -> ContributionPlan:
    plan = get_user_plan(db, user.id, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


def _run(state: AgentState) -> AgentState:
    try:
        return run_intent(state)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{plan_id}/recommend-files", response_model=ContributionPlanOut)
def recommend_files(
    plan_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> ContributionPlanOut:
    plan = _load_plan(db, user, plan_id)
    repo = _plan_repo(db, plan)
    state: AgentState = {
        "intent": "recommend_files",
        "repo_full_name": repo.full_name,
        "plan_summary": plan.summary,
        "retrieved_chunks": retrieve_context(str(repo.id), plan.summary),
    }
    result = _run(state)
    files = result.get("structured", {}).get("recommended_files", [])
    if files:
        plan.recommended_files = files
        db.flush()
    return ContributionPlanOut.model_validate(plan)


@router.post("/{plan_id}/suggest-code", response_model=CodeSuggestionOut)
async def suggest_code(
    plan_id: uuid.UUID,
    payload: SuggestCodeIn,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> CodeSuggestionOut:
    plan = _load_plan(db, user, plan_id)
    repo = _plan_repo(db, plan)

    gh = GitHubService(token=token)
    file_content = await gh.get_file_content(
        repo.owner, repo.name, payload.file_path, repo.default_branch
    )

    state: AgentState = {
        "intent": "suggest_code",
        "repo_full_name": repo.full_name,
        "plan_summary": plan.summary,
        "target_file": payload.file_path,
        "instruction": payload.instruction or "",
        "file_content": file_content or "",
        "retrieved_chunks": retrieve_context(
            str(repo.id), f"{payload.file_path} {payload.instruction or ''}"
        ),
    }
    result = _run(state)
    suggestion = CodeSuggestion(
        plan_id=plan.id,
        file_path=payload.file_path,
        diff=result.get("diff", ""),
        explanation=result.get("output", ""),
    )
    db.add(suggestion)
    db.flush()
    return CodeSuggestionOut.model_validate(suggestion)


@router.post("/{plan_id}/suggest-tests", response_model=AgentTextOut)
def suggest_tests(
    plan_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> AgentTextOut:
    plan = _load_plan(db, user, plan_id)
    repo = _plan_repo(db, plan)
    suggestion = db.get(CodeSuggestion, suggestion_id)
    if suggestion is None or suggestion.plan_id != plan.id:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    state: AgentState = {
        "intent": "suggest_tests",
        "repo_full_name": repo.full_name,
        "target_file": suggestion.file_path,
        "diff": suggestion.diff,
        "retrieved_chunks": retrieve_context(str(repo.id), suggestion.file_path),
    }
    result = _run(state)
    suggestion.tests = result.get("output", "")
    db.flush()
    return AgentTextOut(content=result.get("output", ""))


@router.post("/{plan_id}/explain-change", response_model=AgentTextOut)
def explain_change(
    plan_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> AgentTextOut:
    plan = _load_plan(db, user, plan_id)
    suggestion = db.get(CodeSuggestion, suggestion_id)
    if suggestion is None or suggestion.plan_id != plan.id:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    state: AgentState = {"intent": "explain_change", "diff": suggestion.diff}
    result = _run(state)
    return AgentTextOut(content=result.get("output", ""))
