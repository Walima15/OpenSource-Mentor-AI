"""row level security policies

Enables RLS on user-owned tables and adds policies that scope every row to the
authenticated Supabase user (``auth.uid()``). This is defense-in-depth: the
FastAPI service connects with a privileged role and also scopes by user id, but
RLS protects any direct access through the Supabase client/PostgREST.

For fully-local Postgres (no Supabase ``auth`` schema), a no-op ``auth.uid()``
returning NULL is created so the migration applies cleanly.

Revision ID: 0002_rls
Revises: 0001_initial
Create Date: 2026-06-24

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002_rls"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Tables scoped directly by a user id column.
DIRECT = {
    "profiles": "id = auth.uid()",
    "user_github_tokens": "user_id = auth.uid()",
    "skills": "user_id = auth.uid()",
    "tracked_repos": "user_id = auth.uid()",
    "mentor_sessions": "user_id = auth.uid()",
}

# Tables scoped through a parent relationship.
INDIRECT = {
    "repo_index_chunks": (
        "repo_id IN (SELECT id FROM public.tracked_repos WHERE user_id = auth.uid())"
    ),
    "issues_cache": (
        "repo_id IN (SELECT id FROM public.tracked_repos WHERE user_id = auth.uid())"
    ),
    "mentor_messages": (
        "session_id IN (SELECT id FROM public.mentor_sessions WHERE user_id = auth.uid())"
    ),
    "contribution_plans": (
        "session_id IN (SELECT id FROM public.mentor_sessions WHERE user_id = auth.uid())"
    ),
    "code_suggestions": (
        "plan_id IN (SELECT cp.id FROM public.contribution_plans cp "
        "JOIN public.mentor_sessions ms ON cp.session_id = ms.id "
        "WHERE ms.user_id = auth.uid())"
    ),
    "pull_request_drafts": (
        "plan_id IN (SELECT cp.id FROM public.contribution_plans cp "
        "JOIN public.mentor_sessions ms ON cp.session_id = ms.id "
        "WHERE ms.user_id = auth.uid())"
    ),
}

ALL_TABLES = {**DIRECT, **INDIRECT}


def upgrade() -> None:
    # Local-dev fallback so auth.uid() always resolves.
    op.execute("CREATE SCHEMA IF NOT EXISTS auth;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'auth' AND p.proname = 'uid'
            ) THEN
                CREATE FUNCTION auth.uid() RETURNS uuid
                LANGUAGE sql STABLE AS $func$ SELECT NULL::uuid $func$;
            END IF;
        END $$;
        """
    )

    # NOTE: we intentionally do NOT FORCE row level security. The FastAPI
    # service connects as the table owner / a superuser (Supabase `postgres`),
    # which bypasses RLS so server-side access keeps working while it scopes by
    # user id in code. RLS still protects the anon/authenticated roles used by
    # the Supabase client / PostgREST.
    for table, predicate in ALL_TABLES.items():
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY {table}_owner_select ON public.{table} "
            f"FOR SELECT USING ({predicate});"
        )
        op.execute(
            f"CREATE POLICY {table}_owner_modify ON public.{table} "
            f"FOR ALL USING ({predicate}) WITH CHECK ({predicate});"
        )


def downgrade() -> None:
    for table in ALL_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_owner_modify ON public.{table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_owner_select ON public.{table};")
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;")
