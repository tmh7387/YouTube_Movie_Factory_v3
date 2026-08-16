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
