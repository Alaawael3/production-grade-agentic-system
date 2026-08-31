SHELL := /bin/bash

ENV ?= development


# ============================================================
# Dependencies
# ============================================================

install-dev:
	@echo "Installing development dependencies..."
	@uv pip install -e ".[dev]"


install-prod:
	@echo "Installing production dependencies..."
	@uv pip install --no-cache -e .


# ============================================================
# Docker
# ============================================================

docker-up:
	@echo "Starting docker containers..."
	@docker compose -f docker/docker-compose.yml up -d --build


docker-down:
	@echo "Stopping docker containers..."
	@docker compose -f docker/docker-compose.yml down


# ============================================================
# Cleanup
# ============================================================

clean:
	@echo "Cleaning up..."

	@rm -rf __pycache__ .pytest_cache dist build .venv *.egg-info

	@find . -type d -name "__pycache__" -exec rm -rf {} +

	@find . -type d -name ".pytest_cache" -exec rm -rf {} +

	@find . -type f -name "*.pyc" -delete


# ============================================================
# Help
# ============================================================

help:
	@echo "Usage: make <target> [ENV=development|staging|production|test]"
	@echo ""
	@echo "Targets:"
	@echo "  install-dev   Install development dependencies"
	@echo "  install-prod  Install production dependencies"
	@echo "  docker-up     Build and start docker containers"
	@echo "  docker-down   Stop docker containers"
	@echo "  clean         Clean temporary files and caches"
	@echo "  help          Show this help message"


# ============================================================
# RUN APP
# ============================================================
dev:
	@echo "Starting server in $(ENV) environment"
	@powershell -Command "$$env:APP_ENV='$(ENV)'; uv run uvicorn main:app --reload --port 8000"