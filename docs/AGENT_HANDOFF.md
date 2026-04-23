# ozzb2b — engineering handoff for an AI assistant

This is an opinionated, exhaustive map of the `ozzb2b` codebase written so that
a new AI model (or a new engineer) can open a fresh chat, read only this file,
and be immediately productive. It prioritizes "where does X live" and "why is
it designed this way" over narrative prose.

Treat every path as relative to the repository root unless noted.

---

## 0. Product in one paragraph

ozzb2b is a B2B marketplace: a catalog of service providers (IT outsourcing,
accounting, legal, marketing, HR) with search, claim-your-company, real-time
chat between buyers and provider owners, and product analytics. It runs on a
single VPS and intentionally uses multiple languages (Python, TypeScript, Go,
Rust) as a polyglot learning playground, while keeping contracts typed
(OpenAPI, Protobuf, SQLAlchemy models).

---

## 1. Absolute rules when editing this repo

- **Do not commit secrets.** Production secrets live in `/root/.ozzb2b_secrets`
  and `.env.prod` on the VPS. Never check in real `.env.prod`, only
  `.env.prod.example`. Alertmanager config is rendered at deploy time from
  `infra/alertmanager/alertmanager.yml.tmpl`; the rendered file is gitignored.
- **UI language is Russian.** All user-facing copy is Russian. Don't put
  English strings in JSX; localize via `src/lib/ru.ts` or inline Russian.
- **User-facing errors are Russian, English detail stays on API side.** API
  returns stable machine-readable English in `detail`. Frontend maps it to
  Russian via `apps/web/src/lib/errors.ts` (`humanizeError`). When you add a
  new backend error, add its mapping in `errors.ts` AND render it via
  `<ErrorAlert message=... />`.
- **Mobile friendly.** Every UI change must be checked on mobile/tablet/desktop.
  Tailwind-less styling lives in `apps/web/app/globals.css`.
- **TDD and existing-code-first.** Base fixes on how the codebase already
  works before introducing new frameworks. Follow existing patterns
  (dependency injection, service-layer split, typed schemas).
- **Root-cause only.** No fallbacks that hide bugs. Fix the cause. Prefer to
  add tests alongside behavior changes.
- **Security > stability > speed > scalability.** In that order of priority.

---

## 2. Services — what each one owns

| Service | Language | Purpose | Reads | Writes | Listens on |
|---|---|---|---|---|---|
| `apps/api` | Python 3.12 / FastAPI | Catalog, auth, claims, chat persistence, admin, search orchestration | Postgres, Redis, Meilisearch, gRPC matcher, ClickHouse (admin only) | Postgres, Redis streams + pub/sub, Meilisearch index | HTTP `:8001` (container `:8000`) |
| `apps/web` | TypeScript / Next.js 15 | SSR + CSR UI in Russian, SEO pages, admin pages | API via REST, WS for chat | — | HTTP `:3101` (container `:3000`) |
| `apps/chat` | Go 1.23 | Stateless WebSocket gateway for chat fanout | Redis pub/sub, JWT (HS256) | Redis pub/sub (echo) | HTTP/WS `:8090` |
| `apps/events` | Go 1.23 | Stream → ClickHouse consumer for analytics | Redis Streams | ClickHouse HTTP | HTTP `:8095` (health + `/metrics`) |
| `apps/matcher` | Rust 1.85 | gRPC re-ranker for search | — | — | HTTP `:8090` (health), gRPC `:9090` |
| `apps/scraper` | Python 3.12 / Celery | Polite crawlers + ingestion into Postgres + Meili reindex | HTTP + Postgres (read existing) | Postgres (providers), Meilisearch (reindex) | Celery via Redis broker |

The **API is the system of record**. Chat gateway and events consumer are
stateless by design — they can be restarted or replaced without data loss.

---

## 3. Where to find things (cheat sheet)

### 3.1 API (`apps/api`)

```
src/ozzb2b_api/
  app.py                  FastAPI factory, middleware, router include list
  main.py                 uvicorn entrypoint
  config.py               pydantic Settings (all env is OZZB2B_* prefixed)
  logging.py              structlog configuration
  routes/
    health.py             /health, /ready
    auth.py               /auth/* (register, login, refresh, logout, me)
    catalog.py            /providers, /categories, /countries, /cities, /legal-forms
    search.py             /search (Meili + optional matcher re-rank)
    chat.py               /chat/conversations, /messages, /ws-token
    claims.py             /providers/{slug}/claim, /me/claims, /me/providers
    admin.py              /admin/* (analytics, claim moderation)
    deps.py               FastAPI dependencies (current_user, admin-only)
  services/               pure business logic, no FastAPI imports
    auth.py               password hashing, tokens, user lifecycle
    catalog.py            provider queries, facets
    search.py             Meili-first, matcher re-rank, Postgres fallback
    chat.py               conversation + message CRUD
    claims.py             meta-tag claim flow, admin verify/reject
    analytics.py          ClickHouse queries for admin
    indexer.py            Meilisearch reindex helpers
  clients/                thin wrappers around external deps
    redis.py, meilisearch.py, matcher.py, clickhouse.py, events.py
  db/
    base.py, session.py   SQLAlchemy engine + AsyncSession
    models/               ORM entities (user, provider, category, geo, chat, provider_claim)
    migrations/versions/  Alembic migrations (timestamped files)
    seed.py, cli.py       `python -m ozzb2b_api.db.cli migrate|seed|reindex`
  schemas/                Pydantic request/response DTOs
  security/
    passwords.py          Argon2id
    tokens.py             JWT access + refresh (+ WS chat token)
    rate_limit.py         Redis fixed-window limiter
  observability/
    metrics.py            Prometheus middleware + /metrics
    security_headers.py   CSP/HSTS/etc. Starlette middleware
  grpc_gen/               generated stubs (do not edit by hand)
tests/                    pytest, DB runs against aiosqlite in-memory
```

Key code paths to know:

- `app.py` wires middleware in this exact order (outer → inner): `CORS` →
  `PrometheusMiddleware` → `SecurityHeadersMiddleware`. Keep this order;
  Prometheus must count all errors, security headers must wrap final response.
- `routes/deps.py` contains `get_current_user` (reads access token from
  `Authorization` or cookie). `get_admin_user` layers on top.
- JWT secret is `OZZB2B_JWT_SECRET`. Access TTL 15 min, refresh TTL 30 days.
  Refresh tokens are stored as SHA-256 hash only (`RefreshToken.token_hash`).
- Rate limiting is Redis-backed; the limiter decorates auth endpoints and
  reads keys like `rl:login:{ip}`. Returns `429` + `Retry-After`.
- **Error contract**: FastAPI errors raise `HTTPException(status, "stable english detail")`.
  Don't localize here — frontend does it.

### 3.2 Frontend (`apps/web`)

```
app/                      Next.js App Router pages
  page.tsx                landing
  providers/page.tsx      provider list (server component)
  providers/[slug]/page.tsx  provider detail (SEO: JSON-LD, breadcrumbs)
  providers/[slug]/claim/page.tsx  "claim your company" flow entry
  categories/page.tsx     category tree
  login/page.tsx, register/page.tsx
  chat/page.tsx           inbox
  chat/[id]/page.tsx      per-conversation chat room
  account/companies/page.tsx          provider_owner dashboard
  account/companies/[slug]/page.tsx   edit owned provider
  admin/analytics/page.tsx            admin analytics
  layout.tsx, globals.css
  robots.ts, sitemap.ts
  api/health/route.ts     Next route for health (used by Docker)
src/
  lib/
    api.ts                typed API client, exports ApiError
    errors.ts             humanizeError(err, context) → Russian string
    types.ts              TS types mirroring API schemas
    ru.ts                 category/country/city translations + freshnessLabel
    server-fetch.ts       server-only cookie forwarding helper
  components/
    ErrorAlert.tsx        unified error banner (role="alert", optional onRetry)
    SiteNav.tsx           top navigation, role-aware ("Мои компании")
    LoginForm.tsx, RegisterForm.tsx
    ClaimFlow.tsx, ClaimProviderButton.tsx
    OwnedProviderEditor.tsx
    ContactProviderButton.tsx, FreshnessBadge.tsx, Breadcrumbs.tsx
    useCurrentUser.ts
    chat/ChatInbox.tsx, chat/ChatPageClient.tsx, chat/useChatSocket.ts
```

Conventions:

- **Server Components** fetch data via `lib/api.ts`; they set `credentials:
  'include'` and use `cache: 'no-store'` to forward cookies from the browser
  to the API.
- **Client components** handle errors exclusively via:

  ```tsx
  import { humanizeError, isApiErrorStatus } from '@/lib/errors';
  import { ErrorAlert } from '@/components/ErrorAlert';

  try {
    await call();
  } catch (err) {
    if (isApiErrorStatus(err, 401)) router.push('/login?next=...');
    else setError(humanizeError(err, 'chat-send'));
  }
  ```

- **New error mapping?** Add to `DETAIL_MAP` in `src/lib/errors.ts` and a test
  in `src/lib/errors.test.ts`.
- **New UI error surface?** Use `<ErrorAlert message=... onRetry=... />` —
  don't invent a new banner, don't render raw `err.message` or `err.detail`.
- Styles are plain CSS in `app/globals.css`, custom properties define the dark
  theme. When you add UI, reuse classes (`.sidebar-card`, `.chip`, `.hero`,
  `.auth-hint`, `.auth-error`, `.error-alert`, `.grid-table`, `.empty`).

### 3.3 Chat gateway (`apps/chat`)

```
main.go                   Entrypoint: HTTP mux + /metrics, graceful shutdown
internal/
  config/                 Config.Load() reads env: PORT, JWT_SECRET, REDIS_URL, IDLE_TIMEOUT
  authz/                  JWT verifier (HS256/RS256), expects ws-chat scoped token
  pubsub/
    redis.go              RedisFactory: NewSubscriber(channel) over go-redis
    memory.go             in-memory impl for tests
  gateway/
    handler.go            /ws endpoint: verify token → subscribe → pump frames
  metrics/                Prometheus: active_connections, frames_sent_total, etc.
```

Token format: API issues a short-lived JWT with `typ=ws-chat` and `conv={id}`
from `/chat/conversations/{id}/ws-token`. Gateway subscribes to Redis channel
`chat:{conversation_id}`. Messages published by the API land here.

### 3.4 Events consumer (`apps/events`)

```
main.go                   HTTP /health /ready /metrics, runs pipeline
internal/
  stream/redis.go         XREADGROUP consumer with auto-claim for stuck messages
  pipeline/pipeline.go    Batcher: BatchSize + FlushInterval, writes to ClickHouse
  clickhouse/client.go    HTTP insert with JSONEachRow
  config/, metrics/
```

Events table is bootstrapped from the consumer on startup. The API publishes
events only when `OZZB2B_EVENTS_ENABLED=true`; consumer drains the same
stream (`OZZB2B_EVENTS_STREAM`, default `ozzb2b:events:v1`). Group name and
consumer id also come from env. Batch defaults are 200 events / 2s.

### 3.5 Matcher (`apps/matcher`)

```
src/
  main.rs                 Axum HTTP health + Tonic gRPC bind
  lib.rs                  Re-exports + proto module via tonic-build (build.rs)
  service.rs              MatcherService impl: Rank(req) → re-ranked hits
  scoring.rs              Term overlap + cosine over lightweight features
  metrics.rs              Prometheus Registry (HTTP + gRPC histograms)
proto/ozzb2b/matcher/v1/matcher.proto   contract
```

API calls `Rank(query, candidates)` over gRPC; on any error (timeout,
unavailable, invalid response) the API falls back to Meilisearch order.

### 3.6 Scraper (`apps/scraper`)

```
src/ozzb2b_scraper/
  config.py, models.py
  http.py                 PoliteFetcher: per-host rate limiting, robots, challenge detection
  robots.py               RobotsCache with fail-open policy
  pipeline.py             Ingest facts → Postgres upsert, Meili reindex, dedup (source_id, domain, fuzzy name)
  tasks.py                Celery app + beat_schedule (daily staggered)
  cli.py                  ad-hoc CLI: `run`, `list`, `run-all --fail-fast`
  spiders/
    base.py                 BaseSpider interface (source slug, async iter)
    demo_directory.py       demo dataset for dev
    ru_outsourcing_seed.py  curated RU IT outsourcing
    ru_business_services_seed.py  RU accounting/legal/marketing/HR
    ru_regional_it_seed.py  regional RU IT shops
```

Three beat entries spread daily runs at 02:00/02:20/02:40 UTC. To add a new
source:

1. Subclass `BaseSpider` in `spiders/` with a unique `source` slug.
2. Register in `spiders/__init__.py::ALL_SPIDERS`.
3. Add a `beat_schedule` entry in `tasks.py`.
4. Add an ingestion test with sample HTML fixtures.

### 3.7 Proto contracts (`proto/`)

- `matcher/v1/matcher.proto` — `MatcherService.Rank`.
- `events/v1/events.proto` — shared event envelope schema (used by API publisher
  and Go consumer).
- `chat/v1/chat.proto` — shared chat message envelope.

Generated code is NOT edited by hand:
- Python: `apps/api/src/ozzb2b_api/grpc_gen/` (regenerate with `grpcio-tools`).
- Rust: `tonic-build` at `build.rs` (automatic).
- Go: not used for RPC today; if added, put generated packages in
  `internal/proto/`.

---

## 4. Database model (Postgres)

Tables (primary keys noted):

- `users (id uuid, email, password_hash, role, created_at, ...)`
- `refresh_tokens (id uuid, user_id, token_hash, family_id, expires_at, revoked_at)`
- `countries (id int)`, `cities (id int, country_id)`, `legal_forms (id int, country_id)`
- `categories (id int, parent_id)` — nested tree
- `providers (id uuid, slug unique, display_name, legal_name, ..., search_document tsvector, meta jsonb, is_claimed, claimed_by_user_id, last_scraped_at)`
- `provider_categories (provider_id, category_id)` — many-to-many
- `provider_claims (id uuid, provider_id, user_id, status, method, token_hash, verified_at, rejected_at, ...)`
- `conversations (id uuid, user_id, provider_id UNIQUE(user_id, provider_id), last_message_at, is_active)`
- `messages (id uuid, conversation_id, sender_user_id, body, created_at)`

Important conventions:

- All app tables use **UUIDv4 primary keys** (`UUIDPrimaryKeyMixin`).
- Timestamps are `timestamptz` via `TimestampMixin`.
- `providers.search_document` is a `tsvector` maintained by a DB trigger (see
  baseline migration). `pg_trgm` is also enabled for `ILIKE` fallback.
- Enums (`user_role`, `provider_status`, `claim_status`, `claim_method`) are
  stored as VARCHAR with app-side `enum.Enum` validation (not native Postgres
  enums) to keep migrations painless.

Migration strategy:

- Alembic with one file per change, named `YYYYMMDD_####_short_description.py`.
- Always add the forward and backward steps.
- For "additive" columns: add nullable → backfill → flip non-null in a separate
  migration.
- Commands: `python -m ozzb2b_api.db.cli migrate|seed|reindex`. On the VPS:
  `bash deploy/vps_migrate.sh`.

---

## 5. Runtime data stores

| Store | Purpose | Key data / stream |
|---|---|---|
| Postgres | System of record for users, catalog, chat, claims | tables above |
| Redis db 0 (dev) / db 3 (prod) | cache, rate-limit counters, Celery broker, chat pub/sub, event stream | `rl:*`, `chat:{convId}` channels, `ozzb2b:events:v1` stream |
| Meilisearch | Full-text search for providers | index `providers` |
| ClickHouse | Product analytics store | db `ozzb2b`, table `events_v1` |

ClickHouse internal `system.*_log` tables are disabled via
`infra/clickhouse/disable_system_logs.xml` mounted into the container — this
is a deliberate trade-off for the small VPS (less diagnostics, less disk/CPU).

---

## 6. Observability & alerting

- Every service exposes **Prometheus `/metrics`** (API via middleware, Go/Rust
  via the respective libraries).
- Prometheus scrapes them per `infra/prometheus/prometheus.yml`. Rules live in
  `infra/prometheus/rules/ozzb2b.rules.yml` (service down, 5xx rate, CPU/RAM/
  disk thresholds).
- Host metrics: `node_exporter` (runs in-compose with `/proc`, `/sys`, `/`
  mounts). Container metrics: `cAdvisor v0.47.2` (pinned — newer 0.49.x drops
  per-container series on overlay2).
- Logs: Promtail ships Docker container logs → Loki. Grafana has both
  datasources pre-provisioned.
- Alerting: Alertmanager uses a Telegram receiver (token + chat id rendered
  from `/root/.ozzb2b_secrets` at deploy time). Only started when
  `--profile alerts` is active.
- Dashboards: `infra/grafana/dashboards/ozzb2b-overview.json` (services) and
  `ozzb2b-host.json` (host + containers).

---

## 7. Authentication model

- Registration: Argon2id password hash (`security/passwords.py`).
- Login: issues a short-lived JWT **access token** in body + `access_token`
  cookie AND a rotating opaque **refresh token** in `refresh_token` cookie
  (HTTP-only, `SameSite=None; Secure` in prod, `Lax` in dev).
- Refresh: server compares SHA-256 of cookie to stored `token_hash`, revokes
  the old one, issues a new pair. Reuse of a revoked family is treated as
  theft → whole family is revoked.
- `/chat/conversations/{id}/ws-token` issues a separate JWT with
  `typ=ws-chat` and `conv={id}`, valid for 60 seconds.
- Roles: `client` (default), `provider_owner` (after claim is verified),
  `admin` (set manually in DB).

---

## 8. Error handling contract

Backend:

```python
raise HTTPException(status.HTTP_400_BAD_REQUEST, "provider has no website")
```

Frontend:

```ts
// src/lib/errors.ts
const DETAIL_MAP: Record<string, string> = {
  'provider has no website':
    'В карточке компании не указан сайт — подтверждение владения недоступно.',
  // ...
};
```

Rules:

- **Never localize on the API.** Russian text in API responses breaks tests
  and other clients.
- **Never surface raw `err.message` / `err.detail` to the user.** Always go
  through `humanizeError(err, context)`.
- **401 is a redirect, not an alert.** Use `isApiErrorStatus(err, 401)` and
  `router.push('/login?next=...')`.
- **422 validation**: `humanizeError` already extracts
  `password`/`email` hints for `auth-register` context — extend similarly for
  new forms.

Test additions: `apps/web/src/lib/errors.test.ts` + matching unit tests on the
API side where the raise happens.

---

## 9. Deployment

- All workloads run under `docker compose -f compose.prod.yml` on the VPS.
- Nginx terminates TLS on the host (not in containers). Vhosts in
  `infra/nginx/*.conf` → copied into `/etc/nginx/sites-available/` by
  `deploy/vps_apply_stack.sh`.
- CI (`.github/workflows/ci.yml`) runs lint + typecheck + tests per service on
  push/PR. Green CI is required before deploy.
- Deploy cadence is **3-sync**: local → GitHub → VPS. There is a known caveat
  that the VPS currently does not have a GitHub deploy key; temporary
  workaround is `git bundle` over scp (see `deploy/` notes in recent commits).
- Smoke tests per phase live in `deploy/vps_smoke_phase*.sh`. Run the latest
  one after each deploy to validate metrics, alerts, and HTTP surfaces.

---

## 10. Common tasks — where to start

| Task | Start here | Also touch |
|---|---|---|
| Add a new API endpoint | `apps/api/src/ozzb2b_api/routes/<area>.py` | `services/<area>.py`, `schemas/<area>.py`, tests in `apps/api/tests/` |
| Add a new Postgres column | new Alembic migration, then the SQLAlchemy model under `db/models/` | Pydantic schemas in `schemas/`, frontend types in `apps/web/src/lib/types.ts` |
| Add a new UI page | `apps/web/app/<route>/page.tsx` | `src/components/`, `src/lib/api.ts` for new endpoints, update `SiteNav.tsx` if needed |
| Localize a new error | `apps/web/src/lib/errors.ts` + `errors.test.ts` | — (backend untouched) |
| Add a scraper source | new file in `apps/scraper/src/ozzb2b_scraper/spiders/` | `spiders/__init__.py`, `tasks.py` beat_schedule |
| Add a chat feature | `apps/api/src/ozzb2b_api/services/chat.py` + `routes/chat.py` | `apps/chat/internal/gateway/` if transport changes, `apps/web/src/components/chat/` |
| Add an analytics event type | API publisher (`clients/events.py`) | `apps/events/internal/pipeline/` + ClickHouse schema in `clickhouse/client.go` |
| Change matcher scoring | `apps/matcher/src/scoring.rs` + tests | keep `proto/ozzb2b/matcher/v1/matcher.proto` stable |
| Add/modify a Prometheus rule | `infra/prometheus/rules/ozzb2b.rules.yml` | Grafana dashboard JSON in `infra/grafana/dashboards/` |
| Change nginx vhost | `infra/nginx/*.conf` | `deploy/vps_apply_stack.sh` if new vhost added |

---

## 11. Testing strategy per service

- **Python (api/scraper)**: `pytest`, async mode auto, SQLite aiosqlite DB for
  model-level tests, httpx AsyncClient for integration. `mypy --strict`
  enabled for API. Run with `pytest` inside the package.
- **TypeScript (web)**: Vitest for logic (`lib/*.test.ts`). `tsc --noEmit` for
  types. Prefer small pure helpers and unit-test them (see `errors.test.ts`,
  `api.test.ts`).
- **Go (chat/events)**: `go vet ./... && go test ./...`. Use the `memory`
  pubsub / fake ClickHouse in tests. No network in tests.
- **Rust (matcher)**: `cargo fmt --check && cargo clippy -- -D warnings && cargo test`.
  Scoring is pure and has direct unit tests.

When fixing a bug, add a test that fails before and passes after. When
changing public contracts (REST/gRPC/Proto), update the contract file first,
regenerate stubs, then update consumers.

---

## 12. Known operational quirks

- **Alertmanager** needs `/alertmanager` volume owned by UID 65534
  (nobody). `vps_apply_stack.sh` does this; if you add a fresh VPS, re-run
  bootstrap.
- **cAdvisor** is pinned to `v0.47.2` — don't upgrade blindly; 0.49.x stops
  emitting per-container metrics on Docker overlay2.
- **ClickHouse** RAM limit is 1 GiB in `compose.prod.yml`. Disabled internal
  logs are required at this size.
- **WordPress sites (`xsiblings.com`, `wordpress.ozzy1986.com`, ...) also live
  on the VPS** but are NOT part of this project. Don't touch their files
  (`/var/www/xsiblings.com/...`, `/var/www/wordpress.ozzy1986.com/...`) unless
  explicitly asked. They run behind Apache on port 8081 via nginx reverse
  proxy and have their own configuration.
- **swap is enabled (1 GiB)** on the VPS with `vm.swappiness=10`. 100% swap
  use alone is not an incident — only active swap I/O is.

---

## 13. Glossary

- **Provider** — a B2B company entry in the catalog.
- **Claim** — user's assertion of ownership of a Provider. Flow: initiate →
  user places `<meta name="ozzb2b-verify" content="TOKEN">` on homepage →
  verify → backend fetches homepage → on success promotes user to
  `provider_owner` and links `providers.claimed_by_user_id`.
- **Matcher** — Rust service that re-ranks a list of Meilisearch hits given
  an original query. Stateless.
- **Events emitter** — the Python side that does
  `XADD ozzb2b:events:v1 MAXLEN ~ 100000 ...` on user actions when
  `OZZB2B_EVENTS_ENABLED=true`.
- **Freshness badge** — UI label on a provider card showing how long ago the
  scraper last refreshed that entry (`last_scraped_at`).
- **Beat** — the Celery scheduler container; it triggers scraper jobs at
  02:00/02:20/02:40 UTC daily.

---

## 14. Pointers to the most useful single files

If you only read five files before making a change, read these:

1. `apps/api/src/ozzb2b_api/app.py` — middleware + router list.
2. `apps/api/src/ozzb2b_api/config.py` — every tunable env var.
3. `apps/web/src/lib/api.ts` — the whole REST client surface and TS types
   mirror.
4. `apps/web/src/lib/errors.ts` — the error UX contract.
5. `compose.prod.yml` — what actually runs in production and how services
   reach each other.

When in doubt, grep inside `apps/<service>/` — directory layout is repeated
across services and each has a small, predictable shape.
