# OSMA

OSMA (Open Source Mentor AI) is a local mentor for people who want to contribute to Bitcoin open-source projects. It teaches the protocol and the review culture, then helps you set up a repository, find a first issue, plan a change, and review a pull request.

It does not open pull requests for you, and it will not ACK code you have not read.

## What you can ask

- Explain a concept: UTXOs, transactions, scripts, blocks, consensus, the peer-to-peer network, the mempool, BIPs, Lightning, ACK/NACK, signed commits, mailing lists, IRC.
- Walk a learning path. Each lesson has a quiz. Answers stay hidden until you submit.
- Show a setup guide for Bitcoin Core, libsecp256k1, rust-bitcoin, rust-miniscript, BDK, LDK, LND, Core Lightning, BTCPay Server, or the Lightning BOLTs.
- Fetch open good-first-issue style tickets from GitHub.
- Explain a repository or a file.
- Plan a contribution from a goal or an issue number.
- Review a pull request URL or a diff, using project review conventions. OSMA will not say ACK for you.

With `OPENAI_API_KEY` set, a tool-calling model writes the reply. Without a key, **guide mode** still calls the same tools and assembles the answer from the curriculum and GitHub. That is enough to learn and to try the app.

## Architecture

```
Browser
  └─ Next.js (apps/web)          chat, curriculum, project pages
       └─ same-origin proxy      only /health and /api/v1/* 
            └─ FastAPI (services/agent-api)
                 ├─ mentor loop  OpenAI-compatible /chat/completions
                 ├─ tools        curriculum, projects, GitHub, review
                 └─ SQLite       conversations only
```

The GitHub token and the LLM key stay in the environment. They are sent as headers to `api.github.com` and to `OPENAI_BASE_URL`. They are not stored in SQLite, not written into tool results, and there is no job queue that could hold them. Logs pass through a redaction filter.

The web proxy only forwards to `localhost`, `127.0.0.1`, or the Compose hostname `agent-api`. Redirects from GitHub and from the LLM endpoint are not followed.

## Run locally without Docker

Requirements: Python 3.11+, Node.js 22, and git.

```bash
cp .env.example .env
# Optional: put a real key in OPENAI_API_KEY and a token in GITHUB_TOKEN.

make install
make dev
```

- Web: http://127.0.0.1:3000
- API: http://127.0.0.1:8000 (interactive docs at http://127.0.0.1:8000/docs)

`make dev` starts both processes. Ctrl-C stops them. You can also run `make api-dev` and `make web-dev` in two terminals.

The API reads `.env` from the repository root. An empty `OPENAI_API_KEY` is valid: chat uses guide mode.

Check the install:

```bash
make lint
make test
make build
```

## Run with Docker

Requirements: Docker with Compose v2.

```bash
cp .env.example .env
# Optional: fill in OPENAI_API_KEY and GITHUB_TOKEN.
make up
```

`make up` is `docker compose up --build`. The site is http://127.0.0.1:3000 and the API is http://127.0.0.1:8000. Ports are bound to loopback. SQLite lives in the `osma-data` volume.

```bash
make down
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Bearer token for the chat API. Empty enables guide mode. |
| `OPENAI_BASE_URL` | OpenAI-compatible base, default `https://api.openai.com/v1`. `http://` is allowed only for localhost (for example Ollama on `http://127.0.0.1:11434/v1`). |
| `OPENAI_MODEL` | Model name sent as `model`. Default `gpt-4o-mini`. |
| `GITHUB_TOKEN` | Optional. Public read is enough. Without it, GitHub's anonymous rate limit applies. |
| `DATABASE_URL` | Default SQLite file `sqlite:///./data/osma.db` under `services/agent-api`. |
| `AGENT_API_URL` | Where the Next.js server proxies. Default `http://127.0.0.1:8000`. |

There is one env example file: `.env.example`. Do not commit `.env`.

## Tests

API tests live in `services/agent-api/tests`. They cover the curriculum, project guides, GitHub tools (with a fake client and a mock HTTP transport), the tool-calling loop, guide mode, validation, and the chat rate limit. The LLM is scripted in tests, so no key is required.

The web package tests the proxy allowlist (`npm test` in `apps/web`).

## Limitations

- No accounts. Anyone who can open the port can read the conversations in that SQLite file. Keep it on localhost.
- Guide mode routes by phrases and then calls tools. It is not a free-form tutor. Set an API key for that.
- OSMA does not fork repositories, push commits, or open pull requests.
- Setup steps are a map, not a mirror of upstream docs. When they disagree, follow the repository.
- Good-first-issue search depends on the labels projects actually use. Bitcoin Core often has few of them. Reviewing an existing pull request is the better first contribution, and the mentor says so.
- Rate limits are in-memory and per process.
- The web proxy will not forward to an arbitrary host. Local and Compose hostnames only.

## License

MIT
