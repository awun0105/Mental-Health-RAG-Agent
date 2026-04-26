.PHONY: help install dev-be dev-fe format check clean ingest

# Display list of supported commands when typing just `make` or `make help`
help:
	@echo "Supported commands:"
	@echo "  make install    - Install/Sync all dependencies for the Workspace (uv sync)"
	@echo "  make dev-be     - Run the Backend server (FastAPI) with hot-reload"
	@echo "  make dev-fe     - Run the Frontend server (Streamlit)"
	@echo "  make format     - Auto-format code using Ruff"
	@echo "  make check      - Run code quality checks (Ruff Linting + Mypy Type checking)"
	@echo "  make clean      - Remove cache directories and temporary files"
	@echo "  make ingest     - Run the data ingestion pipeline"
# Install dependencies
install:
	uv sync

# Run Backend (Default port is usually 8000)
dev-be:
	cd backend && uv run uvicorn app.main:app --reload

# Run Frontend (Default port is usually 8501)
dev-fe:
	cd frontend && uv run streamlit run main.py
# Run ingestion pipeline
ingest:
	cd backend && uv run python -m app.ingestion.cli
# Clean and format code
format:
	uv run ruff check . --fix
	uv run ruff format .

# Check code quality (Ruff + Mypy)
check:
	uv run ruff check .
	uv run mypy .

# Clean up junk/cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
