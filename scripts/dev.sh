#!/usr/bin/env bash
# Start the mentor API and the web app together. Ctrl-C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -x "$ROOT/services/agent-api/.venv/bin/uvicorn" ]]; then
  echo "Missing API virtualenv. Run: make install" >&2
  exit 1
fi
if [[ ! -d "$ROOT/apps/web/node_modules" ]]; then
  echo "Missing web dependencies. Run: make install" >&2
  exit 1
fi

cleanup() {
  trap - EXIT INT TERM
  kill 0
}
trap cleanup EXIT INT TERM

cd "$ROOT/services/agent-api"
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &

cd "$ROOT/apps/web"
AGENT_API_URL="${AGENT_API_URL:-http://127.0.0.1:8000}" npm run dev -- --hostname 127.0.0.1 --port 3000 &

wait
