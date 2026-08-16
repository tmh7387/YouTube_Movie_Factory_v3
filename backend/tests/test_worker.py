"""
Job 4 — jobs survive the process that started them.

The pipeline used to run inside the HTTP request that started it. A restart, deploy or
crash left the job frozen mid-status with no owner and no way to resume, and every
scene already paid for was lost on any retry.

These run against the real database, because the whole mechanism is one atomic
UPDATE ... WHERE ... RETURNING and an in-memory fake would not exercise it.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

import tasks.production as production
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models import CurationJob, ProductionJob, ProductionScene
from worker import Worker

pytestmark = pytest.mark.smoke


@pytest.fixture
async def job(clean_database):
    """A queued production job with four scene rows, none of them started."""
    async with AsyncSessionLocal() as session:
        curation = CurationJob(status="approved", creative_brief={"storyboard": []})
        session.add(curation)
        await session.commit()
        await session.refresh(curation)

        row = ProductionJob(
            curation_job_id=curation.id, status="queued", num_scenes=4, num_tracks=0
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)

        for number in range(1, 5):
            session.add(ProductionScene(
                job_id=row.id, scene_number=number,
                image_prompt=f"scene {number}", animation_status="pending",
            ))
        await session.commit()
        return str(row.id)


async def _read(job_id: str) -> ProductionJob:
    async with AsyncSessionLocal() as session:
        return (await session.execute(
            select(ProductionJob).where(ProductionJob.id == job_id)
        )).scalar_one()


async def _set(job_id: str, **values) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(ProductionJob).where(ProductionJob.id == job_id).values(**values)
        )
        await session.commit()


# --- claiming ----------------------------------------------------------------

async def test_an_unclaimed_job_can_be_claimed(job):
    assert await production.claim_job(job, "worker-a") is True

    row = await _read(job)
    assert row.worker_id == "worker-a"
    assert row.claimed_at is not None
    assert row.heartbeat_at is not None
    assert row.attempt_count == 1


async def test_a_second_worker_cannot_steal_a_live_claim(job):
    assert await production.claim_job(job, "worker-a") is True
    assert await production.claim_job(job, "worker-b") is False

    row = await _read(job)
    assert row.worker_id == "worker-a"
    assert row.attempt_count == 1, "a failed claim must not bump the attempt count"


async def test_the_owner_can_reclaim_its_own_job(job):
    """A worker that restarts and finds its own claim should carry on, not deadlock."""
    await production.claim_job(job, "worker-a")
    assert await production.claim_job(job, "worker-a") is True
    assert (await _read(job)).attempt_count == 2


async def test_a_stale_claim_can_be_taken_over(job):
    await production.claim_job(job, "worker-a")
    stale = datetime.now(timezone.utc) - timedelta(
        seconds=settings.JOB_HEARTBEAT_STALE_SECONDS + 60
    )
    await _set(job, heartbeat_at=stale)

    assert await production.claim_job(job, "worker-b") is True
    assert (await _read(job)).worker_id == "worker-b"


async def test_two_workers_racing_produce_exactly_one_winner(job):
    """The claim is one atomic statement; concurrency must not produce two owners."""
    results = await asyncio.gather(
        *[production.claim_job(job, f"worker-{i}") for i in range(8)]
    )
    assert sum(results) == 1, results
    assert (await _read(job)).attempt_count == 1


async def test_releasing_makes_a_job_immediately_claimable(job):
    await production.claim_job(job, "worker-a")
    await production.release_job(job)

    row = await _read(job)
    assert row.worker_id is None
    assert await production.claim_job(job, "worker-b") is True


# --- finding work ------------------------------------------------------------

async def test_a_queued_job_is_claimable(job):
    assert job in await production.find_claimable_jobs()


async def test_a_live_job_is_not_offered_to_another_worker(job):
    await production.claim_job(job, "worker-a")
    assert job not in await production.find_claimable_jobs()


async def test_an_abandoned_mid_run_job_is_offered_again(job):
    await production.claim_job(job, "worker-a")
    await _set(
        job,
        status="animating",
        heartbeat_at=datetime.now(timezone.utc) - timedelta(
            seconds=settings.JOB_HEARTBEAT_STALE_SECONDS + 60
        ),
    )
    assert job in await production.find_claimable_jobs()


@pytest.mark.parametrize("status", ["completed", "failed", "qa_review", "assembly_failed"])
async def test_terminal_jobs_are_left_alone(job, status):
    await _set(job, status=status, worker_id=None, heartbeat_at=None)
    assert job not in await production.find_claimable_jobs()


# --- the pipeline respects the claim -----------------------------------------

async def test_the_pipeline_does_not_start_a_second_run(job, monkeypatch):
    """
    The guard that makes an inline run and a worker safe to have at once: whoever
    claims first does the work, the other returns without touching anything.
    """
    await production.claim_job(job, "another-worker")

    started = []
    monkeypatch.setattr(production, "_log", lambda *a, **kw: started.append(a))

    await production.run_production_pipeline(job)
    assert started == [], "pipeline ran despite the job being owned elsewhere"


async def test_progress_refreshes_the_heartbeat(job):
    await production.claim_job(job)
    await _set(job, heartbeat_at=datetime.now(timezone.utc) - timedelta(seconds=600))

    before = (await _read(job)).heartbeat_at
    await production._log(job, "still working")
    after = (await _read(job)).heartbeat_at

    assert after > before


async def test_a_status_change_refreshes_the_heartbeat(job):
    await production.claim_job(job)
    await _set(job, heartbeat_at=datetime.now(timezone.utc) - timedelta(seconds=600))

    before = (await _read(job)).heartbeat_at
    await production._update_status(job, "animating")
    assert (await _read(job)).heartbeat_at > before


# --- resumability ------------------------------------------------------------

async def test_resuming_reuses_existing_scene_rows(job, monkeypatch):
    """
    Re-running must not re-create scenes: (job_id, scene_number) is unique, so a second
    insert would blow up, and any image or clip already paid for would be orphaned.
    """
    calls = {"images": 0, "animations": 0}

    async def _noop_image(_scene_id):
        calls["images"] += 1

    async def _noop_animate(_scene_id, **_kw):
        calls["animations"] += 1

    async def _noop_assemble(*_a, **_kw):
        pass

    monkeypatch.setattr(production, "_generate_scene_image", _noop_image)
    monkeypatch.setattr(production, "_animate_scene", _noop_animate)
    monkeypatch.setattr(production, "_assemble_video", _noop_assemble)

    # The brief is empty, so without the resume path Phase 1 would abort on
    # "No storyboard in brief" — the existing rows are what let it continue.
    async with AsyncSessionLocal() as session:
        row = (await session.execute(
            select(ProductionJob).where(ProductionJob.id == job)
        )).scalar_one()
        curation = (await session.execute(
            select(CurationJob).where(CurationJob.id == row.curation_job_id)
        )).scalar_one()
        curation.creative_brief = {"storyboard": [{"scene_index": 1}]}
        await session.commit()

    await production.run_production_pipeline(job)

    async with AsyncSessionLocal() as session:
        scenes = (await session.execute(
            select(ProductionScene).where(ProductionScene.job_id == job)
        )).scalars().all()

    assert len(scenes) == 4, "scene rows were duplicated on resume"
    assert calls["images"] == 4
    assert calls["animations"] == 4

    log = (await _read(job)).progress_log
    assert any("Phase 1 skipped" in line for line in log), log


async def test_an_image_that_already_exists_is_not_regenerated(job, monkeypatch, tmp_path):
    async with AsyncSessionLocal() as session:
        scene = (await session.execute(
            select(ProductionScene).where(ProductionScene.job_id == job)
            .order_by(ProductionScene.scene_number)
        )).scalars().first()
        scene.image_url = "https://cdn.test/already.jpg"
        await session.commit()
        scene_id = str(scene.id)

    async def _must_not_run(*_a, **_kw):
        raise AssertionError("regenerated an image that already existed")

    monkeypatch.setattr(production.media_gen_service, "generate_image", _must_not_run)
    monkeypatch.setattr(production.gpt_image_service, "generate_with_character", _must_not_run)

    await production._generate_scene_image(scene_id)  # must simply return


async def test_a_failed_image_is_retried_on_resume(job, monkeypatch, tmp_path):
    monkeypatch.setattr(production, "IMAGE_CACHE_DIR", tmp_path)

    async with AsyncSessionLocal() as session:
        scene = (await session.execute(
            select(ProductionScene).where(ProductionScene.job_id == job)
            .order_by(ProductionScene.scene_number)
        )).scalars().first()
        scene.image_url = "https://cdn.test/dead.jpg"
        scene.animation_status = "image_failed"
        await session.commit()
        scene_id = str(scene.id)

    attempted = []

    async def _generate(prompt, model=None, **_kw):
        attempted.append(prompt)
        return {"url": "https://cdn.test/fresh.jpg"}

    async def _download(_url, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"jpeg")
        return True

    monkeypatch.setattr(production.media_gen_service, "generate_image", _generate)
    monkeypatch.setattr(production, "_download_image", _download)

    await production._generate_scene_image(scene_id)
    assert attempted, "image_failed scene was skipped instead of retried"


async def test_beat_mapping_is_not_repeated_on_resume(job, monkeypatch):
    await _set(job, music_url="https://stub/track.wav", tempo_bpm=120.0)

    async def _must_not_run(*_a, **_kw):
        raise AssertionError("re-ran beat mapping on a job that already has a grid")

    async def _noop(*_a, **_kw):
        pass

    monkeypatch.setattr(production, "_map_beats_to_scenes", _must_not_run)
    monkeypatch.setattr(production, "_generate_scene_image", _noop)
    monkeypatch.setattr(production, "_animate_scene", _noop)
    monkeypatch.setattr(production, "_assemble_video", _noop)

    await production.run_production_pipeline(job)
    assert any("Phase 1.5 skipped" in line for line in (await _read(job)).progress_log)


# --- the worker loop ---------------------------------------------------------

async def test_a_single_sweep_runs_the_queued_job(job, monkeypatch):
    ran = []

    async def _fake_pipeline(job_id, **_kw):
        ran.append(job_id)

    monkeypatch.setattr("worker.run_production_pipeline", _fake_pipeline)

    count = await Worker().run_once()
    assert count == 1
    assert ran == [job]


async def test_a_sweep_with_nothing_to_do_is_a_no_op(clean_database, monkeypatch):
    async def _must_not_run(*_a, **_kw):
        raise AssertionError("ran a pipeline with no claimable jobs")

    monkeypatch.setattr("worker.run_production_pipeline", _must_not_run)
    assert await Worker().run_once() == 0


async def test_one_exploding_job_does_not_kill_the_worker(job, monkeypatch):
    async def _explode(_job_id, **_kw):
        raise RuntimeError("vendor melted")

    monkeypatch.setattr("worker.run_production_pipeline", _explode)

    # Must not raise: the job keeps its status and stale heartbeat, so it comes back
    # round as claimable rather than taking the worker down with it.
    assert await Worker().run_once() == 0


async def test_shutdown_stops_the_loop(job, monkeypatch):
    async def _fake_pipeline(_job_id, **_kw):
        pass

    monkeypatch.setattr("worker.run_production_pipeline", _fake_pipeline)

    worker = Worker(poll_seconds=60)
    worker.request_stop()
    await asyncio.wait_for(worker.run_forever(), timeout=5)


# --- the API surface ---------------------------------------------------------

async def test_start_enqueues_without_running_inline(api, monkeypatch):
    """With a worker deployed, the web process should only enqueue."""
    monkeypatch.setattr(settings, "RUN_JOBS_INLINE", False)

    async def _must_not_run(*_a, **_kw):
        raise AssertionError("web process ran the pipeline with RUN_JOBS_INLINE off")

    monkeypatch.setattr("app.api.production.run_production_pipeline", _must_not_run)

    async with AsyncSessionLocal() as session:
        curation = CurationJob(
            status="approved",
            creative_brief={"storyboard": [{"scene_index": 1, "visual_prompt": "x"}]},
        )
        session.add(curation)
        await session.commit()
        await session.refresh(curation)
        curation_id = str(curation.id)

    response = await api.post("/api/production/start", json={
        "curation_job_id": curation_id, "animation_mode": "std", "beat_sync_enabled": False,
    })
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "queued"
    assert response.json()["id"] in await production.find_claimable_jobs()


async def test_resume_releases_the_claim_and_requeues(api, job, monkeypatch):
    monkeypatch.setattr(settings, "RUN_JOBS_INLINE", False)
    await production.claim_job(job, "dead-worker")
    await _set(job, status="animating")

    response = await api.post(f"/api/production/{job}/resume")
    assert response.status_code == 200, response.text
    assert response.json()["resumed_from"] == "animating"

    row = await _read(job)
    assert row.worker_id is None
    assert row.status == "queued"
    assert job in await production.find_claimable_jobs()


async def test_resuming_a_completed_job_is_rejected(api, job):
    await _set(job, status="completed")
    response = await api.post(f"/api/production/{job}/resume")
    assert response.status_code == 409


async def test_resuming_an_unknown_job_is_a_404(api):
    response = await api.post(f"/api/production/{uuid.uuid4()}/resume")
    assert response.status_code == 404
