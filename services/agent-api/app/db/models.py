"""SQLAlchemy ORM models.

Application tables live in the `public` schema and reference the Supabase
`auth.users` id via the user id (uuid). We intentionally do not declare a hard
foreign key to `auth.users` so the models also work against a plain Postgres
instance in fully-local mode.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid, utcnow


class IndexStatus(str, enum.Enum):
    pending = "pending"
    indexing = "indexing"
    ready = "ready"
    failed = "failed"


class SkillLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class MentorRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class PlanStatus(str, enum.Enum):
    draft = "draft"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    # Equals the Supabase auth user id.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    github_username: Mapped[str | None] = mapped_column(String(255), index=True)
    github_id: Mapped[int | None] = mapped_column(BigInteger)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(Text)

    skills: Mapped[list[Skill]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class UserGitHubToken(Base, TimestampMixin):
    __tablename__ = "user_github_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str | None] = mapped_column(String(512))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("user_id", "language", name="uq_skill_user_lang"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel, name="skill_level"), default=SkillLevel.beginner
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        onupdate=utcnow,
    )

    profile: Mapped[Profile] = relationship(back_populates="skills")


class TrackedRepo(Base, TimestampMixin):
    __tablename__ = "tracked_repos"
    __table_args__ = (
        UniqueConstraint("user_id", "owner", "name", name="uq_repo_user_owner_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    description: Mapped[str | None] = mapped_column(Text)
    primary_language: Mapped[str | None] = mapped_column(String(64))
    stars: Mapped[int] = mapped_column(Integer, default=0)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    index_status: Mapped[IndexStatus] = mapped_column(
        Enum(IndexStatus, name="index_status"), default=IndexStatus.pending
    )

    chunks: Mapped[list[RepoIndexChunk]] = relationship(
        back_populates="repo", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


class RepoIndexChunk(Base):
    __tablename__ = "repo_index_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    repo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_repos.id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, default=0)
    end_line: Mapped[int] = mapped_column(Integer, default=0)
    qdrant_point_id: Mapped[str] = mapped_column(String(64), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    repo: Mapped[TrackedRepo] = relationship(back_populates="chunks")


class IssueCache(Base):
    __tablename__ = "issues_cache"
    __table_args__ = (
        UniqueConstraint("repo_id", "github_issue_number", name="uq_issue_repo_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    repo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_repos.id", ondelete="CASCADE"), index=True
    )
    github_issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    labels: Mapped[list] = mapped_column(JSONB, default=list)
    state: Mapped[str] = mapped_column(String(32), default="open")
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


class MentorSession(Base, TimestampMixin):
    __tablename__ = "mentor_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    repo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_repos.id", ondelete="CASCADE"), index=True
    )
    issue_number: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text, default="New session")

    messages: Mapped[list[MentorMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    plans: Mapped[list[ContributionPlan]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class MentorMessage(Base):
    __tablename__ = "mentor_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mentor_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MentorRole] = mapped_column(Enum(MentorRole, name="mentor_role"))
    content: Mapped[str] = mapped_column(Text, default="")
    meta: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    session: Mapped[MentorSession] = relationship(back_populates="messages")


class ContributionPlan(Base, TimestampMixin):
    __tablename__ = "contribution_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mentor_sessions.id", ondelete="CASCADE"), index=True
    )
    summary: Mapped[str] = mapped_column(Text, default="")
    steps: Mapped[list] = mapped_column(JSONB, default=list)
    recommended_files: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status"), default=PlanStatus.draft
    )

    session: Mapped[MentorSession] = relationship(back_populates="plans")
    suggestions: Mapped[list[CodeSuggestion]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    pr_drafts: Mapped[list[PullRequestDraft]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class CodeSuggestion(Base):
    __tablename__ = "code_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contribution_plans.id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    diff: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    tests: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    plan: Mapped[ContributionPlan] = relationship(back_populates="suggestions")


class PullRequestDraft(Base):
    __tablename__ = "pull_request_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contribution_plans.id", ondelete="CASCADE"), index=True
    )
    branch_name: Mapped[str] = mapped_column(String(255), default="")
    commit_message: Mapped[str] = mapped_column(Text, default="")
    title: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    plan: Mapped[ContributionPlan] = relationship(back_populates="pr_drafts")
