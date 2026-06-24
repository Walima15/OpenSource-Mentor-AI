# OSMA Agent API (FastAPI + LangGraph)

The backend service for OpenSource Mentor AI. It exposes a REST API, hosts the
LangGraph agent system, ingests repositories into Qdrant, and talks to Anthropic
Claude.

## Structure

```
app/
  main.py                # App factory, CORS, routers, lifespan
  worker.py              # Arq background worker (durable ingestion)
  core/                  # config, logging, security (JWT + token encryption), queue
  db/                    # SQLAlchemy base, models, session, crud
  schemas/               # Pydantic request/response models
  services/              # github, embeddings, vector store, ingestion, pr_service
  agents/
    graph.py             # LangGraph orchestrator (intent router)
    state.py             # Shared AgentState
    llm.py               # Anthropic wrapper
    nodes/               # mentor, contribution, pr, chat nodes
    tools/               # Qdrant retriever
    prompts/             # Prompt templates
  api/
    deps.py              # Shared dependencies (auth, db, github token)
    v1/routers/          # health, profile, repos, issues, mentor, contribute, pr
alembic/                 # Migrations
```

## Develop

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Auth

Every protected endpoint expects a Supabase session JWT as a Bearer token. The
token is validated with `SUPABASE_JWT_SECRET` (HS256) and the `sub` claim is the
user id. GitHub provider tokens are encrypted at rest with Fernet
(`TOKEN_ENCRYPTION_KEY`).

## Agents

`run_intent(state)` routes the request by `state["intent"]` to the matching
node. Each node is a pure function (`AgentState -> partial AgentState`) and can
be tested in isolation.
