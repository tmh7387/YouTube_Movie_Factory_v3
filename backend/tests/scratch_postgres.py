"""
Bring up a throwaway PostgreSQL cluster for the end-to-end smoke run (gate 8.4).

The smoke test has to run migrations for real against real Postgres — SQLite does not
exercise JSONB, and half the columns this pass wired are JSONB. testcontainers needs a
Docker daemon that CI here does not have, so this starts a local cluster from the
postgres binaries instead and tears it down afterwards.

The connection URL is fixed rather than discovered, because app.db.session builds its
engine at import time from settings.DATABASE_URL. conftest.py pins that value; this
module brings a cluster up at exactly that address.

Set YMF_TEST_PG_EXTERNAL=1 to skip the bootstrap and use whatever is already listening
at the pinned URL (a CI service container, say).
"""
from __future__ import annotations

import os
import pwd
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

PG_HOST = "127.0.0.1"
PG_PORT = int(os.environ.get("YMF_TEST_PG_PORT", "55432"))
PG_USER = "postgres"
PG_DATABASE = "ymf_test"

DATABASE_URL = (
    f"postgresql+psycopg://{PG_USER}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
)

# Accounts to drop privileges to when bootstrapping as root — initdb refuses to run
# as root, by design.
UNPRIVILEGED_CANDIDATES = ("postgres", "nobody")


def _bindir() -> Optional[Path]:
    """Locate the postgres binaries: PATH first, then the Debian versioned layout."""
    initdb = shutil.which("initdb")
    if initdb:
        return Path(initdb).parent
    root = Path("/usr/lib/postgresql")
    if root.is_dir():
        for version_dir in sorted(root.iterdir(), reverse=True):
            candidate = version_dir / "bin"
            if (candidate / "initdb").is_file():
                return candidate
    return None


def _drop_privileges_to() -> Optional[int]:
    """UID to run the cluster as, or None when we are already unprivileged."""
    if os.geteuid() != 0:
        return None
    for name in UNPRIVILEGED_CANDIDATES:
        try:
            return pwd.getpwnam(name).pw_uid
        except KeyError:
            continue
    return None


class ScratchPostgres:
    """A cluster that exists for the length of one test session."""

    def __init__(self):
        self.bindir = _bindir()
        self.data_dir: Optional[Path] = None
        self.started = False

    @property
    def available(self) -> bool:
        return self.bindir is not None

    def _run(self, argv: list[str], uid: Optional[int]) -> subprocess.CompletedProcess:
        kwargs = {"capture_output": True, "text": True, "timeout": 180}
        if uid is not None:
            kwargs["user"] = uid
        return subprocess.run(argv, **kwargs)

    def start(self) -> str:
        if os.environ.get("YMF_TEST_PG_EXTERNAL") == "1":
            return DATABASE_URL
        if not self.available:
            raise RuntimeError("postgres binaries not found")

        uid = _drop_privileges_to()
        self.data_dir = Path(tempfile.mkdtemp(prefix="ymf-pg-"))
        # initdb writes as the target user, so the directory has to belong to it.
        os.chmod(self.data_dir, 0o777)
        if uid is not None:
            os.chown(self.data_dir, uid, -1)
        cluster = self.data_dir / "data"

        result = self._run(
            [str(self.bindir / "initdb"), "-D", str(cluster), "-U", PG_USER, "--auth=trust"],
            uid,
        )
        if result.returncode != 0:
            raise RuntimeError(f"initdb failed: {result.stderr[-500:]}")

        result = self._run(
            [
                str(self.bindir / "pg_ctl"),
                "-D", str(cluster),
                "-o", f"-p {PG_PORT} -k {cluster} -c fsync=off -c full_page_writes=off",
                "-l", str(cluster / "server.log"),
                "start",
            ],
            uid,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pg_ctl start failed: {result.stderr[-500:]}")
        self.started = True

        self._wait_ready(uid)
        create = self._run(
            [str(self.bindir / "createdb"), "-h", PG_HOST, "-p", str(PG_PORT),
             "-U", PG_USER, PG_DATABASE],
            uid,
        )
        if create.returncode != 0 and "already exists" not in create.stderr:
            raise RuntimeError(f"createdb failed: {create.stderr[-500:]}")

        return DATABASE_URL

    def _wait_ready(self, uid: Optional[int], timeout: float = 30.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            probe = self._run(
                [str(self.bindir / "pg_isready"), "-h", PG_HOST, "-p", str(PG_PORT)],
                uid,
            )
            if probe.returncode == 0:
                return
            time.sleep(0.5)
        raise RuntimeError("postgres did not become ready in time")

    def stop(self) -> None:
        if self.started and self.data_dir:
            uid = _drop_privileges_to()
            self._run(
                [str(self.bindir / "pg_ctl"), "-D", str(self.data_dir / "data"), "-m", "immediate", "stop"],
                uid,
            )
            self.started = False
        if self.data_dir and self.data_dir.exists():
            shutil.rmtree(self.data_dir, ignore_errors=True)
        self.data_dir = None


def apply_baseline(backend_root: Path, uid: Optional[int] = None) -> None:
    """
    Lay down the pre-Alembic Supabase schema the migration chain assumes exists.

    See tests/schema_baseline.sql: 521d1b9ef974 is an autogenerated diff, not an
    initial migration, so the chain cannot build a database from nothing.
    """
    sql = (backend_root / "tests" / "schema_baseline.sql").read_text(encoding="utf-8")
    bindir = _bindir()
    result = subprocess.run(
        [
            str(bindir / "psql"),
            "-h", PG_HOST, "-p", str(PG_PORT), "-U", PG_USER, "-d", PG_DATABASE,
            "-v", "ON_ERROR_STOP=1", "-q", "-f", "-",
        ],
        input=sql,
        capture_output=True,
        text=True,
        timeout=120,
        **({"user": uid} if uid is not None else {}),
    )
    if result.returncode != 0:
        raise RuntimeError(f"baseline schema failed: {result.stderr[-1000:]}")


def run_migrations(backend_root: Path, database_url: str) -> None:
    """
    `alembic upgrade head` in a subprocess.

    alembic/env.py calls asyncio.run(), which cannot be nested inside the test's own
    event loop, so this has to be a separate process.
    """
    env = dict(os.environ)
    env["DATABASE_URL"] = database_url
    env["DATABASE_URL_DIRECT"] = database_url

    result = subprocess.run(
        [
            sys.executable, "-c",
            "from alembic.config import main; main(argv=['upgrade', 'head'])",
        ],
        cwd=str(backend_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed:\nSTDOUT\n{result.stdout[-2000:]}\n"
            f"STDERR\n{result.stderr[-2000:]}"
        )
