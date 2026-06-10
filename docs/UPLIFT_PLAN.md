# Odyssey ROV — Backend Uplift Master Plan

> **Goal**: Transform this from a frontend-first demo into a portfolio-grade full-stack project that showcases backend engineering competence for mid-level BE roles.

> **Principle**: Every change below should be something you can articulate in an interview. If you can't explain *why* it exists, cut it.

---

## Current State Assessment

### What's solid
- Pydantic models are well-structured with validators, typed literals, and field constraints
- Simulator has real scenario logic (state machine, operator override, physics)
- Test suite covers all three scenario paths (nominal, pressure anomaly, power fault) plus edge cases
- Clean frontend type system mirroring the backend models
- Good HMI design philosophy docs — differentiating and genuine

### What screams "FE engineer bolted on a backend"
- **N-client speed bug**: `simulator.update()` is called inside each client's WS handler — 2 clients = 2x simulation speed
- **No ConnectionManager**: no broadcast abstraction, no client lifecycle management
- **Everything in-memory**: mission logs, telemetry history, alerts — all gone on restart
- **No Dockerfiles**: docker-compose uses raw base images with inline `pip install` on every startup
- **gRPC is vaporware**: proto defined, `alertService.ts` is literally one comment, no Python gRPC server
- **Hardcoded everything**: WS URL (`ws://localhost:8000`), CORS origin (`http://localhost:5173`), no config management
- **No CI/CD**: no GitHub Actions, no linting pipeline, no automated deployment
- **No deployment**: no live URL
- **Global singleton simulator**: no concept of sessions — all clients share one simulation
- **No structured logging**: `print("WebSocket disconnected")` is the extent of observability
- **Tests share global state**: each test mutates the module-level `simulator` object directly

---

## Architecture Target

```
     ┌─────────────────────┐         ┌──────────────────────────┐
     │   React Frontend    │         │     FastAPI Backend      │
     │  (GitHub Pages)     │  wss:// │       (Fly.io)           │
     │                     │────────►├──────────────────────────┤
     │  Static build       │ https://│  WebSocket endpoint      │
     │  served over HTTPS  │────────►│  REST API                │
     └─────────────────────┘         │  gRPC server             │
                                     │  Background sim loop     │
                                     ├──────────────────────────┤
                                     │  ConnectionManager       │
                                     │  SimulatorEngine         │
                                     │  EventBus                │
                                     └────────────┬─────────────┘
                                                  │
                                        ┌─────────▼─────────┐
                                        │    PostgreSQL     │
                                        │   (Fly Postgres)  │
                                        │   event_log,      │
                                        │   missions        │
                                        └───────────────────┘
```

**Deployment note**: GitHub Pages is HTTPS-only, so the backend must be reached via `wss://` and `https://`. Fly.io provides this by default on its `.fly.dev` subdomain — no extra TLS config needed.

---

## Ticket Breakdown

Tickets are grouped into tiers. **Tier 1 is non-negotiable** — skip everything else before skipping Tier 1. Tiers 2 and 3 add depth.

### Tier 1: High Yield (Do These First)

---

#### T1-1: Decouple Simulation Loop from WebSocket Handlers

**Status**: Open (maps to existing GitHub issue)

**Problem**: `simulator.update()` is called inside each client's `while True` WS loop. N clients = Nx speed. This is the single biggest architectural flaw.

**Implementation**:

1. Create `backend/connection_manager.py`:
   ```python
   class ConnectionManager:
       def __init__(self):
           self._connections: list[WebSocket] = []

       async def connect(self, ws: WebSocket):
           await ws.accept()
           self._connections.append(ws)

       def disconnect(self, ws: WebSocket):
           self._connections.remove(ws)

       async def broadcast(self, data: dict):
           dead = []
           for conn in self._connections:
               try:
                   await conn.send_json(data)
               except Exception:
                   dead.append(conn)
           for conn in dead:
               self._connections.remove(conn)
   ```

2. Create a single background task in `main.py` using `asyncio.create_task()` on startup (use the lifespan context manager, not deprecated `@app.on_event`):
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       task = asyncio.create_task(simulation_loop())
       yield
       task.cancel()
   ```

3. The `/ws/telemetry` endpoint only does:
   - `manager.connect(ws)` on open
   - `manager.disconnect(ws)` on close
   - Forward incoming commands to the simulator via an `asyncio.Queue`

4. The background loop:
   - Calls `simulator.update()` at the configured tick rate
   - Calls `manager.broadcast(telemetry)` after each tick

**Acceptance Criteria**:
- Two clients connected: simulation runs at 1x speed (not 2x)
- Both clients receive identical, synchronised telemetry
- Command from either client affects the shared simulation
- Existing tests updated to work with the new architecture

**Why this matters for interviews**: This is a textbook producer-consumer / pub-sub pattern. Being able to explain why you decoupled the game loop from the connection handlers, and how you used asyncio primitives to coordinate them, is strong signal.

---

#### T1-2: Add PostgreSQL Persistence (Event Log)

**Status**: Open (maps to existing GitHub issue)

**Implementation**:

1. Add PostgreSQL and Adminer services to `docker-compose.yml`
2. Add SQLAlchemy + Alembic to the backend:
   - `backend/database.py` — engine, sessionmaker, Base
   - `backend/db_models.py` — `EventLog` table (id, timestamp, severity, message, mission_id)
   - `backend/repository.py` — `EventLogRepository` with `insert()` and `get_by_severity()` / `get_by_mission()`
3. Create initial Alembic migration
4. In the simulator, emit events to an internal callback. The `main.py` wiring inserts into the DB when severity >= WARNING
5. Add REST endpoints:
   - `GET /api/v1/events` — list events, filterable by severity and mission_id
   - `GET /api/v1/missions` — list past missions with summary stats

**Acceptance Criteria**:
- PostgreSQL service in docker-compose, accessible by backend
- `event_log` table created via Alembic migration
- WARNING and CRITICAL events auto-persisted during simulation
- Events survive backend restart
- REST endpoints return persisted data with filtering

**Why this matters**: Schema design, migrations, repository pattern, query design — all fundamentals for BE roles.

---

#### T1-3: Proper Dockerfiles

**Problem**: The current docker-compose uses raw base images and runs `pip install` on every `docker compose up`. This is slow, non-reproducible, and amateur.

**Note**: Only the backend needs a Dockerfile now. The frontend deploys to GitHub Pages as a static build — no container needed in production.

**Implementation**:

1. `backend/Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. Update `docker-compose.yml` to use `build:` for the backend instead of `image:` + inline commands
3. Frontend in docker-compose stays as the dev server (hot-reload) for local development only
4. Add `.dockerignore` for the backend
5. Keep a `docker-compose.dev.yml` override if you want to split dev vs prod configs

**Acceptance Criteria**:
- Backend container doesn't reinstall deps on restart
- `docker compose up` works for local dev (backend + frontend + postgres)
- Backend Dockerfile is production-ready for Fly.io deployment

---

#### T1-4: Configuration Management

**Problem**: CORS origins, WS URLs, tick rates, DB connection strings — all hardcoded.

**Implementation**:

1. Create `backend/config.py` using Pydantic Settings:
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       database_url: str = "postgresql+asyncpg://odyssey:odyssey@db:5432/odyssey"
       cors_origins: list[str] = ["http://localhost:5173"]
       ticks_per_second: int = 2
       log_level: str = "INFO"

       class Config:
           env_file = ".env"
   ```

2. Replace all hardcoded values with `settings.xxx`
3. Frontend: ensure `VITE_API_BASE_URL` and `VITE_WS_URL` are used consistently (fix the hardcoded `ws://localhost:8000` in `useTelemetry.ts`)
4. Add `.env.example` to the repo root

**Acceptance Criteria**:
- No hardcoded connection strings, URLs, or magic numbers in source
- `.env.example` documents all required config
- App works with default config out of the box

---

#### T1-5: CI/CD Pipeline (GitHub Actions)

**Implementation**:

1. `.github/workflows/ci.yml` (runs on all PRs + pushes to main):
   - **Lint**: `ruff check` (backend), `eslint` (frontend)
   - **Type check**: `mypy` (backend), `tsc --noEmit` (frontend)
   - **Test**: `pytest` with PostgreSQL service container
   - **Build**: Docker build for backend, `npm run build` for frontend
   - Matrix: Python 3.11, Node 22

2. `.github/workflows/deploy.yml` (triggered on merge to `main`):
   - **Frontend**: `npm run build` → push `dist/` to `gh-pages` branch using `peaceiris/actions-gh-pages`
   - **Backend**: `flyctl deploy` to Fly.io
   - Run smoke test against deployed URLs (healthz + WS handshake)

3. Add `ruff.toml` and update `pyproject.toml` with tool configs

**Vite config note**: Set `base: '/Odyssey-ROV-Interface/'` in `vite.config.ts` so asset paths work under the GitHub Pages subpath.

**Acceptance Criteria**:
- PRs run lint + type-check + test automatically
- Merges to main auto-deploy frontend to GitHub Pages and backend to Fly.io
- README badge shows CI status

---

#### T1-6: Deploy to a Live URL

**Implementation**:

1. **Backend → Fly.io**:
   - Create `fly.toml` for the backend
   - Provision Fly Postgres (`fly postgres create`) for the database
   - Ensure WebSocket upgrade works through Fly's proxy (it does by default)
   - Set env vars: `DATABASE_URL`, `CORS_ORIGINS` (your GitHub Pages URL)
2. **Frontend → GitHub Pages**:
   - The CI/CD workflow (T1-5) builds the Vite app and pushes to the `gh-pages` branch
   - Set `VITE_API_BASE_URL=https://your-app.fly.dev` and `VITE_WS_URL=wss://your-app.fly.dev` as build-time env vars in the GitHub Actions workflow
   - Enable GitHub Pages in repo settings → source: `gh-pages` branch
   - URL will be `https://<username>.github.io/Odyssey-ROV-Interface/` (set Vite `base` option accordingly)
3. Test WS connection across the public deployment
4. Add live URL to GitHub repo description and README

**Acceptance Criteria**:
- Frontend live on GitHub Pages over HTTPS
- Backend live on Fly.io over HTTPS
- WebSocket connects via `wss://` from the GitHub Pages frontend
- REST endpoints reachable via `https://`
- README updated with live demo link

---

### Tier 2: Backend Depth (Strong Differentiators)

---

#### T2-1: Implement gRPC Mission Log Service

**Status**: Open (maps to existing GitHub issues for proto + server + FE client)

**Implementation**:

1. Generate Python server stubs from `mission_log.proto` using `grpcio-tools`
2. Implement `MissionLogServicer` in `backend/grpc_server.py`:
   - `GetMissionLog()` returns log entries from both in-memory (current session) and database (past sessions)
3. Run gRPC server alongside FastAPI using a shared asyncio event loop (grpcio has async support, or run in a thread)
4. Keep REST `/mission-log` as a fallback but mark it deprecated
5. Frontend: implement `alertService.ts` using `grpc-web` to call `GetMissionLog`
6. Add Envoy or grpc-web proxy config if needed for browser compatibility

**Acceptance Criteria**:
- gRPC server runs on a separate port alongside FastAPI
- `GetMissionLog` RPC returns correct protobuf responses
- Frontend MissionLogModal can use either REST or gRPC
- Code generation scripts documented in README

**Why this matters**: Dual-protocol architecture (WS + gRPC) in a single app is a strong talking point. Most candidates only know REST.

---

#### T2-2: Structured Logging & Observability

**Implementation**:

1. Replace all `print()` with `structlog` or Python's `logging` with JSON formatter
2. Add request ID middleware (generate UUID per request, propagate through logs)
3. Log key events: WS connect/disconnect, commands received, simulation state changes, DB writes
4. Add `/metrics` endpoint with basic counters (connections, commands processed, events persisted) — Prometheus-compatible if ambitious
5. Health check endpoint returns richer data: DB connectivity, active connections count, uptime

**Acceptance Criteria**:
- Zero `print()` statements in backend code
- All logs are structured JSON with timestamps and context
- Health check verifies DB connectivity

---

#### T2-3: Proper Test Architecture

**Problem**: Tests currently mutate a module-level `simulator` global. No test isolation, no DB tests, `AssertionError` typo in helper.

**Implementation**:

1. Refactor: simulator should be injected via FastAPI dependency injection, not a module global
2. Use `pytest` fixtures to create fresh simulator + app instances per test
3. Add unit tests for simulator logic *without* WebSocket (pure function tests):
   - State transitions for each scenario
   - Physics calculations (depth, pressure, battery drain)
   - Command handling edge cases
   - Operator override logic
4. Add integration tests with a real test database (use `testcontainers` or a pytest-scoped Postgres fixture)
5. Add a `conftest.py` with shared fixtures
6. Fix the `AssertionError` typo in `_recv_until`
7. Target: 80%+ backend coverage

**Acceptance Criteria**:
- No shared mutable state between tests
- Unit tests for simulator run without any I/O
- Integration tests verify DB persistence
- Coverage report generated in CI

---

#### T2-4: Session / Mission Management

**Problem**: One global simulator. All clients share one mission. No concept of "sessions" or "past missions."

**Implementation**:

1. Each simulation run gets a `mission_id` (UUID)
2. `MissionManager` class tracks active and completed missions
3. On `START_SIMULATION`: create a new mission record in DB with status, scenario, start time
4. On mission end: update record with end time, outcome, final stats
5. REST endpoints:
   - `GET /api/v1/missions` — list all missions with pagination
   - `GET /api/v1/missions/{id}` — get mission detail + events
   - `GET /api/v1/missions/{id}/events` — get events for a specific mission

**Note**: Multi-session (multiple simultaneous simulations) is a stretch goal. For now, one active mission at a time is fine — the point is that missions are *recorded*.

---

### Tier 3: Polish & Completions

---

#### T3-1: Frontend — Interactive Subsystem Controls

**Status**: Open (maps to existing GitHub issue)

**Implementation**:
- Wire up `SubsystemControls.tsx` with actual command buttons:
  - All Stop → sends `SET_PROPULSION_STATE { status: "inactive" }`
  - Deploy Arm → sends `DEPLOY_ARM`
  - Collect Sample → sends `COLLECT_SAMPLE`
  - Jettison Package → uses `GuardedButton` (confirmation required) → sends `JETTISON_PACKAGE`
- The `GuardedButton` and `GuardedActionButton` components already exist — use them

---

#### T3-2: Frontend — Fix Hardcoded WS URL & Console Spam

**Implementation**:
- `useTelemetry.ts`: replace `ws://localhost:8000` with `import.meta.env.VITE_WS_URL`
- Remove `console.log(message)` and `console.log(useRovStore.getState())` from the WS message handler
- Add reconnection logic with exponential backoff

---

#### T3-3: README & Demo Polish

**Status**: Open (maps to existing GitHub issue)

**Implementation**:
- Rewrite README for a backend-engineer audience:
  - Architecture diagram (the one from this doc)
  - Tech stack table with *why* each choice was made
  - API reference (WS protocol, REST endpoints, gRPC services)
  - How to run locally, how to run tests, how to deploy
- Record a GIF or short video of a mission scenario
- Add CI badge, live demo link, and architecture diagram
- Remove the broken markdown at the bottom of the current README (unclosed code block)

---

#### T3-4: API Versioning

**Implementation**:
- Prefix all REST routes with `/api/v1/`
- Move from `@app.get("/mission-log")` to `@app.get("/api/v1/mission-log")`
- Create an APIRouter for v1 endpoints
- Remove the `/hello` endpoint (adds nothing)

---

#### T3-5: Error Handling Middleware

**Implementation**:
- Add a global exception handler that returns structured error responses
- WebSocket error handling: send error frames to client instead of silently disconnecting
- Validate incoming WS commands with Pydantic (currently raw dict parsing with `.get()`)

---

## Priority Execution Order

This is the recommended order of implementation. Each step builds on the previous.

| Order | Ticket | Effort | Impact |
|-------|--------|--------|--------|
| 1 | T1-1: Decouple sim loop | Medium | Critical — fixes the fundamental architecture bug |
| 2 | T1-4: Config management | Small | Unblocks everything else (DB URLs, deployment) |
| 3 | T1-3: Dockerfiles | Small | Clean build, faster iteration |
| 4 | T1-2: PostgreSQL persistence | Medium | The single biggest "backend engineer" signal |
| 5 | T2-3: Test architecture | Medium | Must happen before CI makes sense |
| 6 | T1-5: CI/CD pipeline | Medium | Shows engineering discipline |
| 7 | T2-2: Structured logging | Small | Quick win, interview talking point |
| 8 | T2-4: Session management | Medium | Ties persistence + API design together |
| 9 | T2-1: gRPC implementation | Medium | Fulfills the dual-protocol promise |
| 10 | T1-6: Deploy | Medium | Nothing matters without a live URL |
| 11 | T3-1–T3-5: Polish | Small each | Cleanup pass |

---

## What to Cut if Time-Constrained

If you only have a weekend, do: **T1-1 → T1-4 → T1-3 → T1-2 → T1-6**. That gives you: proper architecture, a database, Docker builds, config management, and a live URL. That's enough to talk about in interviews.

If you have two weekends, add: **T2-3 → T1-5 → T2-2**. Now you have tests, CI/CD, and structured logging.

gRPC (T2-1) is a nice-to-have. It's a talking point even with just the proto file and the REST fallback — but implementing it properly is the thing that makes the "dual-protocol architecture" claim real instead of aspirational.

---

## Interview Framing

When discussing this project for mid-level BE roles, lead with:

1. **"I built a real-time simulation engine with a decoupled architecture"** — background task loop, connection manager, pub-sub broadcast. Not a CRUD app.
2. **"I added PostgreSQL persistence with migrations"** — schema design, repository pattern, Alembic.
3. **"The system uses two distinct communication protocols"** — WebSocket for real-time streaming, gRPC for structured historical queries. Explain *why* each was chosen.
4. **"I set up CI/CD and deployment from scratch"** — GitHub Actions, Docker, Fly.io. You didn't just write code, you shipped it.
5. **"The HMI design is based on real safety-critical interface principles"** — this differentiates you from every other "I built a dashboard" project.

Don't lead with "it's an ROV simulator" — lead with the engineering patterns.

---

## Existing Issues Disposition

| Existing Issue | Disposition |
|---|---|
| Decouple simulation loop / ConnectionManager | → **T1-1** (kept, refined) |
| PostgreSQL event_log persistence | → **T1-2** (kept, expanded with migrations + repository) |
| Deploy to Fly.io | → **T1-6** (kept) |
| Subsystem control buttons (All Stop, Deploy Arm, Jettison) | → **T3-1** (kept as-is) |
| README & demo GIF | → **T3-3** (kept, expanded) |
| MissionLogButton + modal with gRPC-Web | → **T2-1** (merged into gRPC ticket) |
| gRPC server implementation | → **T2-1** (merged) |
| Proto file definition | Already done — `mission_log.proto` exists |

---

## Files to Create / Modify

### New files
- `backend/Dockerfile`
- `backend/config.py`
- `backend/connection_manager.py`
- `backend/database.py`
- `backend/db_models.py`
- `backend/repository.py`
- `backend/grpc_server.py`
- `backend/tests/conftest.py`
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `.env.example`
- `ruff.toml` or `pyproject.toml`
- `alembic.ini` + `alembic/` directory
- `docker-compose.dev.yml`
- `fly.toml` (backend)

### Modified files
- `backend/main.py` — lifespan, ConnectionManager, dependency injection
- `backend/simulator.py` — event callback hook, mission_id support
- `backend/requirements.txt` — add sqlalchemy, alembic, asyncpg, pydantic-settings, structlog, grpcio
- `docker-compose.yml` — add postgres, use build context
- `frontend/vite.config.ts` — set `base: '/Odyssey-ROV-Interface/'` for GitHub Pages
- `frontend/src/hooks/useTelemetry.ts` — env var for WS URL, remove console spam, add reconnection
- `frontend/src/features/rov-systems/SubsystemControls.tsx` — wire up buttons
- `frontend/src/services/alertService.ts` — implement gRPC client
- `README.md` — full rewrite
