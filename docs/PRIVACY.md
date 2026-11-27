# Privacy

OSMA is a local mentor. This is the threat model for this repository: what stays on the machine in the default setup, and what leaves if you opt into a cloud model or a GitHub token.

This describes OSMA's own requests. It is not a claim about your operating system, browser, Ollama, GitHub, or a cloud model provider.

## No accounts, no telemetry

There are no user accounts and no OSMA-operated service in the default setup. The app does not send analytics. Quiz grading runs in the local API. Conversations are rows in a local SQLite file.

The browser talks only to the Next.js app on your machine. That app proxies `/health` and `/api/v1/*` to the local API (`127.0.0.1`, `localhost`, or the Compose hostname `agent-api`). It is not an open proxy.

## What stays local in guide mode

`OPENAI_API_KEY` is empty by default, so guide mode is the default. Guide mode does not call a language model. Chat text is not sent to Ollama and not sent to a cloud model. Replies are built from the curriculum and project catalog in this repository, plus GitHub tool results when the question needs live issue, file, or pull-request data.

Lessons, quizzes, and setup guides are read from local Python modules (`services/agent-api/app/content/`). Opening a lesson or submitting a quiz does not make a network request.

SQLite stores the conversation id, title, timestamps, role, message text, and a short tool trace (tool name, whether it succeeded, and a summary). It does not store `OPENAI_API_KEY` or `GITHUB_TOKEN`. The default file is `services/agent-api/data/osma.db`. Compose stores it in the `osma-data` volume. There is no account boundary around that file. Keep the API on localhost. See [SECURITY.md](../SECURITY.md).

## Localhost Ollama

The default `OPENAI_BASE_URL` is `http://127.0.0.1:11434/v1` and the default `OPENAI_MODEL` is `llama3.2`. Those values are unused while the key is empty. Guide mode does not connect to the port.

If you set `OPENAI_API_KEY` to any non-empty value and leave the base URL on loopback, OSMA sends the model request to that address. The request contains:

- the system prompt
- the latest user message and up to 12 earlier user and assistant messages
- tool results (curriculum excerpts, project guides, and any GitHub issue, file, or pull-request text the tools returned)
- the key, as an `Authorization: Bearer` header

Ollama does not check the key. OSMA uses a non-empty key only as the switch that leaves guide mode. A placeholder such as a single word is enough. With `make dev`, `127.0.0.1` is your computer, so the HTTP request stays on the machine. OSMA does not add another hop. A stock Ollama process runs the model locally. OSMA cannot see whether that process was configured to call out on its own.

Inside Docker Compose, `127.0.0.1` is the API container, not the host. An empty key still means guide mode, and no model request is made. Plain HTTP to any host other than `localhost`, `127.0.0.1`, or `::1` is rejected. The base URL must not contain a username or password. Redirects from the model endpoint are not followed. The HTTP client does not trust `HTTP_PROXY` from the environment.

## What leaves if you opt into a cloud model

Cloud OpenAI is opt-in. Set `OPENAI_BASE_URL` to an `https` endpoint such as `https://api.openai.com/v1`, set `OPENAI_MODEL` to a cloud model, and set `OPENAI_API_KEY` to a real key. OSMA then sends the same prompt, history, and tool results listed above to that host, with the key in the `Authorization` header.

That content leaves the machine. Retention and training use are the provider's policy, not OSMA's. Unset the key to return to guide mode. The key is read from the environment only. It is not written to SQLite.

## GitHub token and public GitHub lookups

Public GitHub lookups still make outbound requests, including in guide mode and including when the model is local. Asking about an issue, a repository, a file, or a pull request calls `https://api.github.com`. The request carries the owner, repository, path, ref, issue number, or search query needed to answer. It does not carry the whole chat, except where a tool argument was taken from the message (the repository you named, the pull request URL you pasted).

`GITHUB_TOKEN` is optional and env-only. If you set it, OSMA sends it only as an `Authorization` header to `api.github.com`. It is not stored in SQLite and not copied into tool results. It is not given to the model as its own field. Tool results are still included in the model request when a model is on, so do not paste a token into the chat. Without a token, the same GitHub requests are anonymous and still leave the machine. GitHub's anonymous rate limit applies. Redirects are not followed. The GitHub client does not trust `HTTP_PROXY`.

Logs pass through a redaction filter for common token shapes. That filter is a backstop. Do not commit secrets, and do not rely on the filter as the control.

## Other requests that are not chat

`npm install` contacts the npm registry, and `make install` contacts PyPI. `next/font/google` downloads Fraunces and Source Sans 3 at build or dev-compile time and the app then serves those files itself. Those requests do not include chat text, the SQLite database, or your API keys. They happen on a developer machine when dependencies or the web app are built, not when a learner opens a lesson.
