# Contributing to OSMA

OSMA is a local-first mentor for Bitcoin open-source contribution. Changes should keep that shape: guide mode works with no API key, a local model is the first conversational option, and the mentor never acts on GitHub as the user.

## The mentor does not act for the user

OSMA does not open pull requests, push commits, fork repositories, or post review comments. It does not ACK or NACK code. An ACK means a person reviewed that commit. Do not add a tool, prompt, or UI path that files a pull request or speaks an ACK on the user's behalf. Contribution help stops at teaching, planning, and review notes the user can apply themselves.

## Local setup

Requirements: Python 3.11+, Node.js 22, and git. Docker is optional. Ollama is optional and only needed if you want a conversational model.

```bash
cp .env.example .env
make install
make dev
```

- Web: http://127.0.0.1:3000
- API: http://127.0.0.1:8000 (interactive docs at http://127.0.0.1:8000/docs)

`make dev` starts both processes and binds them to loopback. Ctrl-C stops them. `make api-dev` and `make web-dev` run one process each.

Leave `OPENAI_API_KEY` empty. Chat stays in guide mode, which is the default and does not call a model. To try a local model, install [Ollama](https://ollama.com), run `ollama pull llama3.2`, and set `OPENAI_API_KEY` to any non-empty placeholder. The defaults already point at `http://127.0.0.1:11434/v1` and `llama3.2`. Ollama does not check that key. OSMA uses a non-empty key only as the switch that leaves guide mode.

Cloud OpenAI is opt-in. Set `OPENAI_BASE_URL=https://api.openai.com/v1`, set `OPENAI_MODEL` to a cloud model such as `gpt-4o-mini`, and set `OPENAI_API_KEY` to a real key. Do not commit `.env`.

`make dev` runs the API on the host, so `127.0.0.1:11434` is Ollama on the same machine. Inside Docker Compose, `127.0.0.1` is the API container. Compose still defaults to guide mode while the key is empty. Use `make dev` when you want the container-free path to a host Ollama.

`GITHUB_TOKEN` is optional. Public read access is enough. Without it, GitHub's anonymous rate limit applies.

## Tests and linters

```bash
make lint
make test
make build
```

That runs:

- API lint: `ruff check app tests` in `services/agent-api`
- API tests: `pytest` in `services/agent-api` (no network, no API key)
- Web lint: `npm run lint` in `apps/web`
- Web tests: `npm test` in `apps/web` (proxy allowlist)
- Web production build: `npm run build` in `apps/web`

Install first with `make install` so `services/agent-api/.venv` and `apps/web/node_modules` exist. To run one suite:

```bash
cd services/agent-api && .venv/bin/pytest -q
cd services/agent-api && .venv/bin/ruff check app tests
cd apps/web && npm test
cd apps/web && npm run lint
```

The API tests script the language model and stub GitHub. Do not point tests at a live key or a live token.

## Curriculum changes

Lessons live in Python modules and are checked at import:

| Path id | File |
| --- | --- |
| `bitcoin-fundamentals` | `services/agent-api/app/content/fundamentals.py` |
| `lightning` | `services/agent-api/app/content/lightning.py` |
| `contribution-craft` | `services/agent-api/app/content/contribute.py` |

Path titles and order are `PATHS` in `services/agent-api/app/content/loader.py`. A new path needs an entry there and at least one lesson whose `path_id` matches.

Each lesson needs a stable `id`, `path_id`, `title`, `order` (unique within the path), `summary`, `concepts`, `keywords`, `sources`, `body`, and a `quiz` of one or more questions. Source URLs must be `https`. Quiz `answer` is the index of the correct choice. Explanations and answer indexes are not sent to the browser before grading. Teach from primary sources (BIPs, the project docs, the code) and say so in `sources`. Do not present OSMA's notes as a specification.

`services/agent-api/tests/test_curriculum.py` checks that every path has lessons, orders are unique, and quiz answers are in range. Extend it when you add a path or a lesson people will look up by a new phrase.

## Project catalog changes

The catalog is `PROJECTS` in `services/agent-api/app/content/projects.py`. One dict per project. Required fields are enforced by the `Project` model in `loader.py`: `slug`, `name`, `owner`, `repo`, `language`, `difficulty`, `summary`, `tags`, `aliases`, `issue_labels`, `docs`, `prerequisites`, `setup_steps`, `test_steps`, `contributing`, `code_map`, and `review_notes`.

Setup steps are a map, not a copy of upstream docs. Point `docs` at the repository and the current build instructions, and tell the reader to follow those when they disagree with OSMA. Doc URLs must be `https`, except the existing Miniscript reference URL allowed in `loader.py`.

Review checklists live in `services/agent-api/app/content/review_guides.py`. Add a `PROJECT_CHECKLIST` entry keyed by the project slug when the project has review rules worth stating. Keep the rule that the user reviews the commit themselves.

`services/agent-api/tests/test_projects.py` covers the catalog. Update it when you add a project that should stay in the default set, and run `pytest` so the model validation runs.

## Proposing a change

Open an issue or a pull request that describes the lesson or project, the sources you used, and what a newcomer should be able to do afterward. Small corrections to a setup step or a quiz explanation are welcome as a focused pull request.

A proposal should not include API keys, GitHub tokens, or a `.env` file. Read [SECURITY.md](SECURITY.md) before reporting a vulnerability, and [docs/PRIVACY.md](docs/PRIVACY.md) before changing anything that sends chat text, tokens, or repository contents off the machine.
