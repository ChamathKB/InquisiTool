.PHONY: help install dev-install clean run test lint format services-start services-stop docker-up docker-down frontend-dev frontend-build widget-build

help:
	@echo "InquisiTool Makefile Commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make clean          - Remove build artifacts and cache"
	@echo "  make run            - Run the application"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code"
	@echo "  make services-start - Start MongoDB, Qdrant, and Redis"
	@echo "  make services-stop  - Stop all services"
	@echo "  make docker-up      - Start with Docker Compose"
	@echo "  make docker-down    - Stop Docker Compose"
	@echo "  make frontend-dev   - Run frontend dev server"
	@echo "  make frontend-build - Build frontend for production"
	@echo "  make widget-build   - Build embeddable survey widget"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

run:
	inquisitool run --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

lint:
	flake8 inquisitool/
	pylint inquisitool/

format:
	black inquisitool/
	isort inquisitool/

services-start:
	@echo "Starting MongoDB..."
	@mongod --fork --logpath /tmp/mongodb.log --dbpath /tmp/mongodb || echo "MongoDB already running or failed to start"
	@echo "Starting Qdrant..."
	@docker run -d --name qdrant -p 6333:6333 qdrant/qdrant 2>/dev/null || echo "Qdrant already running"
	@echo "Starting Redis..."
	@redis-server --daemonize yes || echo "Redis already running"
	@echo "All services started!"

services-stop:
	@echo "Stopping services..."
	@mongod --shutdown 2>/dev/null || true
	@docker stop qdrant 2>/dev/null || true
	@docker rm qdrant 2>/dev/null || true
	@redis-cli shutdown 2>/dev/null || true
	@echo "All services stopped!"

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

widget-build:
	cd widget && npm install && npm run build
