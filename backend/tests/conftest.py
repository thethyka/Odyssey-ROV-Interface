# backend/tests/conftest.py
import os

# Must be set before any `backend.*` import: it's read when the DB engine is
# constructed at import time, switching the engine to NullPool so connections
# are never reused across the per-test event loops TestClient creates.
os.environ.setdefault("TESTING", "1")

import asyncio  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from backend.config import settings  # noqa: E402
from backend.main import app  # noqa: E402
from backend.simulator import RovSimulator  # noqa: E402


@pytest.fixture
def client():
    """TestClient as a context manager so FastAPI's lifespan (and therefore
    app.state.sim_manager) actually starts up/shuts down for each test."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def fast_mode():
    """Run every session's simulator at high tick rate for fast tests.

    TICKS_PER_SECOND lives on the RovSimulator class, and each websocket
    session now creates its own instance, so we patch the class attribute
    rather than a single shared instance.
    """
    original = RovSimulator.TICKS_PER_SECOND
    RovSimulator.TICKS_PER_SECOND = 200
    yield
    RovSimulator.TICKS_PER_SECOND = original


@pytest.fixture(autouse=True)
def _clean_event_log():
    """Ensure each test starts with an empty event_log table."""
    asyncio.run(_truncate_event_log())
    yield


async def _truncate_event_log():
    """Use a short-lived engine: the global one is bound to the app's event
    loop, which differs from the loop `asyncio.run` creates here."""
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("TRUNCATE TABLE event_log"))
    finally:
        await engine.dispose()
