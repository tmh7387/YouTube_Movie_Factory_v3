"""
worker — runs production jobs outside the web process.

Until now the pipeline ran inside the HTTP request that started it, via FastAPI
BackgroundTasks. That works until something interrupts it: a restart, a deploy, or a
crash left the job frozen mid-status with no owner and no way to resume, and a
twenty-scene video is an hour of waiting on external services.

    python -m worker           # poll forever
    python -m worker --once    # one sweep, then exit (CI, cron, manual recovery)

It picks up two kinds of work:

  * queued jobs — created by POST /api/production/start
  * abandoned jobs — mid-run, but whose owner stopped reporting for
    JOB_HEARTBEAT_STALE_SECONDS

Both go through the same claim, so running several workers is safe and running one
alongside a web process with RUN_JOBS_INLINE=true is also safe: whoever claims first
does the work, and the other returns immediately.

Restarting a job never regenerates finished scenes. Each phase skips what is already
done, so recovery costs only the work that was actually lost.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from tasks.production import (  # noqa: E402
    WORKER_ID,
    find_claimable_jobs,
    run_production_pipeline,
)

logger = logging.getLogger("worker")


class Worker:
    def __init__(self, poll_seconds: int | None = None, concurrency: int = 1):
        self.poll_seconds = poll_seconds or settings.WORKER_POLL_SECONDS
        self.concurrency = max(1, concurrency)
        self._stopping = asyncio.Event()

    def request_stop(self) -> None:
        """Finish the job in hand, then exit. Sent by SIGINT/SIGTERM."""
        if not self._stopping.is_set():
            logger.info("Shutdown requested — finishing the current job, then stopping")
            self._stopping.set()

    async def run_once(self) -> int:
        """Claim and run whatever is available right now. Returns how many jobs ran."""
        job_ids = await find_claimable_jobs(limit=self.concurrency)
        if not job_ids:
            return 0

        logger.info(f"Picked up {len(job_ids)} job(s): {', '.join(j[:8] for j in job_ids)}")
        ran = 0
        for job_id in job_ids:
            if self._stopping.is_set():
                break
            try:
                # run_production_pipeline claims the job itself and returns immediately
                # if another worker got there first, so this is safe to race.
                await run_production_pipeline(job_id)
                ran += 1
            except Exception:
                # One job blowing up must never take the worker down with it. The job
                # keeps its last status and stale heartbeat, so it becomes claimable
                # again and attempt_count records that it has been tried.
                logger.exception(f"Job {job_id} raised out of the pipeline")
        return ran

    async def run_forever(self) -> None:
        logger.info(
            f"Worker {WORKER_ID} started — polling every {self.poll_seconds}s, "
            f"stale claims reclaimed after {settings.JOB_HEARTBEAT_STALE_SECONDS}s"
        )
        while not self._stopping.is_set():
            try:
                ran = await self.run_once()
            except Exception:
                logger.exception("Worker sweep failed; continuing")
                ran = 0

            if self._stopping.is_set():
                break
            if ran == 0:
                # Nothing to do — wait, but wake immediately on shutdown.
                try:
                    await asyncio.wait_for(
                        self._stopping.wait(), timeout=self.poll_seconds
                    )
                except asyncio.TimeoutError:
                    pass
        logger.info(f"Worker {WORKER_ID} stopped")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--once", action="store_true", help="one sweep, then exit")
    parser.add_argument("--poll", type=int, default=None, help="seconds between sweeps")
    parser.add_argument(
        "--concurrency", type=int, default=1,
        help="jobs to take per sweep (they run one after another)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = Worker(poll_seconds=args.poll, concurrency=args.concurrency)

    if args.once:
        ran = await worker.run_once()
        logger.info(f"Single sweep complete — {ran} job(s) run")
        return 0

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.request_stop)
        except NotImplementedError:  # pragma: no cover - Windows
            signal.signal(sig, lambda *_a: worker.request_stop())

    await worker.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
