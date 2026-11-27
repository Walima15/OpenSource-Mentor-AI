# Security

## Reporting a vulnerability

Report security issues privately. Do not open a public GitHub issue for a suspected vulnerability, and do not include a secret, a token, or an exploit in a public commit.

Use GitHub private vulnerability reporting:

https://github.com/Walima15/OpenSource-Mentor-AI/security/advisories/new

If that form is unavailable, contact the maintainer, Mwila Alfred Walima, on GitHub as [@Walima15](https://github.com/Walima15) and ask for a private channel before sending details. Include what you found, how to reproduce it, and the impact. Wait for a response before any public disclosure.

## No user accounts

OSMA has no user accounts, passwords, sessions, or roles. The API does not authenticate callers. There is no per-user access boundary inside the application.

## Localhost only

Run the API and the web app on loopback.

- `make dev`, `make api-dev`, and `make web-dev` bind to `127.0.0.1`.
- Docker Compose publishes the web app and the API on `127.0.0.1` only (`127.0.0.1:3000` and `127.0.0.1:8000`). The process inside the API container listens on `0.0.0.0` so Compose can reach it. The published port is still loopback. Do not republish those ports on a public interface.

The database is a local SQLite file. The default URL is `sqlite:///./data/osma.db`, resolved under `services/agent-api` when you use `make dev`. Compose stores the file in the `osma-data` volume at `/data/osma.db`. That file holds conversation titles and message text. Anyone who can read the file, or who can send requests to the API port, can read and write those conversations. Do not put the file on a shared disk, do not expose the port, and do not point `DATABASE_URL` at a remote database.

`OPENAI_API_KEY` and `GITHUB_TOKEN` belong in the environment or in an uncommitted `.env`. The API reads `.env` from the repository root. Do not commit that file. `.env.example` has empty secrets on purpose.

The web app proxies only to `localhost`, `127.0.0.1`, or the Compose hostname `agent-api`, and only to `/health` and `/api/v1/*`. Do not widen that allowlist so the browser can be pointed at an arbitrary host.

What stays on the machine, and what leaves when you opt into a cloud model or a GitHub token, is described in [docs/PRIVACY.md](docs/PRIVACY.md).
