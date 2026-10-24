# Argus Platform — developer shortcuts
.PHONY: help install dev test test-unit test-integration test-eval test-api lint format clean pipeline api docker-build docker-up docker-down

help:
@echo "Argus Platform — available targets:"
@echo "  make install          Install package + dev deps"
@echo "  make dev              Install and start dev server (port 8000)"
@echo "  make test             Run all tests"
@echo "  make test-integration Run integration tests only (cassette-backed)"
@echo "  make test-eval        Run evaluation tests only"
@echo "  make test-api         Run API tests only"
@echo "  make lint             ruff check + mypy"
@echo "  make format           ruff format (write)"
@echo "  make pipeline         Fetch all sources and write data/fused.parquet"
@echo "  make api              Start API server locally"
@echo "  make docker-build     Build API container"
@echo "  make docker-up        Start API via docker compose"
@echo "  make docker-down      Stop containers"
@echo "  make clean            Remove __pycache__, .pytest_cache, build artifacts"

install:
pip install -e ".[dev]"

dev: install
uvicorn argus.api.main:app --reload --port 8000

test:
pytest tests/integration tests/evaluation tests/api -v

test-integration:
pytest tests/integration -v

test-eval:
pytest tests/evaluation -v

test-api:
pytest tests/api -v

lint:
ruff check src tests
mypy src

format:
ruff format src tests
ruff check --fix src tests

pipeline:
argus pipeline --state CA --iso NG

api:
uvicorn argus.api.main:app --reload --port 8000

docker-build:
docker compose build

docker-up:
docker compose up -d

docker-down:
docker compose down

clean:
Get-ChildItem -Recurse -Directory -Include __pycache__,.pytest_cache,.mypy_cache,.ruff_cache -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Include build,dist -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter *.egg-info -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force