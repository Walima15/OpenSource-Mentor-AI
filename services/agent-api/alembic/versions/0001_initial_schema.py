"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    index_status = sa.Enum(
        "pending", "indexing", "ready", "failed", name="index_status"
    )
    skill_level = sa.Enum(
        "beginner", "intermediate", "advanced", name="skill_level"
    )
    mentor_role = sa.Enum("user", "assistant", "system", "tool", name="mentor_role")
    plan_status = sa.Enum(
        "draft", "in_progress", "completed", "abandoned", name="plan_status"
    )

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("github_username", sa.String(255), index=True),
        sa.Column("github_id", sa.BigInteger()),
        sa.Column("avatar_url", sa.Text()),
        sa.Column("bio", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "user_github_tokens",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(512)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("language", sa.String(64), nullable=False),
        sa.Column("level", skill_level, nullable=False, server_default="beginner"),
        sa.Column("score", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "language", name="uq_skill_user_lang"),
    )

    op.create_table(
        "tracked_repos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("default_branch", sa.String(255), server_default="main"),
        sa.Column("description", sa.Text()),
        sa.Column("stars", sa.Integer(), server_default="0"),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "index_status", index_status, nullable=False, server_default="pending"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "owner", "name", name="uq_repo_user_owner_name"),
    )

    op.create_table(
        "repo_index_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tracked_repos.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("start_line", sa.Integer(), server_default="0"),
        sa.Column("end_line", sa.Integer(), server_default="0"),
        sa.Column("qdrant_point_id", sa.String(64), nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "issues_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tracked_repos.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("github_issue_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("labels", postgresql.JSONB(), server_default="[]"),
        sa.Column("state", sa.String(32), server_default="open"),
        sa.Column("raw", postgresql.JSONB(), server_default="{}"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "repo_id", "github_issue_number", name="uq_issue_repo_number"
        ),
    )

    op.create_table(
        "mentor_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tracked_repos.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("issue_number", sa.Integer()),
        sa.Column("title", sa.Text(), server_default="New session"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "mentor_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mentor_sessions.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("role", mentor_role, nullable=False),
        sa.Column("content", sa.Text(), server_default=""),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "contribution_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mentor_sessions.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("summary", sa.Text(), server_default=""),
        sa.Column("steps", postgresql.JSONB(), server_default="[]"),
        sa.Column("recommended_files", postgresql.JSONB(), server_default="[]"),
        sa.Column("status", plan_status, nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "code_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contribution_plans.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("diff", sa.Text(), server_default=""),
        sa.Column("explanation", sa.Text(), server_default=""),
        sa.Column("tests", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "pull_request_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contribution_plans.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("branch_name", sa.String(255), server_default=""),
        sa.Column("commit_message", sa.Text(), server_default=""),
        sa.Column("title", sa.Text(), server_default=""),
        sa.Column("body", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("pull_request_drafts")
    op.drop_table("code_suggestions")
    op.drop_table("contribution_plans")
    op.drop_table("mentor_messages")
    op.drop_table("mentor_sessions")
    op.drop_table("issues_cache")
    op.drop_table("repo_index_chunks")
    op.drop_table("tracked_repos")
    op.drop_table("skills")
    op.drop_table("user_github_tokens")
    op.drop_table("profiles")
    for enum_name in ("plan_status", "mentor_role", "skill_level", "index_status"):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
