# ==============================================================================
# PROJECT CONTROL PANEL (MAKEFILE)
# Note: Indentations MUST be Tabs.
# ==============================================================================

.PHONY: help install dev-be dev-fe format check clean ingest

# Display list of supported commands
help:
	@echo "Environment & Setup:"
	@echo "  make install    - Install and sync all workspace dependencies (uv sync)"
	@echo "  make clean      - Remove cache directories and temporary files"
	@echo ""
	@echo "Development & Execution:"
	@echo "  make dev-be     - Run Backend server (FastAPI) with hot-reload"
	@echo "  make dev-fe     - Run Frontend server (Streamlit)"
	@echo "  make ingest     - Run the data ingestion pipeline"
	@echo ""
	@echo "Code Quality (Run before commit):"
	@echo "  make format     - Auto-format code and sort imports using Ruff"
	@echo "  make check      - Run linting (Ruff) and type checking (Mypy)"

# Install and sync all packages in the workspace
install:
	uv sync --all-packages

# Run Backend
dev-be:
	cd backend && uv run uvicorn app.main:app --reload

# Run Frontend (Updated to main.py to match your recent rename)
dev-fe:
	cd frontend && uv run streamlit run main.py

# Run Data Ingestion
ingest:
	cd backend && uv run python -m app.ingestion.cli

# Auto-format code
format:
	uv run ruff check . --fix
	uv run ruff format .
	uv run pre-commit run --all-files

# Check code quality
check:
	uv run ruff check .
	uv run mypy .

# Clean up junk/cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
