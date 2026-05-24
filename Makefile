.PHONY: help install dev-env run test lint clean

help:
	@echo "credential-gateway"
	@echo ""
	@echo "  make install     Install production dependencies"
	@echo "  make dev-env     Install development dependencies"
	@echo "  make run         Run the dev server"
	@echo "  make test        Run the test suite"
	@echo "  make lint        Run linters"
	@echo "  make migrate     Run database migrations"
	@echo "  make clean       Remove artifacts"

install:
	pip install -r requirements.txt

dev-env:
	pip install -r requirements.txt -r requirements-dev.txt

run:
	uvicorn src.main:app --reload --host $(APP_HOST) --port $(APP_PORT)

test:
	pytest tests/ -v

lint:
	ruff check src/ client_sdk/ tests/

migrate:
	alembic upgrade head

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
