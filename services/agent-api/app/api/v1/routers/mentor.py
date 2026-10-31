"""Mentor agent endpoints: sessions, repo/issue explanation, planning, chat."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.agents.graph import run_intent
from app.agents.llm import LLMNotConfigured, get_llm
from app.agents.state import AgentState
from app.agents.tools.retriever import retrieve_context
from app.api.deps import current_user, db_session, github_token
from app.core.rate_limit import limit_mentor
from app.core.security import AuthUser
from app.db.crud import get_user_repo, get_user_session
from app.db.models import (
    ContributionPlan,
    MentorMessage,
    MentorRole,
    MentorSession,
    TrackedRepo,
)
from app.schemas.models import (
    AgentTextOut,
    ChatIn,
    ContributionPlanOut,
    MentorMessageOut,
    MentorSessionCreate,
    MentorSessionOut,
)
from app.services.github_service import GitHubService

router = APIRouter(prefix="/mentor", tags=["mentor"])


async def _base_state(
    db: Session,
    repo: TrackedRepo,
    session: MentorSession,
    token: str | None,
    query: str,
) -> AgentState:
    """Assemble shared agent state for a repo/session, including retrieval."""
    state: AgentState = {
        "repo_full_name": repo.full_name,
        "repo_description": repo.description or "",
        "retrieved_chunks": retrieve_context(str(repo.id), query),
    }
    if session.issue_number:
        gh = GitHubService(token=token)
        try:
            issue = await gh.get_issue(repo.owner, repo.name, session.issue_number)
            state["issue_title"] = issue["title"]
            state["issue_body"] = issue["body"] or ""
        except Exception:  # noqa: BLE001
            pass
    return state


def _persist(db: Session, session_id: uuid.UUID, role: MentorRole, content: str) -> None:
    db.add(MentorMessage(session_id=session_id, role=role, content=content))


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
@router.post("/sessions", response_model=MentorSessionOut)
def create_session(
    payload: MentorSessionCreate,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> MentorSessionOut:
    repo = get_user_repo(db, user.id, payload.repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not tracked")
    title = payload.title or (
        f"Issue #{payload.issue_number}" if payload.issue_number else repo.full_name
    )
    session = MentorSession(
        user_id=uuid.UUID(user.id),
        repo_id=payload.repo_id,
        issue_number=payload.issue_number,
        title=title,
    )
    db.add(session)
    db.flush()
    return MentorSessionOut.model_validate(session)


@router.get("/sessions", response_model=list[MentorSessionOut])
def list_sessions(
    db: Session = Depends(db_session), user: AuthUser = Depends(current_user)
) -> list[MentorSessionOut]:
    sessions = db.scalars(
        select(MentorSession)
        .where(MentorSession.user_id == user.id)
        .order_by(MentorSession.created_at.desc())
    ).all()
    return [MentorSessionOut.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=list[MentorMessageOut])
def get_session_messages(
    session_id: uuid.UUID,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> list[MentorMessageOut]:
    session = get_user_session(db, user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = db.scalars(
        select(MentorMessage)
        .where(MentorMessage.session_id == session_id)
        .order_by(MentorMessage.created_at.asc())
    ).all()
    return [MentorMessageOut.model_validate(m) for m in messages]


# ---------------------------------------------------------------------------
# Agent actions
# ---------------------------------------------------------------------------
async def _run_session_intent(
    db: Session,
    user: AuthUser,
    session_id: uuid.UUID,
    intent: str,
    token: str | None,
    query: str,
) -> AgentState:
    session = get_user_session(db, user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    repo = db.get(TrackedRepo, session.repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    state = await _base_state(db, repo, session, token, query)
    state["intent"] = intent  # type: ignore[typeddict-item]
    try:
        return run_intent(state)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/sessions/{session_id}/explain-repo",
    response_model=AgentTextOut,
    dependencies=[Depends(limit_mentor)],
)
async def explain_repo(
    session_id: uuid.UUID,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> AgentTextOut:
    result = await _run_session_intent(
        db, user, session_id, "explain_repo", token, "project architecture overview"
    )
    _persist(db, session_id, MentorRole.assistant, result.get("output", ""))
    return AgentTextOut(content=result.get("output", ""))


@router.post(
    "/sessions/{session_id}/explain-issue",
    response_model=AgentTextOut,
    dependencies=[Depends(limit_mentor)],
)
async def explain_issue(
    session_id: uuid.UUID,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> AgentTextOut:
    result = await _run_session_intent(
        db, user, session_id, "explain_issue", token, "issue context"
    )
    _persist(db, session_id, MentorRole.assistant, result.get("output", ""))
    return AgentTextOut(content=result.get("output", ""))


@router.post(
    "/sessions/{session_id}/plan",
    response_model=ContributionPlanOut,
    dependencies=[Depends(limit_mentor)],
)
async def create_plan(
    session_id: uuid.UUID,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
) -> ContributionPlanOut:
    result = await _run_session_intent(
        db, user, session_id, "plan", token, "implementation plan"
    )
    structured = result.get("structured", {})
    plan = ContributionPlan(
        session_id=session_id,
        summary=structured.get("summary", result.get("output", "")),
        steps=structured.get("steps", []),
        recommended_files=structured.get("recommended_files", []),
    )
    db.add(plan)
    db.flush()
    return ContributionPlanOut.model_validate(plan)


@router.post("/sessions/{session_id}/chat", dependencies=[Depends(limit_mentor)])
async def chat(
    session_id: uuid.UUID,
    payload: ChatIn,
    db: Session = Depends(db_session),
    token: str | None = Depends(github_token),
    user: AuthUser = Depends(current_user),
):
    """Stream a mentor response over Server-Sent Events."""
    session = get_user_session(db, user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    repo = db.get(TrackedRepo, session.repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Load short history and persist the user's message.
    history = [
        {"role": m.role.value, "content": m.content}
        for m in db.scalars(
            select(MentorMessage)
            .where(MentorMessage.session_id == session_id)
            .order_by(MentorMessage.created_at.asc())
        ).all()
    ]
    _persist(db, session_id, MentorRole.user, payload.message)
    db.commit()

    state = await _base_state(db, repo, session, token, payload.message)

    from app.agents import prompts

    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.CHAT.format(
        repo_full_name=state.get("repo_full_name", ""),
        history="\n".join(f"{h['role']}: {h['content']}" for h in history[-10:])
        or "(no prior messages)",
        context=context,
        user_message=payload.message,
    )

    async def event_generator():
        chunks: list[str] = []
        try:
            for delta in get_llm().stream(prompts.SYSTEM_BASE, prompt, max_tokens=1800):
                chunks.append(delta)
                yield {"event": "delta", "data": delta}
        except LLMNotConfigured as exc:
            yield {"event": "error", "data": str(exc)}
            return
        full = "".join(chunks)
        # Persist the assistant message in a fresh session (generator outlives request).
        from app.db.session import SessionLocal

        write_db = SessionLocal()
        try:
            write_db.add(
                MentorMessage(
                    session_id=session_id,
                    role=MentorRole.assistant,
                    content=full,
                )
            )
            write_db.commit()
        finally:
            write_db.close()
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())
