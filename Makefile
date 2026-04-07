# Personal Agent - Makefile
.PHONY: help install backend frontend dev test lint clean docker-build docker-up docker-down

# Default target
help:
	@echo "Personal Agent - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start both backend and frontend (requires tmux or separate terminals)"
	@echo "  make backend      - Start backend server only"
	@echo "  make frontend     - Start frontend dev server only"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests only"
	@echo ""
	@echo "Linting:"
	@echo "  make lint         - Run all linters"
	@echo "  make lint-backend - Run backend linters only"
	@echo "  make lint-frontend- Run frontend linters only"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Clean up generated files"
	@echo "  make format       - Format all code"

# Installation
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Development
backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting development servers..."
	@echo "Please run 'make backend' and 'make frontend' in separate terminals"

# Testing
test: test-backend

test-backend:
	cd backend && pytest -v

test-frontend:
	cd frontend && npm test

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd backend && ruff check app tests
	cd backend && ruff format --check app tests
	cd backend && mypy app || true

lint-frontend:
	cd frontend && npm run lint || true

# Formatting
format: format-backend format-frontend

format-backend:
	cd backend && ruff format app tests

format-frontend:
	cd frontend && npm run format

# Docker
docker-build:
	docker-compose -f docker/docker-compose.yml build

docker-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-dev-up:
	docker-compose -f docker/docker-compose.dev.yml up -d

docker-dev-down:
	docker-compose -f docker/docker-compose.dev.yml down

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	rm -f backend/.coverage 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true

# Database migrations
db-init:
	cd backend && alembic init alembic

db-migrate:
	cd backend && alembic revision --autogenerate -m "$(message)"

db-upgrade:
	cd backend && alembic upgrade head

db-downgrade:
	cd backend && alembic downgrade -1
