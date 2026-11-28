# Changelog

All notable changes to OSMA are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the version number follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Bitcoin Core and LDK can be cloned in the IDE next to BDK and rust-bitcoin. Bitcoin Core uses a shallow blobless sparse checkout of the source, docs, functional tests, and CI files. Guide mode can explain how to contribute to either repository without an API key, including build commands as text, review rules, and where good-first-issue labels live.
- A local IDE at `/workspace` for BDK and rust-bitcoin. OSMA shallow-clones the repository outside its own source tree, with git hooks disabled. The page has a file tree, an editor, the project's contributing notes and review checklist, and the mentor beside the file.
- Workspace tools that read and search the local clone. When a model is configured, it can propose a diff that is applied only if you accept it. Guide mode still explains the open file with no model.
- Documented Ollama code model for that assistant: `qwen2.5-coder:1.5b`.

The IDE does not run a shell, tests, `git commit`, `git push`, or open a pull request.

Nothing else is queued for the v0.1.0 candidate below. The `v0.1.0` git tag and the GitHub Release have not been created.

## [0.1.0] - Unreleased

First public release candidate of the local-first mentor. Prepared on 27 November 2026 from `main`. Do not treat this heading as a published release until the tag exists.

The product in this version starts at commit `58c7fc3` (31 October 2026), which replaced an earlier hosted prototype. That earlier stack is not part of v0.1.0. Details of what shipped are in [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md).

### Added

- FastAPI mentor and Next.js web app for learning to contribute to Bitcoin open-source projects (31 October 2026).
- Guide mode: with an empty `OPENAI_API_KEY`, curriculum, project guides, and GitHub tools still answer, and no language model is called.
- Three English learning paths and quizzes graded by the local API: Bitcoin fundamentals (8 lessons), Lightning (3 lessons), and contribution craft (8 lessons).
- Project guides for Bitcoin Core, libsecp256k1, rust-bitcoin, rust-miniscript, BDK, LDK, LND, Core Lightning, BTCPay Server, and the Lightning BOLTs.
- GitHub tools for public issues, repository files, contribution planning, and pull-request review notes. The mentor does not open pull requests and does not ACK a diff.
- SQLite storage for local conversations only. No accounts and no telemetry.
- Optional OpenAI-compatible chat. Defaults point at local Ollama (`llama3.2`, `http://127.0.0.1:11434/v1`). Cloud OpenAI is opt-in (26 November 2026).
- MIT license, `CONTRIBUTING.md`, `SECURITY.md`, and `docs/PRIVACY.md` (26 November 2026).
- GitHub Actions CI for API `ruff` and `pytest`, and for web lint, test, and production build (27 November 2026).
- One-command local startup with `make start` and one-command Compose with `make up` (27 November 2026).

### Changed

- Next.js and `eslint-config-next` are 16.4.5 (27 November 2026).
- Package versions declared by the repo are `0.1.0`: `apps/web/package.json`, the matching lockfile entries, `services/agent-api/pyproject.toml`, and the FastAPI `version` field. They previously read `1.0.0`, which was ahead of this first release.

### Security

- Web proxy forwards only to `localhost`, `127.0.0.1`, or the Compose hostname `agent-api`.
- Plain HTTP to the model endpoint is limited to loopback. Redirects from GitHub and from the model endpoint are not followed.
- Logs pass through a redaction filter. Secrets stay in the environment and are not written to SQLite.
