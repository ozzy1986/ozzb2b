.PHONY: help install test test-api test-web test-chat test-events test-matcher test-scraper lint typecheck coverage docker-build clean

help:
	@echo "Common targets:"
	@echo "  make install        - install dev dependencies for every service"
	@echo "  make test           - run every test suite with coverage"
	@echo "  make test-api       - pytest for apps/api"
	@echo "  make test-web       - vitest for apps/web"
	@echo "  make test-chat      - go test for apps/chat"
	@echo "  make test-events    - go test for apps/events"
	@echo "  make test-matcher   - cargo test for apps/matcher"
	@echo "  make test-scraper   - pytest for apps/scraper"
	@echo "  make lint           - run all linters"
	@echo "  make typecheck      - mypy + tsc + clippy"
	@echo "  make coverage       - run everything with coverage enabled"

install:
	cd apps/api && pip install -e ".[dev]"
	cd apps/scraper && pip install -e ".[dev]"
	cd apps/web && npm install --legacy-peer-deps
	cd apps/chat && go mod download
	cd apps/events && go mod download
	cd apps/matcher && cargo fetch

test: test-api test-scraper test-web test-chat test-events test-matcher

test-api:
	cd apps/api && pytest

test-web:
	cd apps/web && npm run test

test-chat:
	cd apps/chat && go test -race ./...

test-events:
	cd apps/events && go test -race ./...

test-matcher:
	cd apps/matcher && cargo test --all-targets

test-scraper:
	cd apps/scraper && pytest

lint:
	cd apps/api && ruff check . && mypy src
	cd apps/scraper && ruff check .
	cd apps/web && npm run typecheck
	cd apps/chat && go vet ./...
	cd apps/events && go vet ./...
	cd apps/matcher && cargo fmt --check && cargo clippy --all-targets -- -D warnings

typecheck:
	cd apps/api && mypy src
	cd apps/web && npm run typecheck

coverage:
	cd apps/api && pytest
	cd apps/scraper && pytest
	cd apps/web && npm run test:coverage
	bash scripts/check_go_coverage.sh apps/chat 55
	bash scripts/check_go_coverage.sh apps/events 55
	cd apps/matcher && cargo test --all-targets

docker-build:
	docker build -f apps/api/Dockerfile -t ozzb2b-api:dev apps/api
	docker build -f apps/web/Dockerfile -t ozzb2b-web:dev apps/web
	docker build -f apps/chat/Dockerfile -t ozzb2b-chat:dev apps/chat
	docker build -f apps/events/Dockerfile -t ozzb2b-events:dev apps/events
	docker build -f apps/matcher/Dockerfile -t ozzb2b-matcher:dev .
	docker build -f apps/scraper/Dockerfile -t ozzb2b-scraper:dev apps/scraper

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + || true
	find . -type d -name .mypy_cache -prune -exec rm -rf {} + || true
	find . -type d -name .ruff_cache -prune -exec rm -rf {} + || true
	find . -type f -name coverage.xml -delete || true
	find . -type f -name coverage.out -delete || true
