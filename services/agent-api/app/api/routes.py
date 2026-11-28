"""HTTP API for the mentor, the curriculum, and the project catalog."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.agent.prompts import workspace_prompt
from app.content.loader import LESSONS, PATHS, PROJECTS, lessons_for_path, public_lesson
from app.core.rate_limit import client_ip
from app.core.security import ToolError, validate_git_path
from app.db.models import Conversation, Message
from app.tools.curriculum import grade_quiz
from app.tools.github_tools import find_good_first_issues
from app.tools.projects import get_project_guide, list_projects
from app.workspace.context import reset_workspace_id, set_workspace_id
from app.workspace.store import get_workspace

router = APIRouter()
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def get_db(request: Request):
    session: Session = request.app.state.Session()
    try:
        yield session
    finally:
        session.close()


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=8_000)
    conversation_id: str | None = None
    workspace_id: str | None = None
    open_path: str | None = None

    @field_validator("message")
    @classmethod
    def _message(cls, value: str) -> str:
        cleaned = value.replace("\x00", "").strip()
        if not cleaned:
            raise ValueError("message is empty")
        return cleaned

    @field_validator("conversation_id", "workspace_id")
    @classmethod
    def _uuid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _UUID.fullmatch(value):
            raise ValueError("id must be a UUID")
        return value

    @field_validator("open_path")
    @classmethod
    def _open_path(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        try:
            return validate_git_path(value)
        except ToolError as exc:
            raise ValueError(exc.message) from None


class QuizRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[int] = Field(min_length=1, max_length=20)


@router.get("/health")
def health(request: Request) -> dict:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "llm_configured": bool(settings.llm_configured),
        "github_token_configured": bool(settings.github_token),
        "model": settings.openai_model if settings.llm_configured else None,
    }


@router.get("/api/v1/curriculum/paths")
def curriculum_paths(request: Request) -> dict:
    _limit_read(request)
    return list_paths_payload()


@router.get("/api/v1/curriculum/paths/{path_id}")
def curriculum_path(path_id: str, request: Request) -> dict:
    _limit_read(request)
    _check_slug(path_id)
    path = next((item for item in PATHS if item.id == path_id), None)
    if path is None:
        raise HTTPException(status_code=404, detail="Learning path not found")
    lessons = lessons_for_path(path.id)
    return {
        **path.model_dump(),
        "lessons": [
            {"id": lesson.id, "title": lesson.title, "summary": lesson.summary, "order": lesson.order}
            for lesson in lessons
        ],
    }


@router.get("/api/v1/curriculum/lessons/{lesson_id}")
def curriculum_lesson(lesson_id: str, request: Request) -> dict:
    _limit_read(request)
    lesson = _lesson_or_404(lesson_id)
    return public_lesson(lesson)


@router.post("/api/v1/curriculum/lessons/{lesson_id}/quiz")
def curriculum_quiz(lesson_id: str, body: QuizRequest, request: Request) -> dict:
    _limit_read(request)
    _lesson_or_404(lesson_id)
    try:
        return grade_quiz({"lesson_id": lesson_id, "answers": body.answers})
    except Exception as exc:
        message = getattr(exc, "message", None) or "Could not grade that quiz"
        raise HTTPException(status_code=422, detail=message) from None


@router.get("/api/v1/projects")
def projects(request: Request) -> dict:
    _limit_read(request)
    return list_projects({})


@router.get("/api/v1/projects/{slug}")
def project_detail(slug: str, request: Request) -> dict:
    _limit_read(request)
    _check_slug(slug)
    if slug not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    return get_project_guide({"project": slug})


@router.get("/api/v1/projects/{slug}/issues")
def project_issues(slug: str, request: Request, limit: int = 5) -> dict:
    _limit_read(request)
    _check_slug(slug)
    if slug not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    if limit < 1 or limit > 10:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 10")
    try:
        return find_good_first_issues(request.app.state.github, {"project": slug, "limit": limit})
    except Exception as exc:
        message = getattr(exc, "message", None) or "Could not load issues"
        raise HTTPException(status_code=502, detail=message) from None


@router.get("/api/v1/conversations")
def list_conversations(request: Request, db: Session = Depends(get_db)) -> dict:
    _limit_read(request)
    rows = db.scalars(select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)).all()
    return {"conversations": [_conversation_out(row) for row in rows]}


@router.get("/api/v1/conversations/{conversation_id}")
def get_conversation(conversation_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    _limit_read(request)
    _check_uuid(conversation_id)
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.scalars(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.position)
    ).all()
    return {
        "conversation": _conversation_out(conversation),
        "messages": [_message_out(message) for message in messages],
    }


@router.delete("/api/v1/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, request: Request, db: Session = Depends(get_db)) -> None:
    _limit_read(request)
    _check_uuid(conversation_id)
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.execute(delete(Message).where(Message.conversation_id == conversation_id))
    db.delete(conversation)
    db.commit()


@router.post("/api/v1/chat")
def chat(body: ChatRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    request.app.state.chat_limiter.check(f"chat:{client_ip(request)}")
    now = datetime.now(UTC)
    if body.conversation_id:
        conversation = db.get(Conversation, body.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            id=str(uuid4()),
            title=_title(body.message),
            created_at=now,
            updated_at=now,
        )
        db.add(conversation)
        db.flush()
    existing = db.scalars(
        select(Message.position)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.position.desc())
    ).first()
    next_position = 0 if existing is None else existing + 1
    history = [
        {"role": message.role, "content": message.content}
        for message in db.scalars(
            select(Message).where(Message.conversation_id == conversation.id).order_by(Message.position)
        ).all()
        if message.role in {"user", "assistant"}
    ]
    db.add(
        Message(
            id=str(uuid4()),
            conversation_id=conversation.id,
            position=next_position,
            role="user",
            content=body.message,
            tool_trace="[]",
            created_at=now,
        )
    )
    prompt = None
    if body.workspace_id:
        try:
            prompt = workspace_prompt(get_workspace(body.workspace_id))
        except ToolError as exc:
            db.rollback()
            status_code = 404 if exc.message == "Unknown workspace" else 400
            raise HTTPException(status_code=status_code, detail=exc.message) from None
    elif body.open_path:
        db.rollback()
        raise HTTPException(status_code=400, detail="open_path requires a workspace")
    token = set_workspace_id(body.workspace_id)
    try:
        reply = request.app.state.agent.reply(
            history,
            body.message,
            system_prompt=prompt,
            open_path=body.open_path,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="The mentor could not answer that message") from None
    finally:
        reset_workspace_id(token)
    assistant = Message(
        id=str(uuid4()),
        conversation_id=conversation.id,
        position=next_position + 1,
        role="assistant",
        content=reply.content,
        tool_trace=json.dumps(reply.traces),
        created_at=datetime.now(UTC),
    )
    db.add(assistant)
    conversation.updated_at = assistant.created_at
    db.commit()
    db.refresh(assistant)
    return {
        "conversation_id": conversation.id,
        "mode": reply.mode,
        "message": _message_out(assistant),
    }


def list_paths_payload() -> dict:
    paths = []
    for path in sorted(PATHS, key=lambda item: item.order):
        lessons = lessons_for_path(path.id)
        paths.append(
            {
                **path.model_dump(),
                "lessons": [
                    {"id": lesson.id, "title": lesson.title, "summary": lesson.summary}
                    for lesson in lessons
                ],
            }
        )
    return {"paths": paths}


def _lesson_or_404(lesson_id: str):
    if not _SLUG.fullmatch(lesson_id):
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson = LESSONS.get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


def _check_slug(value: str) -> None:
    if not _SLUG.fullmatch(value):
        raise HTTPException(status_code=404, detail="Not found")


def _check_uuid(value: str) -> None:
    if not _UUID.fullmatch(value):
        raise HTTPException(status_code=404, detail="Conversation not found")


def _limit_read(request: Request) -> None:
    request.app.state.read_limiter.check(f"read:{client_ip(request)}")


def _title(message: str) -> str:
    cleaned = re.sub(r"[\s]+", " ", message).strip()
    cleaned = re.sub(r"[\x00-\x1f]", "", cleaned)
    return (cleaned[:80] or "New session")


def _conversation_out(conversation: Conversation) -> dict:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": _iso(conversation.created_at),
        "updated_at": _iso(conversation.updated_at),
    }


def _message_out(message: Message) -> dict:
    try:
        trace = json.loads(message.tool_trace or "[]")
    except json.JSONDecodeError:
        trace = []
    if not isinstance(trace, list):
        trace = []
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "tool_trace": trace,
        "created_at": _iso(message.created_at),
    }


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()
