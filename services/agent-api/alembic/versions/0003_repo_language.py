"""add primary_language to tracked_repos

Revision ID: 0003_repo_language
Revises: 0002_rls
Create Date: 2026-06-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_repo_language"
down_revision: str | None = "0002_rls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tracked_repos",
        sa.Column("primary_language", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tracked_repos", "primary_language")
