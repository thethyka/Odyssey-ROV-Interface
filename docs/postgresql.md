# PostgreSQL

This project persists mission events (WARNING/CRITICAL+ severity) to a
PostgreSQL database via SQLAlchemy (async) + Alembic. This doc covers what you
need to know to develop with it, day to day.

## Mental model

- Postgres is a **separate server process**, not a file. Your app connects to
  it over a network connection (`localhost` in dev).
- The frontend never talks to Postgres directly — only the FastAPI backend
  does, via SQLAlchemy's async engine + connection pool.
- Schema changes are tracked as **migrations** (Alembic), not by just letting
  the ORM create tables. This gives a versioned history of schema changes that
  can be applied in order to any environment.

## Connection details (local dev)

| | |
|---|---|
| Host | `localhost` (or `db` from inside other containers) |
| Port | `5432` |
| User | `odyssey` |
| Password | `odyssey` |
| Database | `odyssey` |
| URL | `postgresql+asyncpg://odyssey:odyssey@db:5432/odyssey` |

Configured via `DATABASE_URL` in [backend/config.py](../backend/config.py).
The `+asyncpg` part selects the async driver SQLAlchemy uses to speak
Postgres's wire protocol.

## Starting it up

```bash
docker-compose up
```

This starts `db` (Postgres), `adminer`, `backend`, and `frontend`. The
backend's command runs `alembic upgrade head` before starting uvicorn, so the
schema is always current on boot. The `db` service has a healthcheck
(`pg_isready`) — `backend` waits for it before starting.

## Browsing data

### Adminer (GUI, easiest)

Go to **http://localhost:8080**:

- System: `PostgreSQL`
- Server: `db`
- Username: `odyssey`
- Password: `odyssey`
- Database: `odyssey`

### psql (CLI)

```bash
docker-compose exec db psql -U odyssey
```

or, if `psql` is installed locally:

```bash
psql postgresql://odyssey:odyssey@localhost:5432/odyssey
```

Useful commands once connected:

```sql
\dt                     -- list tables
\d event_log            -- describe a table's columns/indexes
SELECT * FROM event_log ORDER BY timestamp DESC LIMIT 20;
SELECT * FROM alembic_version;   -- which migration is currently applied
```

## Schema & migrations (Alembic)

- ORM models live in [backend/db_models.py](../backend/db_models.py) (e.g.
  `EventLog`).
- Migration scripts live in `backend/alembic/versions/`. Each one has an
  `upgrade()` and `downgrade()` and links to the previous migration via
  `down_revision`, forming a chain.
- `alembic_version` (a table Alembic creates) tracks which migration the DB is
  currently at.

### Applying migrations

```bash
cd backend
alembic upgrade head
```

Run this whenever you pull changes that include new migrations, or after
resetting the database.

### Changing the schema

1. Edit the model in `backend/db_models.py`.
2. Generate a migration from the diff:
   ```bash
   cd backend
   alembic revision --autogenerate -m "describe the change"
   ```
3. **Review the generated file** in `backend/alembic/versions/` —
   autogenerate is good but doesn't always pick correct defaults for existing
   rows, and won't detect every kind of change (e.g. column renames look like
   drop+add).
4. Apply it: `alembic upgrade head`
5. Commit the model change and the migration file together.

### Undoing a migration

```bash
alembic downgrade -1     # roll back one migration
alembic downgrade base   # roll back everything
```

## Running tests against Postgres

Tests need a running Postgres instance reachable via `DATABASE_URL`. Point it
at a test database (do **not** use your dev database — the test fixtures
truncate `event_log` before every test):

```bash
export DATABASE_URL="postgresql+asyncpg://odyssey:odyssey@localhost:5433/odyssey"
cd backend
alembic upgrade head        # only needed once, or after adding migrations
cd ..
.venv/bin/python -m pytest backend/tests
```

CI spins up its own Postgres service container automatically (see
[.github/workflows/ci.yml](../.github/workflows/ci.yml)).

### Why tests use `NullPool`

`backend/database.py` builds the SQLAlchemy engine with `NullPool` when
`settings.testing` is true (set via the `TESTING` env var in
`backend/tests/conftest.py`). Without this, tests hang intermittently:

- asyncpg connections are bound to the asyncio event loop that created them.
- Each `TestClient` in the test suite runs on its own event loop.
- A pooled connection from one test's loop, reused by a later test on a
  different loop, deadlocks silently (no error, just hangs forever).

`NullPool` disables pooling — every request opens and closes a fresh
connection — which is fine for tests and avoids this entirely. Production
keeps normal pooling since it runs on one long-lived event loop.

## Production (Fly + Neon)

The deployed backend (`odyssey-rov-backend` on Fly, region `lhr`) uses a
[Neon](https://neon.tech) Postgres database (free tier, `eu-west-2` region) —
not a Fly Postgres app. Neon is serverless: it auto-suspends when idle and
wakes on the first connection (a brief cold-start delay).

The connection string is stored as the `DATABASE_URL` secret on the Fly app:

```bash
fly secrets list -a odyssey-rov-backend
```

Format differs slightly from local dev:

```
postgresql+asyncpg://<user>:<password>@<endpoint>.eu-west-2.aws.neon.tech/neondb?ssl=require
```

Two changes vs. the connection string Neon shows you in its dashboard:

- `postgresql://` → `postgresql+asyncpg://`
- `?sslmode=require` → `?ssl=require` (asyncpg's URL parser expects `ssl`,
  not `sslmode`, as the query key — but still validates the value against
  libpq's `sslmode` enum, so `require` is correct and `true` is **not**)

### Updating the production DB connection

```bash
printf 'DATABASE_URL=postgresql+asyncpg://...?ssl=require\n' | fly secrets import -a odyssey-rov-backend
```

Using `fly secrets import` with stdin (rather than `fly secrets set KEY=value`)
keeps the credential out of shell history and process listings. Setting the
secret triggers an automatic redeploy.

### Migrations in production

The Dockerfile's `CMD` runs `alembic upgrade head` before starting uvicorn, so
every deploy applies any pending migrations against the Neon database
automatically — no separate manual step needed.

## Resetting the database

To wipe all data and start fresh (e.g. local DB got into a weird state):

```bash
docker-compose down -v   # -v removes the odyssey-db-data volume
docker-compose up        # recreates the DB and re-runs migrations
```

## Key files

| File | Purpose |
|---|---|
| [backend/database.py](../backend/database.py) | Async engine, session factory, `Base` |
| [backend/db_models.py](../backend/db_models.py) | ORM models (table definitions) |
| [backend/repository.py](../backend/repository.py) | Query layer (`EventLogRepository`) |
| [backend/alembic.ini](../backend/alembic.ini) | Alembic config |
| [backend/alembic/env.py](../backend/alembic/env.py) | Alembic runtime setup (wires in `Base.metadata` and `DATABASE_URL`) |
| [backend/alembic/versions/](../backend/alembic/versions/) | Migration scripts |
| [backend/tests/conftest.py](../backend/tests/conftest.py) | Test fixtures: DB cleanup, `TESTING` flag |
