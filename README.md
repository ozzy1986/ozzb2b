# ozzb2b — B2B services marketplace

[![ci](https://github.com/ozzy1986/ozzb2b/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/ozzy1986/ozzb2b/actions/workflows/ci.yml)

Aggregator and marketplace of B2B service providers (IT outsourcing, accounting,
legal, marketing, HR) focused on the RU market. Public catalog, faceted search,
real-time chat between buyers and providers, a "claim your company" flow, and
product analytics — delivered as a small polyglot stack on a single VPS.

The project doubles as a learning playground; each service is deliberately
written in a different language to showcase idiomatic patterns (typed contracts,
async I/O, gRPC, pub/sub, streams, observability).

---

## Feature overview

- **Catalog of companies** with categories, countries, cities, legal forms, and a
  "last scraped" freshness badge.
- **Search** over the catalog: Meilisearch (typo-tolerant) + optional Rust
  re-ranker for business-aware scoring; Postgres FTS as fallback.
- **Authentication** with JWT access tokens (short-lived) and opaque
  refresh tokens (HTTP-only cookies, rotated, hashed at rest). Argon2id for
  password hashing. RBAC: `admin`, `provider_owner`, `client`.
- **Real-time chat** between clients and provider owners via WebSocket, backed
  by Redis pub/sub. Message persistence in Postgres.
- **"Claim your company" flow** with meta-tag verification on the company's
  homepage, admin moderation queue, and owner-scoped profile editing.
- **Product analytics**: API publishes events to Redis Streams, a Go consumer
  drains them into ClickHouse; admin dashboard shows top searches / top
  providers / event counts.
- **Scraper**: polite async crawlers (`robots.txt`, rate limits, anti-bot
  detection) scheduled by Celery Beat. Host-based de-duplication on ingestion.
- **Full observability**: Prometheus metrics in every service, Grafana
  dashboards (service overview + host/container), Loki for logs, Alertmanager
  with Telegram notifications for critical alerts.

---

## Architecture at a glance

```
                                     Internet
                                        │
                            (HTTPS, Let's Encrypt)
                                        │
                                  ┌─────▼──────┐
                                  │   nginx    │
                                  │ (reverse   │
                                  │  proxy)    │
                                  └─┬───┬───┬──┘
                                    │   │   │
         ┌──────────────────────────┘   │   └────────────────────────┐
         │                              │                            │
    ozzb2b.com                    api.ozzb2b.com                 grafana.ozzb2b.com
         │                              │                            │
 ┌───────▼────────┐       ┌─────────────▼───────────────┐    ┌───────▼───────┐
 │  web (Next.js  │       │         API (FastAPI)       │    │    Grafana    │
 │  15, SSR, RSC) │──────►│   /auth /providers /chat    │    │  (dashboards) │
 │  port 3101     │  REST │   /search /admin /claims    │    │  port 3102    │
 └────────────────┘       └──┬─────┬─────┬─────┬────┬───┘    └───────┬───────┘
                             │     │     │     │    │                │
                 ┌───────────┘     │     │     │    │       ┌────────┴────────┐
                 │                 │     │     │    │       │  Prometheus +   │
                 │                 │     │     │    │       │  Loki + Alert-  │
                 ▼                 ▼     ▼     ▼    ▼       │  manager (TG)   │
          ┌────────────┐   ┌────────────┐ ┌──────┐ ┌─────┐  └─────────────────┘
          │ PostgreSQL │   │   Redis    │ │Meili │ │gRPC │
          │  (catalog, │   │ (cache,    │ │search│ │  ▲  │
          │   users,   │   │  rate-lim, │ │      │ │  │  │
          │   chat,    │   │  pub/sub,  │ │      │ │  │  │
          │   claims)  │   │  streams)  │ │      │ │  │  │
          └────────────┘   └──┬──┬──┬───┘ └──────┘ │  │  │
                              │  │  │              │  │  │
           pub/sub ◄──────────┘  │  └──► stream    │  │  │
                                 │                 │  │  │
                       ┌─────────▼────────┐        │  │  │
                       │   Chat (Go)      │        │  │  │
                       │   WebSocket      │        │  │  │
                       │   gateway 8090   │        │  │  │
                       └──────────────────┘        │  │  │
                                                   │  │  │
                       ┌─────────────────┐         │  │  │
                       │  Events (Go)    │◄────────┘  │  │
                       │  XREADGROUP →   │  stream     │  │
                       │  ClickHouse     │            │  │
                       └────────┬────────┘            │  │
                                │                     │  │
                       ┌────────▼────────┐            │  │
                       │   ClickHouse    │            │  │
                       │  (analytics)    │            │  │
                       └─────────────────┘            │  │
                                                      │  │
                       ┌──────────────────┐           │  │
                       │  Matcher (Rust)  │◄──────────┘  │
                       │  gRPC re-ranker  │              │
                       │  port 9090       │              │
                       └──────────────────┘              │
                                                         │
                       ┌──────────────────┐              │
                       │  Scraper worker  │              │
                       │  (Python+Celery) │──────────────┘
                       │  Beat scheduler  │  writes to Postgres
                       └──────────────────┘  reindexes Meilisearch
```

Request flow example — **browsing providers**:

1. Browser → `ozzb2b.com` (nginx → Next.js SSR).
2. Next.js server renders the page and calls `api.ozzb2b.com/providers?...`.
3. API queries Postgres, returns JSON with facets.
4. API emits `provider_viewed` / `search_performed` events to Redis Stream.
5. Go consumer drains events → ClickHouse.
6. Admin dashboard later reads aggregations from ClickHouse.

Request flow example — **sending a chat message**:

1. Client authenticates on the API (JWT cookie).
2. API issues a short-lived WS token for a specific conversation.
3. Browser opens WebSocket to `api.ozzb2b.com/chat/ws?token=...`
   (nginx proxies to the Go `chat` service).
4. Sending a message: browser POSTs to the API → message is stored in
   Postgres and published on Redis pub/sub.
5. Chat gateway subscribers push the message to both participants over WS.

---

## Tech stack

| Concern | Technology |
|---|---|
| Frontend | Next.js 15 (App Router, RSC + SSR), TypeScript, React 19 RC, Vitest |
| API | Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2, structlog, Celery (indexer), grpcio |
| Primary DB | PostgreSQL 16 (with `pg_trgm`, `tsvector` FTS triggers) |
| Cache / queues / streams / pub-sub | Redis 7 |
| Search | Meilisearch v1.11 (primary), Postgres FTS (fallback), Rust matcher re-ranker |
| Chat gateway | Go 1.23 (coder/websocket, go-redis, golang-jwt), stateless |
| Events consumer | Go 1.23 (go-redis Streams consumer → ClickHouse HTTP) |
| Matcher | Rust 1.85 (tonic gRPC, axum for health, prometheus crate) |
| Analytics store | ClickHouse 24.11 |
| Scraper | Python 3.12 (httpx, selectolax, tenacity), Celery + Redis broker, Celery Beat schedules |
| Auth | JWT (HS256), Argon2id, refresh-token rotation, Redis fixed-window rate limiting |
| Reverse proxy / TLS | Nginx + Let's Encrypt (certbot) |
| Containerization | Docker + docker-compose (production profile) |
| CI | GitHub Actions (lint + typecheck + test per service) |
| Observability | Prometheus 2.54 + Grafana 11.3 + Loki 3 + Promtail + node_exporter + cAdvisor |
| Alerting | Alertmanager 0.27 + Telegram receiver |

Contracts between services are typed end-to-end:

- REST: FastAPI → OpenAPI (auto-generated).
- gRPC: `proto/ozzb2b/*/v1/*.proto` (matcher, events, chat protos).
- DB: SQLAlchemy models + Alembic migrations.

---

## Repository layout

```
apps/
  api/          Python FastAPI service (catalog, auth, chat HTTP, claims, admin)
  web/          Next.js 15 frontend (Russian UI)
  chat/         Go WebSocket gateway (Redis pub/sub consumer)
  events/       Go analytics consumer (Redis Streams → ClickHouse)
  matcher/      Rust gRPC search re-ranker
  scraper/      Python + Celery scraping worker
proto/          Protobuf contracts (matcher, events, chat)
infra/
  nginx/        nginx vhosts
  prometheus/   Prometheus config + alert rules
  grafana/      provisioned dashboards + datasources
  loki/         Loki log store config
  promtail/     Docker log shipper config
  alertmanager/ Alertmanager template (Telegram)
  clickhouse/   ClickHouse overrides (disables high-churn system logs)
deploy/         Bash scripts to bootstrap / apply / smoke-test the VPS
.github/workflows/ci.yml  CI per service
compose.prod.yml  Production docker-compose for the VPS
```

---

## Running locally (minimal path)

Prerequisites: Docker, Python 3.12, Node 22, Go 1.23, Rust 1.85, `protoc`.

```bash
# 1. Start Postgres + Redis + Meilisearch (dev profile comes from a separate
#    compose file in your environment; defaults in .env.example target
#    localhost:5433/6380/7700).

# 2. API
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn ozzb2b_api.app:app --reload --port 8001

# 3. Frontend
cd apps/web
npm install
npm run dev        # http://localhost:3000

# 4. Optional services
cd apps/chat    && go run ./...
cd apps/events  && go run ./...
cd apps/matcher && cargo run
cd apps/scraper && celery -A ozzb2b_scraper.tasks worker --loglevel=INFO
```

Per-service tests:

```bash
cd apps/api    && pytest                       # coverage + snapshot
cd apps/web    && npm run test:coverage        # vitest v8 coverage
cd apps/chat   && go test -race ./...
cd apps/events && go test -race ./...
cd apps/matcher && cargo test --all-targets
cd apps/scraper && pytest                      # coverage
```

Or run everything from the repo root:

```bash
make install                 # install every language toolchain
make test                    # run every unit suite
make coverage                # enforce per-service coverage thresholds
make lint                    # ruff + mypy + tsc + go vet + clippy + rustfmt
make test-api-integration    # requires Postgres + Redis; see env vars below
make test-e2e                # builds web, installs browsers, runs Playwright
```

Integration tests read their connection strings from the environment:

```bash
OZZB2B_INTEGRATION_DATABASE_URL=postgresql+asyncpg://ozzb2b:ozzb2b@127.0.0.1:5432/ozzb2b_test
OZZB2B_INTEGRATION_REDIS_URL=redis://127.0.0.1:6379/0
```

Optional pre-commit hooks (Python + secret scan + large file guard) are
configured in `.pre-commit-config.yaml`; enable with
`pip install pre-commit && pre-commit install`.

---

## Testing strategy

All work in `apps/` is guarded by a matching CI job in
`.github/workflows/ci.yml` that must be green before merging:

- **apps/api** — `pytest` + `pytest-cov` with a 60% threshold, strict
  `mypy --strict`, `ruff check`. Includes an OpenAPI snapshot test to detect
  public surface drift (`apps/api/tests/snapshots/openapi_routes.json`).
- **apps/scraper** — `pytest` with a 70% threshold, `ruff check`, per-spider
  HTML fixtures.
- **apps/web** — `vitest` with v8 coverage provider (floor: 20% lines /
  55% branches), `tsc --noEmit`, React component tests via `@testing-library/react`.
- **apps/chat, apps/events** — `go vet` + `go test -race -coverprofile`
  with a 55% coverage floor enforced by `scripts/check_go_coverage.sh`.
- **apps/matcher** — `cargo fmt --check`, `cargo clippy -- -D warnings`,
  `cargo test --all-targets`.

Extra CI gates:

- **integration api** — hard gate. Spins up Postgres 16 + Redis 7 as services
  and runs `tests/integration` (TSVECTOR / JSONB / UUID / native enums / real
  rate limiter) so ORM and cache changes that silently work on SQLite but
  break on Postgres are caught before deploy.
- **e2e (playwright, 3 viewports)** — hard gate. Builds the web app and runs
  a Playwright smoke suite on mobile (iPhone 13), tablet (iPad), and desktop
  Chrome against an intentionally unreachable API — we verify that page
  shells, routing, and HTML5 validation never regress.
- **coverage diff (changed lines)** — on pull requests, `diff-cover` enforces
  ≥85% coverage on changed Python lines; web diff-coverage is tracked
  informationally until the vitest suite grows.
- **secret scan (gitleaks)** — hard gate. Any leaked credential fails the
  build; zero tolerance.
- **proto drift** — regenerates Python stubs from `proto/` and fails if the
  committed `grpc_gen/` files don't match.
- **docker-build matrix** — builds every service's Dockerfile to catch
  packaging-only regressions.
- **security (informational)** — `pip-audit` + `bandit` for Python,
  `govulncheck` for Go, `cargo audit` for Rust, Trivy filesystem scan.

---

## Production deployment

Single VPS, orchestrated by `compose.prod.yml`:

- `deploy/vps_bootstrap.sh` — first-time nginx + SSL + compose bring-up.
- `deploy/vps_apply_stack.sh` — idempotent redeploy on git pull.
- `deploy/vps_migrate.sh` — run Alembic migrations inside the API container.
- `deploy/vps_smoke_phase*.sh` — end-to-end smoke tests.

Secrets never land in Git. Production values live in:

- `.env.prod` on the VPS (rendered from `.env.prod.example`).
- `/root/.ozzb2b_secrets` on the VPS (Grafana admin password, Telegram bot
  token, Telegram chat id). `vps_apply_stack.sh` injects them into the
  Alertmanager config template at deploy time.

CI runs lint/type/test for every language in `.github/workflows/ci.yml` on
push to `main` and pull requests.

---

## Status

Active development, single production VPS, stack reaches MVP for each domain
(catalog, search, chat, claims, analytics, observability).
