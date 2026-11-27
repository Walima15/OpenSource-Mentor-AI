# OSMA local tasks. Run `make help`.

.PHONY: help install api-install web-install dev api-dev web-dev test lint build up down

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: api-install web-install ## Install Python and Node dependencies

api-install: ## Create the API virtualenv and install dependencies
	python3 -m venv services/agent-api/.venv
	services/agent-api/.venv/bin/pip install -r services/agent-api/requirements.txt -r services/agent-api/requirements-dev.txt

web-install: ## Install the web app dependencies
	cd apps/web && npm install

dev: ## Run the API and the web app (http://127.0.0.1:3000)
	bash scripts/dev.sh

api-dev: ## Run only the FastAPI mentor
	cd services/agent-api && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web-dev: ## Run only the Next.js app
	cd apps/web && AGENT_API_URL=$${AGENT_API_URL:-http://127.0.0.1:8000} npm run dev -- --hostname 127.0.0.1 --port 3000

test: ## Run API and web tests
	cd services/agent-api && .venv/bin/pytest -q
	cd apps/web && npm test

lint: ## Lint the API and the web app
	cd services/agent-api && .venv/bin/ruff check app tests
	cd apps/web && npm run lint

build: ## Production-build the web app
	cd apps/web && npm run build

up: ## Build and start the Docker Compose stack
	docker compose up --build

down: ## Stop the Docker Compose stack
	docker compose down
