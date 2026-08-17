"""
e2e_run — one real job, end to end, against the real services.

live_check proves each supplier answers. It cannot prove the pipeline holds together:
scene ordering, the beat grid, reference resolution, the QA gate on real frames, and
the ffmpeg assembly are all code that only runs when a whole job runs. That code has
never met a real vendor reply.

    python -m e2e_run                        # 2 scenes, no music
    python -m e2e_run --scenes 3
    python -m e2e_run --music ..\\track.mp3   # adds the beat grid and the audio mix
    python -m e2e_run --keep                 # leave the rows behind for inspection

It drives the same HTTP endpoints the frontend calls, in-process, so no server has to
be running. Nothing is stubbed. It costs real generation credits — roughly one still
and one clip per scene — so it defaults to two scenes.

The brief is trimmed to --scenes before approval. Research and brief writing are real
Claude calls; only the storyboard length is ours, to keep the bill small.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Same reason as live_check: psycopg refuses the Proactor loop, and the Higgsfield CLI
# runs through a worker thread precisely so both can share the Selector loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

GREEN, RED, YELLOW, DIM, BOLD, OFF = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"
)

TOPIC = "a diver descending through a kelp forest"
SOURCE = {"text": "Slow, green, tidal. One character, no dialogue. Two shots only."}


def say(message: str = "") -> None:
    print(message, flush=True)


def step(n: int, total: int, message: str) -> None:
    say(f"\n{BOLD}[{n}/{total}]{OFF} {message}")


# ---------------------------------------------------------------------------
# Preflight — fail before spending money, not after
# ---------------------------------------------------------------------------

async def preflight() -> list[str]:
    """Everything the run needs. Returns a list of reasons not to start."""
    import shutil

    from sqlalchemy import text

    from app.core.config import settings
    from app.db.session import AsyncSessionLocal
    from app.services.higgsfield_service import higgsfield_service

    problems: list[str] = []

    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            problems.append(f"{binary} is not on PATH — assembly and QA cannot run")

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:                       # noqa: BLE001 - reported, not raised
        problems.append(f"database unreachable: {type(exc).__name__}: {exc}")

    if settings.HIGGSFIELD_ENABLED and not await higgsfield_service.available():
        problems.append(
            f"Higgsfield unavailable ({higgsfield_service.last_auth_error or 'not signed in'})"
            " — generation would silently fall back to CometAPI"
        )

    if not settings.ANTHROPIC_API_KEY:
        problems.append("ANTHROPIC_API_KEY is not set — no brief can be written")

    return problems


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

async def drive(api, scenes: int, music: Optional[Path]) -> str:
    """research -> brief -> trim -> approve -> production. Returns the job id."""
    total = 5

    step(1, total, "Research")
    response = await api.post("/api/research/start", json={
        "topic": TOPIC, "source_type": "text_brief", "source_data": SOURCE,
    })
    response.raise_for_status()
    research_id = response.json()["id"]
    detail = (await api.get(f"/api/research/{research_id}")).json()
    if detail["status"] not in ("completed", "ready"):
        raise RuntimeError(f"research ended {detail['status']}: {detail.get('error_message')}")
    say(f"  {GREEN}done{OFF}  research job {research_id}")

    step(2, total, "Creative brief (real Claude call)")
    response = await api.post("/api/curation/start", json={"research_job_id": research_id})
    response.raise_for_status()
    curation_id = response.json()["id"]
    brief_state = (await api.get(f"/api/curation/{curation_id}")).json()
    # approve accepts either, so both count as success here.
    if brief_state["status"] not in ("completed", "ready"):
        raise RuntimeError(
            f"brief ended {brief_state['status']}: {brief_state.get('error_message')}"
        )
    say(f"  {GREEN}done{OFF}  {brief_state['num_scenes']} scenes written")

    step(3, total, f"Trim to {scenes} scenes and approve")
    brief = brief_state.get("creative_brief") or {}
    storyboard = brief.get("storyboard") or brief.get("scenes") or []
    if not storyboard:
        raise RuntimeError("the brief carries no storyboard — nothing to produce")
    brief["storyboard"] = storyboard[:scenes]
    brief.pop("scenes", None)
    response = await api.put(
        f"/api/curation/{curation_id}/approve", json={"edited_brief": brief}
    )
    response.raise_for_status()
    say(f"  {GREEN}done{OFF}  approved with {len(brief['storyboard'])} scenes")

    step(4, total, "Upload music" if music else "No music — the beat grid is skipped")
    music_url = music_filename = None
    if music:
        with music.open("rb") as handle:
            response = await api.post(
                "/api/production/upload/audio",
                files={"file": (music.name, handle.read())},
            )
        response.raise_for_status()
        music_url = response.json()["public_url"]
        music_filename = music.name
        say(f"  {GREEN}done{OFF}  {music_filename} -> ...{music_url[-40:]}")

    step(5, total, "Start production")
    response = await api.post(
        "/api/production/start",
        params={"music_url": music_url, "music_filename": music_filename},
        json={
            "curation_job_id": curation_id,
            "animation_mode": "std",
            "beat_sync_enabled": bool(music_url),
        },
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    say(f"  {GREEN}queued{OFF}  production job {job_id}")
    return job_id


async def run_and_watch(job_id: str) -> None:
    """Run the pipeline, printing each progress line as the job writes it."""
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models import ProductionJob
    from tasks.production import run_production_pipeline

    say(f"\n{BOLD}Pipeline{OFF} {DIM}(stills, then animation, then QA, then assembly){OFF}")
    task = asyncio.create_task(run_production_pipeline(job_id))

    seen = 0
    started = time.time()
    while True:
        async with AsyncSessionLocal() as session:
            job = (await session.execute(
                select(ProductionJob).where(ProductionJob.id == job_id)
            )).scalar_one_or_none()
            entries = list(job.progress_log or []) if job else []

        for entry in entries[seen:]:
            text_of = entry.get("message") if isinstance(entry, dict) else str(entry)
            say(f"  {DIM}{time.time() - started:6.0f}s{OFF}  {text_of}")
        seen = len(entries)

        if task.done():
            break
        await asyncio.sleep(3)

    # Surfaces a crash inside the pipeline instead of letting it read as "finished".
    await task


async def report(job_id: str) -> int:
    """Print what the job produced and judge it. Returns the exit code."""
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models import GenerationOutcome, ProductionJob, ProductionScene

    async with AsyncSessionLocal() as session:
        job = (await session.execute(
            select(ProductionJob).where(ProductionJob.id == job_id)
        )).scalar_one()
        scenes = (await session.execute(
            select(ProductionScene)
            .where(ProductionScene.job_id == job_id)
            .order_by(ProductionScene.scene_number)
        )).scalars().all()
        outcomes = (await session.execute(
            select(GenerationOutcome).where(GenerationOutcome.job_id == job_id)
        )).scalars().all()

    say(f"\n{BOLD}Result{OFF}\n")
    say(f"  status          {job.status}")
    if job.error_message:
        say(f"  {RED}error{OFF}           {job.error_message}")
    say(f"  tempo           {job.tempo_bpm or '(no music)'}")
    say(f"  beat interval   {job.beat_interval_sec or '(no music)'}")
    say(f"  outcome rows    {len(outcomes)}  {DIM}(the learning loop){OFF}")
    say("")

    for scene in scenes:
        picture = "yes" if (scene.image_url or scene.image_b64_path) else f"{RED}no{OFF}"
        clip = scene.video_url or ""
        say(
            f"  scene {scene.scene_number}  still {picture}  "
            f"animation {scene.animation_status or '-'}  "
            f"qa {scene.qa_status or '-'}  "
            f"{scene.target_duration_sec or '-'}s  "
            f"{DIM}...{clip[-36:] if clip else 'no clip'}{OFF}"
        )

    say("")
    problems: list[str] = []
    if job.status != "completed":
        problems.append(f"job ended '{job.status}', not 'completed'")
    for scene in scenes:
        if not scene.video_url:
            problems.append(f"scene {scene.scene_number} has no clip")
    if not outcomes:
        problems.append("no generation_outcome rows — the learning loop wrote nothing")

    final = job.final_video_path
    if not final:
        problems.append("no final video path on the job")
    else:
        probed = probe(final)
        if "error" in probed:
            problems.append(f"final video is not playable: {probed['error']}")
        else:
            say(
                f"  {GREEN}final video{OFF}  {probed['codec']} "
                f"{probed['width']}x{probed['height']} {probed['duration']:.1f}s "
                f"{DIM}{final}{OFF}"
            )

    say("")
    if problems:
        say(f"{RED}{BOLD}The pipeline did not hold together.{OFF}")
        for problem in problems:
            say(f"  {RED}-{OFF} {problem}")
        say("")
        return 1

    say(f"{GREEN}{BOLD}Brief in, film out. The whole pipeline works.{OFF}\n")
    return 0


def probe(path: str) -> dict:
    """ffprobe a local file or URL. A still is not a video, whatever ffprobe calls it."""
    argv = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height",
        "-show_entries", "format=duration", "-of", "json", path,
    ]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=300)
    except Exception as exc:                       # noqa: BLE001 - reported, not raised
        return {"error": f"{type(exc).__name__}: {exc}"}
    if proc.returncode != 0:
        return {"error": (proc.stderr or "").strip()[:200] or "ffprobe exited non-zero"}

    payload = json.loads(proc.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        return {"error": "no video stream"}
    duration = float(payload.get("format", {}).get("duration") or 0.0)
    if duration <= 0:
        return {"error": "zero duration — this is a still, not a film"}
    return {
        "codec": streams[0].get("codec_name", "?"),
        "width": streams[0].get("width", 0),
        "height": streams[0].get("height", 0),
        "duration": duration,
    }


async def clean_up(job_id: str) -> None:
    """
    Remove this run's rows, children first.

    No foreign key in this schema declares ON DELETE CASCADE, so deleting the job
    while its scenes exist raises a constraint error. The order below is the reverse
    of the order the pipeline creates them.
    """
    from sqlalchemy import delete, select

    from app.db.session import AsyncSessionLocal
    from app.models import (
        GenerationOutcome, ProductionJob, ProductionScene, ProductionTrack,
    )

    async with AsyncSessionLocal() as session:
        job = (await session.execute(
            select(ProductionJob).where(ProductionJob.id == job_id)
        )).scalar_one_or_none()
        if not job:
            return

        await session.execute(delete(GenerationOutcome).where(GenerationOutcome.job_id == job_id))
        await session.execute(delete(ProductionScene).where(ProductionScene.job_id == job_id))
        await session.execute(delete(ProductionTrack).where(ProductionTrack.job_id == job_id))
        await session.execute(delete(ProductionJob).where(ProductionJob.id == job_id))
        await session.commit()

    # The curation and research rows are left alone on purpose: they are cheap, they
    # carry the brief this run used, and deleting them would take a bible with them.
    say(f"{DIM}production rows removed — pass --keep to leave them behind{OFF}")


async def main_async(args) -> int:
    import httpx

    from app.core.config import settings

    say(f"{BOLD}e2e_run — one real job, end to end{OFF}")
    say(f"{DIM}{args.scenes} scenes, music: {args.music or 'none'}. This costs credits.{OFF}")

    problems = await preflight()
    if problems:
        say(f"\n{RED}{BOLD}Not starting.{OFF}")
        for problem in problems:
            say(f"  {RED}-{OFF} {problem}")
        say("")
        return 2

    # The web layer only enqueues; this script runs the pipeline itself so it can print
    # progress as it happens. With BackgroundTasks the /start call would block for the
    # whole run and print nothing until the end.
    settings.RUN_JOBS_INLINE = False

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://e2e", timeout=1800.0
    ) as api:
        job_id = await drive(api, args.scenes, args.music)

    await run_and_watch(job_id)
    code = await report(job_id)

    if not args.keep:
        await clean_up(job_id)
    else:
        say(f"{DIM}kept: production job {job_id}{OFF}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="One real end-to-end job.")
    parser.add_argument("--scenes", type=int, default=2, help="how many scenes (default 2)")
    parser.add_argument("--music", type=Path, help="audio file; turns on the beat grid")
    parser.add_argument("--keep", action="store_true", help="do not delete the rows after")
    args = parser.parse_args()

    if args.music and not args.music.is_file():
        say(f"{RED}no such file: {args.music}{OFF}")
        return 2

    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        say(f"\n{YELLOW}stopped. The job keeps its rows; re-run to resume it.{OFF}")
        return 130
    except Exception as exc:                       # noqa: BLE001 - a runner, not a service
        say(f"\n{RED}{type(exc).__name__}: {exc}{OFF}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
