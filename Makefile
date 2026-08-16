# Verification entry point.
#
#   make verify        everything below
#   make gates         just the four acceptance gates (§8 of the wiring brief)
#   make smoke         just the end-to-end run (gate 8.4)
#
# The four gates exist because the previous pass shipped green on tsc, npm run build,
# compileall and an Alembic head count — none of which executes a code path, which is
# how an unresolvable import and six orphaned services got through.
#
#   8.1  tests/test_gate_imports.py              every first-party import resolves
#   8.2  tests/test_gate_orphans.py              no service with zero importers
#   8.3  tests/test_gate_migration_coherence.py  no column that exists only on paper
#   8.4  tests/test_gate_smoke.py                research -> brief -> approve -> produce

BACKEND  := backend
FRONTEND := frontend
VENV     := $(BACKEND)/.venv
PY       := $(VENV)/bin/python

GATES := tests/test_gate_imports.py \
         tests/test_gate_orphans.py \
         tests/test_gate_migration_coherence.py \
         tests/test_gate_smoke.py

.PHONY: verify verify-backend verify-frontend gates smoke live-check live-check-all db-state venv clean-venv

verify: verify-backend verify-frontend

venv: $(VENV)/bin/pytest

$(VENV)/bin/pytest:
	python3 -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -r $(BACKEND)/requirements-dev.txt

# Runs the whole backend suite, gates included.
verify-backend: venv
	cd $(BACKEND) && .venv/bin/python -m pytest

gates: venv
	cd $(BACKEND) && .venv/bin/python -m pytest $(GATES)

# Gate 8.4 needs a real PostgreSQL: it starts a throwaway cluster from the local
# postgres binaries and tears it down afterwards. Point YMF_TEST_PG_EXTERNAL=1 at an
# already-running server (see tests/scratch_postgres.py) if that is easier in CI.
smoke: venv
	cd $(BACKEND) && .venv/bin/python -m pytest tests/test_gate_smoke.py

verify-frontend:
	cd $(FRONTEND) && npm ci --no-audit --no-fund && npx tsc --noEmit

# Everything above replaces the vendors with stand-ins. This is the only thing that
# talks to them for real. Needs env/.env populated; costs a few cents.
live-check: venv
	cd $(BACKEND) && .venv/bin/python -m live_check

# Adds video generation — slower and the expensive one.
live-check-all: venv
	cd $(BACKEND) && .venv/bin/python -m live_check --all

# Read-only. Says which migrations the database really has, and what to run next.
# Use it whenever `alembic current` refuses to answer.
db-state: venv
	cd $(BACKEND) && .venv/bin/python -m db_state

clean-venv:
	rm -rf $(VENV)
