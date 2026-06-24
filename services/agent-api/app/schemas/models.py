"""Pydantic request/response schemas exposed by the API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import IndexStatus, MentorRole, PlanStatus, SkillLevel


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Profile / skills
# ---------------------------------------------------------------------------
class ProfileOut(ORMModel):
    id: uuid.UUID
    github_username: str | None
    github_id: int | None
    avatar_url: str | None
    bio: str | None
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    bio: str | None = None
    avatar_url: str | None = None


class SkillOut(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    language: str
    level: SkillLevel
    score: int
    updated_at: datetime


class SkillUpsert(BaseModel):
    language: str = Field(min_length=1, max_length=64)
    level: SkillLevel = SkillLevel.beginner
    score: int = Field(default=0, ge=0, le=100)


# ---------------------------------------------------------------------------
# Repos
# ---------------------------------------------------------------------------
class RepoSearchResult(BaseModel):
    owner: str
    name: str
    full_name: str
    description: str | None
    stars: int
    language: str | None
    url: str


class RepoTrackIn(BaseModel):
    owner: str
    name: str


class TrackedRepoOut(ORMModel):
    id: uuid.UUID
    owner: str
    name: str
    default_branch: str
    description: str | None
    primary_language: str | None = None
    stars: int
    last_indexed_at: datetime | None
    index_status: IndexStatus


class IndexStatusOut(BaseModel):
    repo_id: uuid.UUID
    index_status: IndexStatus
    indexed_chunks: int
    last_indexed_at: datetime | None


class RepoStructureNode(BaseModel):
    path: str
    type: str  # "file" | "dir"
    size: int | None = None


class RepoStructureOut(BaseModel):
    default_branch: str
    tree: list[RepoStructureNode]
    truncated: bool = False


class RepoDocsOut(BaseModel):
    readme: str | None
    contributing: str | None


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------
class IssueOut(BaseModel):
    number: int
    title: str
    body: str | None
    labels: list[str]
    state: str
    url: str
    comments: int
    created_at: str


# ---------------------------------------------------------------------------
# Mentor sessions / messages
# ---------------------------------------------------------------------------
class MentorSessionCreate(BaseModel):
    repo_id: uuid.UUID
    issue_number: int | None = None
    title: str | None = None


class MentorSessionOut(ORMModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    issue_number: int | None
    title: str
    created_at: datetime


class MentorMessageOut(ORMModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: MentorRole
    content: str
    metadata: dict = Field(
        default_factory=dict,
        validation_alias="meta",
        serialization_alias="metadata",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChatIn(BaseModel):
    message: str = Field(min_length=1)


class AgentTextOut(BaseModel):
    content: str


# ---------------------------------------------------------------------------
# Plans / suggestions / PR
# ---------------------------------------------------------------------------
class PlanStep(BaseModel):
    model_config = ConfigDict(extra="ignore")
    order: int = 0
    title: str = ""
    detail: str = ""


class RecommendedFile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    path: str = ""
    reason: str = ""


class ContributionPlanOut(ORMModel):
    id: uuid.UUID
    session_id: uuid.UUID
    summary: str
    steps: list[PlanStep]
    recommended_files: list[RecommendedFile]
    status: PlanStatus
    created_at: datetime


class CodeSuggestionOut(ORMModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    file_path: str
    diff: str
    explanation: str
    tests: str | None
    created_at: datetime


class SuggestCodeIn(BaseModel):
    file_path: str
    instruction: str | None = None


class PullRequestDraftOut(ORMModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    branch_name: str
    commit_message: str
    title: str
    body: str
    created_at: datetime


class GitHubTokenIn(BaseModel):
    """Used by the web app to persist the GitHub provider token after login."""

    access_token: str
    scope: str | None = None


class PullRequestCreateIn(BaseModel):
    draft: bool = False


class PullRequestCreateOut(BaseModel):
    url: str
    number: int
    branch: str
    head: str
    applied_files: list[str]
    skipped_files: list[str]
    note: str | None = None
