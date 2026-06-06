# ==============================================================================
# Project Control Panel
# ==============================================================================
#
# Usage notes:
# - Run `make help` to see the command list.
# - Run backend and frontend in separate terminals: `make dev-be` and `make dev-fe`.
# - Override ports when needed, for example: `make dev-be BACKEND_PORT=8010`.
# - Run `make check` before committing code changes.
# - Run `make db-sql-order` before applying SQL manually in the Supabase UI.
# - Harness commands operate on the local gitignored `harness.db` file.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Default local development addresses. Override on the command line when a port is busy.
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 8501
WEB_PORT ?= 5173

# Optional arguments for focused tests and Harness traces.
# Example: make test-one PYTEST_ARGS='backend/tests/test_api_auth.py -q'
PYTEST_ARGS ?= backend/tests
TRACE_SUMMARY ?= "manual trace"
TRACE_OUTCOME ?= "completed"

# Repo-local Harness CLI. Use this instead of a globally installed command.
HARNESS := scripts/bin/harness-cli

.PHONY: \
	help \
	env install sync lock \
	dev dev-be dev-fe \
	dev-web build-web typecheck-web \
	test test-be test-one \
	format check ruff mypy precommit validate \
	ingest \
	db-sql-order db-migrations db-seeds \
	harness-init harness-migrate harness-matrix harness-backlog harness-stats harness-friction harness-trace \
	clean

# Print available commands. This is the safest starting point for humans and agents.
help:
	@printf "\nProject commands\n"
	@printf "  make env              Copy .env.example to .env if .env is missing\n"
	@printf "  make install          Sync uv workspace and install pre-commit hooks\n"
	@printf "  make sync             Sync all uv workspace packages\n"
	@printf "  make lock             Refresh uv.lock\n"
	@printf "\nDevelopment\n"
	@printf "  make dev-be           Run FastAPI backend on $(BACKEND_HOST):$(BACKEND_PORT)\n"
	@printf "  make dev-fe           Run Streamlit frontend on port $(FRONTEND_PORT)\n"
	@printf "  make dev-web          Run React frontend on port $(WEB_PORT)\n"
	@printf "  make build-web        Build React frontend\n"
	@printf "  make dev              Print commands for running backend and frontend\n"
	@printf "  make ingest           Run backend ingestion CLI\n"
	@printf "\nValidation\n"
	@printf "  make test             Run backend pytest suite\n"
	@printf "  make test-one PYTEST_ARGS='backend/tests/test_api_auth.py -q'\n"
	@printf "  make format           Format and auto-fix imports with Ruff\n"
	@printf "  make check            Run Ruff, Mypy, and backend tests\n"
	@printf "  make precommit        Run all pre-commit hooks\n"
	@printf "  make validate         Run check and precommit\n"
	@printf "\nDatabase SQL\n"
	@printf "  make db-sql-order     Show Supabase SQL apply order\n"
	@printf "  make db-migrations    List Supabase migration files\n"
	@printf "  make db-seeds         List Supabase seed files\n"
	@printf "\nHarness\n"
	@printf "  make harness-init     Create local harness.db if missing\n"
	@printf "  make harness-matrix   Show Harness proof matrix\n"
	@printf "  make harness-backlog  Show Harness backlog\n"
	@printf "  make harness-trace TRACE_SUMMARY='...' TRACE_OUTCOME='...'\n"
	@printf "\nMaintenance\n"
	@printf "  make clean            Remove Python/tool cache directories\n\n"

# Create a local .env from the committed template only if .env does not exist.
env:
	@test -f .env || cp .env.example .env

# Full local setup after clone: install dependencies and enable pre-commit hooks.
install: sync
	uv run pre-commit install

# Sync all uv workspace packages from uv.lock.
sync:
	uv sync --all-packages

# Refresh uv.lock after dependency changes.
lock:
	uv lock

# Reminder target because backend and frontend should run in separate terminals.
dev:
	@printf "Run these in separate terminals:\n"
	@printf "  make dev-be\n"
	@printf "  make dev-fe\n"

# Run FastAPI with hot reload. Override host/port with BACKEND_HOST/BACKEND_PORT.
dev-be:
	cd backend && uv run uvicorn app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload

# Run the current Streamlit frontend. Override port with FRONTEND_PORT.
dev-fe:
	cd frontend && uv run streamlit run main.py --server.port $(FRONTEND_PORT)

# Run the React frontend that will replace Streamlit.
dev-web:
	cd web && npm run dev -- --port $(WEB_PORT)

typecheck-web:
	cd web && npm run typecheck

build-web:
	cd web && npm run build

# Run the backend ingestion CLI for clinical knowledge documents.
ingest:
	cd backend && uv run python -m app.ingestion.cli

# Alias for the default backend test suite.
test: test-be

# Run all backend tests.
test-be:
	uv run pytest backend/tests

# Run a focused pytest command.
# Example: make test-one PYTEST_ARGS='backend/tests/test_api_roles.py -q'
test-one:
	uv run pytest $(PYTEST_ARGS)

# Format Python code and auto-fix Ruff lint/import issues.
format:
	uv run ruff format .
	uv run ruff check . --fix

# Check formatting and linting without modifying files.
ruff:
	uv run ruff format --check .
	uv run ruff check .

# Run strict static type checking.
mypy:
	uv run mypy .

# Main pre-commit validation: format check, lint, type check, and tests.
check: ruff mypy test-be

# Run every configured pre-commit hook across the repo.
precommit:
	uv run pre-commit run --all-files

# Strongest local validation target before pushing important changes.
validate: check build-web precommit

# Show the exact SQL apply order for Supabase SQL Editor.
# Seeds are sorted together with migrations by filename timestamp.
db-sql-order:
	@printf "Apply in this order in Supabase SQL editor:\n"
	@find supabase/migrations supabase/seeds -maxdepth 1 -type f -name '*.sql' -printf '%f %p\n' | sort | cut -d' ' -f2-

# List schema/data migration files only.
db-migrations:
	@find supabase/migrations -maxdepth 1 -type f -name '*.sql' | sort

# List seed files only.
db-seeds:
	@find supabase/seeds -maxdepth 1 -type f -name '*.sql' | sort

# Create the local Harness SQLite database when it does not exist.
harness-init:
	$(HARNESS) init

# Apply Harness schema migrations to the local harness.db.
harness-migrate:
	$(HARNESS) migrate

# Show story proof status from Harness durable records.
harness-matrix:
	$(HARNESS) query matrix

# Show Harness backlog items.
harness-backlog:
	$(HARNESS) query backlog

# Show Harness operational stats.
harness-stats:
	$(HARNESS) query stats

# Show recorded Harness friction, useful after repeated workflow problems.
harness-friction:
	$(HARNESS) query friction

# Record a minimal Harness trace.
# Example: make harness-trace TRACE_SUMMARY='"Updated Makefile"' TRACE_OUTCOME=completed
harness-trace:
	$(HARNESS) trace --summary $(TRACE_SUMMARY) --outcome $(TRACE_OUTCOME)

# Remove local Python/tool caches. Does not remove .venv or project data.
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
