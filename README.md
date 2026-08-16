# YouTube Movie Factory v3

## Overview
A standalone desktop application replacing the n8n workflows for automated YouTube video creation.

## Stage 1 Architecture Setup
See `docs/YouTube_Movie_Factory_v3.docx` for the full technical specifications.

### Running Backend Stack (Python 3.12, FastAPI, Celery, Neon DB)
1. Set up `.env` from `.env.example`
2. `cd backend`
3. `python -m venv venv`
4. `.\venv\Scripts\Activate.ps1` (Windows PowerShell) or `.\venv\Scripts\activate.bat` (Command Prompt)
5. `pip install -r requirements.txt`
6. Run server: `uvicorn app.main:app --reload`
7. Run worker: `celery -A tasks.celery_app worker --loglevel=info`

### Generation suppliers

Higgsfield is the primary generator for stills and clips. CometAPI is the fallback:
when Higgsfield is switched off, not installed, not signed in, or a call fails, the
pipeline changes supplier rather than stopping.

Higgsfield publishes no HTTP API, so the app drives its CLI — the same way it already
drives ffmpeg and yt-dlp. Set it up once per machine that runs the backend:

```
npm i -g @higgsfield/cli
higgsfield auth login       # opens a browser
```

Sign-in is a browser flow, so a person has to do it once. The CLI stores and refreshes
the token afterwards, so the worker runs unattended from then on.

Higgsfield model ids use underscores and are **not** the CometAPI names — `seedance_2_5`,
not `doubao-seedance-2-5`. `higgsfield model list --video --json` lists what your
account can reach, and `make live-check` fails with a suggestion when a configured id
is not among them.

### Running the background worker

A production run is an hour of waiting on external services. By default the pipeline
runs inside the HTTP request that started it, which is fine for local development but
means a restart, deploy or crash loses the job.

For anything longer-lived, run a worker alongside the API:

```
cd backend
python -m worker            # poll forever
python -m worker --once     # one sweep, then exit (cron, CI, manual recovery)
```

and set `RUN_JOBS_INLINE=false` so the web process only enqueues. Both together are
also safe — a job is claimed atomically, so whoever gets there first does the work.

The worker picks up queued jobs, and jobs left mid-run by a worker that stopped
reporting for `JOB_HEARTBEAT_STALE_SECONDS` (default 900). Nothing is regenerated on
resume: existing scene rows are reused, images and clips already produced are kept, and
beat mapping is not repeated — recovery costs only the work that was actually lost.
`POST /api/production/{job_id}/resume` forces the handover without waiting for the
heartbeat to go stale.

### Running Frontend Stack (React 18, Vite, Tailwind)
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Verification

```
make verify     # backend suite (all four gates) + frontend typecheck
make gates      # just the four acceptance gates
make smoke      # just the end-to-end run
```

### On Windows

`make` is a Unix tool. Windows does not have it. Run the same things directly from
PowerShell, in the `backend` folder, with the virtual environment activated:

```powershell
cd backend
.\venv\Scripts\Activate.ps1

python -m pytest                        # same as: make verify-backend
python -m pytest tests/test_gate_*.py   # same as: make gates
python -m live_check                    # same as: make live-check
python -m live_check --list             # list every check, run none
python -m worker --once                 # one worker sweep
python -m db_state                      # what the database really has (read-only)
```

The frontend half of `make verify` is `npm ci` then `npx tsc --noEmit` in `frontend`.

### Checking the real services

Everything under `make verify` replaces the external vendors with stand-ins. That
proves the wiring executes; it cannot prove the vendors answer the way the code
expects. `make live-check` is the only thing that talks to them for real:

```
make live-check       # everything except video generation — a few cents
make live-check-all   # adds one video generation — slower, the expensive one
```

It needs `env/.env` populated, and reports one line per service:

```
PASS  anthropic_vision     2.1s  strict JSON honoured, classified pass
PASS  openai_edit          8.4s  2 references accepted, 1841204 b64 chars
SKIP  supabase             0.1s  SUPABASE_URL / SUPABASE_SERVICE_KEY not set
```

Missing credentials skip rather than fail, so you can see exactly what is not covered.
Run this after any change to a vendor integration, and before trusting a deployment —
several failure modes here (a bucket that is not publicly readable, a model the key
cannot see, a rejected request parameter) are invisible to the test suite by design.

Four gates guard the wiring, because a green `tsc`, `npm run build` and `compileall`
execute no code path — which is how an unresolvable import and six orphaned services
once shipped:

| Gate | What it catches |
|---|---|
| `tests/test_gate_imports.py` | a `from app.X import Y` naming something X does not define |
| `tests/test_gate_orphans.py` | a service under `app/services/` with zero importers and no allowlist entry |
| `tests/test_gate_migration_coherence.py` | a schema column neither read nor written anywhere |
| `tests/test_gate_smoke.py` | the whole pipeline, on real Postgres, with external APIs stubbed |

The smoke gate starts a throwaway PostgreSQL cluster from the local postgres binaries.
Set `YMF_TEST_PG_EXTERNAL=1` to point it at a server that is already running (see
`backend/tests/scratch_postgres.py` for the address it expects).

It runs in two passes. The stubbed pass replaces every network edge and proves the
wiring executes. The real-media pass hands the pipeline actual MP4s and lets assembly
and QA frame extraction shell out to real `ffmpeg`, then ffprobes the assembled file —
that is what proves the ffmpeg invocations are right rather than merely reached. It
needs `ffmpeg` and `ffprobe` on PATH and skips cleanly without them.

### A note on the migration chain

`521d1b9ef974_initial_migration.py` is an autogenerated diff against a hand-created
Supabase schema, not a from-nothing initial migration — its first statement is an
`ALTER TABLE`. `alembic upgrade head` therefore cannot build a database from empty.
`backend/tests/schema_baseline.sql` reconstructs the pre-Alembic starting point so the
smoke gate can run the real migrations; migration `b7c8d9e0f1a2` folds the columns that
were applied out-of-band (the old `backend/alter.py`, plus `research_summary` and
`progress_log`) back into the chain.
