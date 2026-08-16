"""
Shared pytest fixtures.

`app.core.config.Settings` reads required values from the environment at import
time, so every required key is populated here *before* anything under `app.` or
`tasks.` is imported. Values are deliberately obvious placeholders — no test in
this suite may reach a real external API.
"""
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent

# `tasks.` and `app.` are both top-level packages rooted at backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from scratch_postgres import DATABASE_URL as SCRATCH_DATABASE_URL  # noqa: E402

# app.db.session builds its engine at import time, so the URL is pinned here and the
# smoke run brings a cluster up at exactly this address. Tests that never touch the
# database simply fail to connect and handle it, which is the pre-existing behaviour.
_TEST_ENV = {
    "DATABASE_URL": SCRATCH_DATABASE_URL,
    "DATABASE_URL_DIRECT": SCRATCH_DATABASE_URL,
    "COMETAPI_API_KEY": "test-cometapi-key",
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "GEMINI_API_KEY": "test-gemini-key",
    "YOUTUBE_API_KEY": "test-youtube-key",
    "YOUTUBE_CLIENT_ID": "test-client-id",
    "YOUTUBE_CLIENT_SECRET": "test-client-secret",
    "YOUTUBE_REDIRECT_URI": "http://localhost:8000/api/youtube/callback",
    "SECRET_KEY": "test-secret-key",
    "OPENAI_API_KEY": "",
    "STEM_SEPARATION_ENABLED": "false",
    "UPSCALING_ENABLED": "false",
}

for _key, _value in _TEST_ENV.items():
    os.environ.setdefault(_key, _value)


import pytest  # noqa: E402


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def backend_root() -> Path:
    return BACKEND_ROOT


# ---------------------------------------------------------------------------
# Real-database fixtures, shared by every test marked `smoke`.
#
# The cluster is session-scoped because migrations are slow; `clean_database` truncates
# between tests so each one starts from an empty schema. `api` boots the real FastAPI
# app over an in-process transport — modules that also need the vendors stubbed
# override `api` locally.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def smoke_database(backend_root):
    from scratch_postgres import (
        ScratchPostgres,
        _drop_privileges_to,
        apply_baseline,
        run_migrations,
    )

    cluster = ScratchPostgres()
    if not cluster.available:
        pytest.skip("postgres binaries not found — cannot run against a real database")
    try:
        url = cluster.start()
    except Exception as exc:  # pragma: no cover - environment dependent
        cluster.stop()
        pytest.skip(f"could not start a scratch postgres cluster: {exc}")

    try:
        # The chain cannot build a database from nothing — see schema_baseline.sql.
        apply_baseline(backend_root, _drop_privileges_to())
        run_migrations(backend_root, url)
        yield url
    finally:
        cluster.stop()


@pytest.fixture
async def clean_database(smoke_database):
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await session.execute(text(
            "TRUNCATE generation_outcome, production_scenes, production_tracks, "
            "production_jobs, curation_jobs, pre_production_bibles, research_videos, "
            "research_jobs RESTART IDENTITY CASCADE"
        ))
        await session.commit()
    return smoke_database


@pytest.fixture
async def api(clean_database):
    import httpx

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://smoke") as client:
        yield client
