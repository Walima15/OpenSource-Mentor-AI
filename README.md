# OpenSource Mentor AI (OSMA)

An AI-powered web application that guides developers through contributing to
open-source projects: issue discovery, repository understanding, code
contribution, testing, and pull request creation.

OSMA pairs a modern Next.js dashboard with a Python FastAPI backend that hosts a
modular [LangGraph](https://langchain-ai.github.io/langgraph/) agent system. It
uses Supabase (Postgres + GitHub OAuth), the GitHub API, Anthropic Claude, and a
Qdrant vector database for retrieval-augmented reasoning over a repository's
codebase.

---

## Table of contents

- [Architecture](#architecture)
- [Monorepo layout](#monorepo-layout)
- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Environment configuration](#environment-configuration)
- [Supabase + GitHub OAuth setup](#supabase--github-oauth-setup)
- [Running with Docker](#running-with-docker-compose)
- [Running locally](#running-locally-without-docker)
- [Development roadmap](#development-roadmap)

---

## Architecture

Two services in a single monorepo communicating over HTTP.

```
                 +---------------------------+
   Developer --> |   Next.js 15 (apps/web)   |
                 |  - Dashboard UI           |
                 |  - Supabase GitHub OAuth  |
                 |  - GitHub REST proxy      |
                 +-------------+-------------+
                               | Supabase JWT (Bearer)
                               v
                 +---------------------------+
                 | FastAPI (services/agent-  |
                 |          api)             |
                 |  - REST API               |
                 |  - LangGraph agents       |
                 |  - Repo ingestion         |
                 +----+--------+--------+-----+
                      |        |        |
                      v        v        v
                 Postgres   Qdrant   Anthropic
                (Supabase) (vectors)  (Claude)
                      ^
                      |
                   GitHub API
```

- **Auth**: Next.js uses Supabase Auth with the GitHub provider. The Supabase
  session JWT is forwarded to FastAPI as a Bearer token. FastAPI validates it and
  loads/creates the user profile. The GitHub provider token is stored encrypted
  for server-side API calls on the user's behalf.
- **Agents**: A LangGraph state graph routes requests by intent
  (explain repo, explain issue, plan, recommend files, suggest code, suggest
  tests, write PR). Each capability is an independently testable node.
- **Retrieval**: Repositories are chunked, embedded, and upserted to Qdrant so
  agents can ground their answers in the actual codebase.
- **Opportunity matching**: Tracked repositories are scanned for
  beginner-friendly issues (`good first issue`, `help wanted`, bugs) which are
  mirrored into an issue cache and ranked against the contributor's per-language
  skills, producing an explainable, scored list of recommended issues. Scanning
  runs on demand from the dashboard and, when `REDIS_URL` is set, continuously
  via an hourly Arq cron in the worker.
- **Pull requests**: OSMA can open a real PR on GitHub. It forks the upstream
  repo (when needed), creates a branch, applies the AI code suggestions, and
  opens the pull request against the base branch.
- **Durable ingestion**: When `REDIS_URL` is set, repo indexing runs on a
  separate Arq worker so jobs survive web-process restarts. Without it, indexing
  falls back to in-process background tasks.
- **Security**: Postgres Row Level Security policies scope every user-owned row
  to the authenticated Supabase user (defense-in-depth alongside API scoping).

## Monorepo layout

```
osma/
  apps/
    web/             # Next.js 15 (App Router, TS, Tailwind)
  services/
    agent-api/       # FastAPI + LangGraph + Qdrant + Anthropic
                     #   app/worker.py -> Arq background worker
  packages/
    shared-types/    # Shared TypeScript types
  infra/
    postgres/        # Local Postgres init
    qdrant/          # Qdrant config
  docker-compose.yml # web, agent-api, worker, postgres, qdrant, redis
  .env.example
  Makefile
```

See each service's directory for more detail.

## Tech stack

| Layer            | Technology                                  |
| ---------------- | ------------------------------------------- |
| Frontend         | Next.js 15, TypeScript, Tailwind CSS        |
| Auth             | Supabase Auth (GitHub OAuth)                |
| Backend          | FastAPI (Python 3.11+)                       |
| Agent framework  | LangGraph                                   |
| LLM              | Anthropic Claude (swappable via env)        |
| Database         | PostgreSQL (Supabase)                       |
| Vector DB        | Qdrant                                      |
| Embeddings       | fastembed (local, configurable)             |
| Source control   | GitHub API                                  |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose, OR
- Node.js 20+ and Python 3.11+ for local development
- A [Supabase](https://supabase.com/) project
- A GitHub OAuth app
- An [Anthropic API key](https://console.anthropic.com/)

## Environment configuration

Copy the example file and fill in the values:

```bash
cp .env.example .env
```

Every variable is documented in [.env.example](.env.example). At minimum you need
Supabase keys, an Anthropic API key, and a GitHub OAuth client id/secret.

## Supabase + GitHub OAuth setup

1. Create a Supabase project. Note the **Project URL**, **anon key**, and
   **service role key** (Project Settings -> API).
2. Find your **JWT secret** (Project Settings -> API -> JWT Settings) and set
   `SUPABASE_JWT_SECRET`.
3. Create a GitHub OAuth app (GitHub -> Settings -> Developer settings ->
   OAuth Apps):
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL:
     `https://<your-project-ref>.supabase.co/auth/v1/callback`
4. In Supabase (Authentication -> Providers -> GitHub), enable GitHub and paste
   the client id/secret. Request the `repo read:user` scopes so the agent can
   read repositories and open pull requests.
5. Add `http://localhost:3000/auth/callback` to Supabase's allowed redirect URLs
   (Authentication -> URL Configuration).
6. Run the database migrations (see below) to create the application tables.

## Running with Docker Compose

```bash
cp .env.example .env   # then fill in values
make up                # or: docker compose up --build
```

Services:

- Web: http://localhost:3000
- API: http://localhost:8000 (docs at http://localhost:8000/docs)
- Worker: Arq background worker (no exposed port)
- Qdrant: http://localhost:6333
- Redis: localhost:6379 (durable job queue)
- Postgres: localhost:5432 (only used for fully-local mode)

Apply migrations once the API container is up:

```bash
make migrate
```

Run the backend test suite (no local Python needed):

```bash
make api-test-docker
```

If host port 3000 is already in use, set an alternate web port in `.env`:

```bash
WEB_PORT=3002   # then: docker compose up -d web  -> http://localhost:3002
```

## Running locally (without Docker)

Backend:

```bash
cd services/agent-api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Optional durable worker (requires Redis + `REDIS_URL`):

```bash
cd services/agent-api
arq app.worker.WorkerSettings        # or: make worker
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

## Development roadmap

1. Monorepo scaffold, env, Docker compose, health checks. (done)
2. Backend core: FastAPI app, config, Supabase JWT auth, SQLAlchemy + Alembic.
3. Frontend core: Next.js, Tailwind, Supabase auth, dashboard shell, API client.
4. GitHub integration: repo search/track, structure/docs, issue discovery.
5. Repo ingestion + Qdrant embeddings + index status UI.
6. Agent system: LangGraph graph, repo/issue/plan nodes, mentor SSE flow.
7. Contribution assistant: file/code/test suggestion nodes + DiffViewer.
8. PR assistant: commit/PR/summary nodes + PR draft UI.
9. Profile + skill tracking, polish, responsive pass, seed data.
10. Hardening: error handling, rate-limit handling, tests, final docs.

## License

MIT
