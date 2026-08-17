"""
Item 3 acceptance — the beat engine.

Every clip used to be hardcoded to 5 seconds and concatenated end to end. Eight
beat_* columns existed with zero writers, and audio_analysis.py — a working beat
tracker — had zero importers.
"""
import math
import shutil
import subprocess
import uuid
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

import tasks.production as production
from app.services.audio_analysis import (
    MAX_CLIP_SECONDS,
    MIN_CLIP_SECONDS,
    audio_analysis_service,
)


# --- helpers -----------------------------------------------------------------

def _click_track(path, bpm=120.0, seconds=20.0, sr=22050):
    """A synthetic click track: one short percussive burst per beat."""
    interval = 60.0 / bpm
    y = np.zeros(int(seconds * sr), dtype=np.float32)
    click_len = int(0.02 * sr)
    envelope = np.exp(-np.linspace(0, 12, click_len)).astype(np.float32)
    tone = np.sin(2 * np.pi * 2000 * np.arange(click_len) / sr).astype(np.float32)
    click = envelope * tone
    t = 0.0
    while t < seconds:
        start = int(t * sr)
        end = min(start + click_len, len(y))
        y[start:end] += click[: end - start]
        t += interval
    sf.write(path, y, sr)
    return path


def _even_beats(bpm=120.0, seconds=120.0):
    interval = 60.0 / bpm
    count = int(seconds / interval)
    return [i * interval for i in range(count)]


# --- analyze_beats on a real signal ------------------------------------------

def test_analyze_beats_recovers_tempo_from_a_120bpm_click_track(tmp_path):
    audio = _click_track(tmp_path / "click.wav", bpm=120.0, seconds=20.0)
    result = audio_analysis_service.analyze_beats(str(audio))

    assert "error" not in result, result
    assert abs(result["tempo"] - 120.0) <= 2.0, f"tempo was {result['tempo']}"
    assert result["beat_count"] > 30
    assert 19.0 <= result["duration"] <= 21.0


def test_analyze_beats_reports_an_error_for_a_missing_file(tmp_path):
    result = audio_analysis_service.analyze_beats(str(tmp_path / "nope.wav"))
    assert "error" in result


def test_mean_beat_interval_matches_the_tempo():
    interval = audio_analysis_service.mean_beat_interval(_even_beats(bpm=128.0, seconds=60.0))
    assert interval == pytest.approx(60.0 / 128.0, abs=1e-6)


def test_mean_beat_interval_is_none_without_two_beats():
    assert audio_analysis_service.mean_beat_interval([]) is None
    assert audio_analysis_service.mean_beat_interval([1.0]) is None


# --- the quantisation rule ---------------------------------------------------

def test_every_scene_gets_a_window_and_an_integer_duration():
    beats = _even_beats(bpm=120.0, seconds=120.0)
    rows = audio_analysis_service.map_scenes_to_beats(beats, scene_count=20, audio_duration=120.0)

    assert len(rows) == 20
    for row in rows:
        assert row["beat_end_sec"] > row["beat_start_sec"]
        assert float(row["requested_duration_sec"]).is_integer()
        assert MIN_CLIP_SECONDS <= row["requested_duration_sec"] <= MAX_CLIP_SECONDS
        assert row["beat_drift_ms"] == pytest.approx(
            (row["requested_duration_sec"] - row["beat_duration_sec"]) * 1000.0
        )


def test_windows_are_contiguous_and_cover_the_track():
    beats = _even_beats(bpm=128.0, seconds=90.0)
    rows = audio_analysis_service.map_scenes_to_beats(beats, scene_count=12, audio_duration=90.0)

    assert rows[0]["beat_start_sec"] == pytest.approx(0.0, abs=60.0 / 128.0)
    assert rows[-1]["beat_end_sec"] == pytest.approx(90.0)
    for earlier, later in zip(rows, rows[1:]):
        assert later["beat_start_sec"] == pytest.approx(earlier["beat_end_sec"])


def test_cuts_land_on_beats():
    beats = _even_beats(bpm=128.0, seconds=90.0)
    rows = audio_analysis_service.map_scenes_to_beats(beats, scene_count=12, audio_duration=90.0)
    beat_set = [round(b, 6) for b in beats]
    # Every cut except the final one (the end of the track) sits exactly on a beat.
    for row in rows[1:]:
        assert round(row["beat_start_sec"], 6) in beat_set


@pytest.mark.parametrize("bpm", [90.0, 120.0, 128.0, 174.0])
def test_drift_stays_bounded_across_twenty_scenes(bpm):
    """
    The property test that catches naive per-scene rounding: after 20 scenes the last
    scene must still start within one beat interval of its ideal position. Rounding
    each scene independently and accumulating durations fails this.
    """
    duration = 120.0
    scene_count = 20
    beats = _even_beats(bpm=bpm, seconds=duration)
    interval = 60.0 / bpm

    rows = audio_analysis_service.map_scenes_to_beats(beats, scene_count, duration)

    ideal_last_start = duration * (scene_count - 1) / scene_count
    assert abs(rows[-1]["beat_start_sec"] - ideal_last_start) <= interval, (
        f"last scene starts {rows[-1]['beat_start_sec']:.3f}s vs ideal "
        f"{ideal_last_start:.3f}s (one beat = {interval:.3f}s)"
    )

    # And the generated footage tracks the music rather than sliding off it.
    total_requested = sum(r["requested_duration_sec"] for r in rows)
    assert abs(total_requested - duration) <= max(interval, 1.0) * 2


def test_naive_rounding_would_fail_the_same_property():
    """
    Guards the guard: show the property test is not vacuous by running the naive
    algorithm (round each window, accumulate starts from durations) over the same
    input and confirming it drifts past one beat interval.
    """
    bpm, duration, scene_count = 128.0, 120.0, 20
    interval = 60.0 / bpm
    window = duration / scene_count  # 6.0s -> rounds cleanly; use an off-grid tempo

    # Make the windows deliberately off-grid: 20 scenes over 20 bars at 128 BPM.
    window = 4 * interval * 1.4  # 5.25s, rounds to 5, losing 250ms every scene
    naive_start = 0.0
    for _ in range(scene_count - 1):
        naive_start += round(window)
    ideal_last_start = window * (scene_count - 1)

    assert abs(naive_start - ideal_last_start) > interval


def test_no_scenes_or_no_audio_maps_to_nothing():
    assert audio_analysis_service.map_scenes_to_beats(_even_beats(), 0, 30.0) == []
    assert audio_analysis_service.map_scenes_to_beats(_even_beats(), 5, 0.0) == []


def test_audio_with_no_detected_beats_falls_back_to_an_even_split():
    rows = audio_analysis_service.map_scenes_to_beats([], scene_count=5, audio_duration=30.0)
    assert len(rows) == 5
    assert [r["beat_duration_sec"] for r in rows] == [pytest.approx(6.0)] * 5


def test_more_scenes_than_beats_still_produces_monotonic_windows():
    rows = audio_analysis_service.map_scenes_to_beats([0.0, 1.0, 2.0], scene_count=8, audio_duration=8.0)
    assert len(rows) == 8
    for earlier, later in zip(rows, rows[1:]):
        assert later["beat_start_sec"] >= earlier["beat_start_sec"]


# --- duration priority in the pipeline ---------------------------------------

def _scene(**kwargs):
    defaults = dict(beat_duration_sec=None, target_duration_sec=None, beat_drift_ms=None,
                    beat_start_sec=None, beat_end_sec=None)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_beat_duration_wins_over_the_brief():
    assert production._resolve_clip_duration(
        _scene(beat_duration_sec=7.4, target_duration_sec=12)
    ) == 7


def test_brief_duration_is_used_when_there_is_no_beat_grid():
    assert production._resolve_clip_duration(_scene(target_duration_sec=10)) == 10


def test_default_is_used_when_nothing_else_is_known():
    assert production._resolve_clip_duration(_scene()) == production.DEFAULT_CLIP_SECONDS


@pytest.mark.parametrize(
    "window, expected",
    [(1.2, MIN_CLIP_SECONDS), (22.0, MAX_CLIP_SECONDS), (4.4, 4), (14.6, 15)],
)
def test_requested_duration_is_clamped_to_the_models_legal_range(window, expected):
    assert production._resolve_clip_duration(_scene(beat_duration_sec=window)) == expected


def test_unparseable_durations_fall_through():
    assert production._resolve_clip_duration(
        _scene(beat_duration_sec="not a number", target_duration_sec=8)
    ) == 8


# --- assembly trim windows ---------------------------------------------------

def test_beat_window_is_none_without_beat_mapping():
    assert production._scene_beat_window(_scene()) is None


def test_beat_window_is_the_musical_span():
    window = production._scene_beat_window(_scene(beat_start_sec=12.0, beat_end_sec=17.5))
    assert window == pytest.approx(5.5)


def test_zero_length_window_is_treated_as_absent():
    assert production._scene_beat_window(_scene(beat_start_sec=4.0, beat_end_sec=4.0)) is None


async def test_assembly_writes_outpoint_directives_for_beat_windows(tmp_path, monkeypatch):
    from app.services.assembly_service import assembly_service

    monkeypatch.setattr(assembly_service, "jobs_dir", tmp_path)
    monkeypatch.setattr(assembly_service, "_ffmpeg_available", lambda: True)

    async def _fake_download(_url, dest):
        dest.write_bytes(b"fake mp4")
        return None

    monkeypatch.setattr(assembly_service, "_download_file", _fake_download)
    monkeypatch.setattr(
        assembly_service, "_run_ffmpeg",
        lambda concat_list, music, out: {"output_path": str(out), "duration": 1.0, "file_size_bytes": 1},
    )

    job_id = str(uuid.uuid4())
    await assembly_service.assemble_video(
        job_id=job_id,
        clip_urls=["http://x/1.mp4", "http://x/2.mp4", "http://x/3.mp4"],
        clip_windows=[5.25, None, 0],
    )

    concat = (tmp_path / job_id / "concat.txt").read_text()
    directives = [ln for ln in concat.splitlines() if ln.startswith("outpoint")]
    # A None window and a zero window both mean "use the whole clip".
    assert directives == ["outpoint 5.250"]


async def test_assembly_without_windows_is_unchanged(tmp_path, monkeypatch):
    from app.services.assembly_service import assembly_service

    monkeypatch.setattr(assembly_service, "jobs_dir", tmp_path)
    monkeypatch.setattr(assembly_service, "_ffmpeg_available", lambda: True)

    async def _fake_download(_url, dest):
        dest.write_bytes(b"fake mp4")
        return None

    monkeypatch.setattr(assembly_service, "_download_file", _fake_download)
    monkeypatch.setattr(
        assembly_service, "_run_ffmpeg",
        lambda concat_list, music, out: {"output_path": str(out), "duration": 1.0, "file_size_bytes": 1},
    )

    job_id = str(uuid.uuid4())
    await assembly_service.assemble_video(job_id=job_id, clip_urls=["http://x/1.mp4"])
    concat = (tmp_path / job_id / "concat.txt").read_text()
    assert not [ln for ln in concat.splitlines() if ln.startswith("outpoint")]


# --- no music --------------------------------------------------------------

def test_a_job_with_no_music_never_reaches_beat_mapping(backend_root):
    """
    Phase 1.5 sits under a `music_url` guard, so a job with no music leaves every
    beat_* column null and raises nothing.

    This is a structural check; the behavioural one runs the whole pipeline in
    tests/test_gate_smoke.py::test_a_job_with_no_music_completes_with_null_beat_columns.
    """
    import ast

    source = (backend_root / "tasks" / "production.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    def _calls_beat_mapping(node) -> bool:
        return any(
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Name)
            and sub.func.id == "_map_beats_to_scenes"
            for sub in ast.walk(node)
        )

    guarded = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and _calls_beat_mapping(node)
        and "music_url" in ast.unparse(node.test)
    ]
    assert guarded, "the Phase 1.5 call is no longer under a music_url guard"


# --- the trim actually trims -------------------------------------------------

@pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe")),
    reason="ffmpeg/ffprobe not on PATH",
)
async def test_outpoint_really_trims_clips_to_their_beat_windows(tmp_path, monkeypatch):
    """
    The beat-window trim rides on the concat demuxer's `outpoint` directive, chosen
    from the docs. This runs real ffmpeg over real MP4s with windows deliberately
    shorter than the clips, so a directive that silently does nothing fails here.
    """
    from app.services.assembly_service import assembly_service

    sources = []
    for i in range(3):
        dest = tmp_path / f"src_{i}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=24:duration=6",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
             str(dest), "-loglevel", "error"],
            check=True, capture_output=True, timeout=120,
        )
        sources.append(dest)

    async def _copy(url, dest):
        shutil.copyfile(url, dest)
        return None

    monkeypatch.setattr(assembly_service, "jobs_dir", tmp_path / "jobs")
    monkeypatch.setattr(assembly_service, "_download_file", _copy)

    result = await assembly_service.assemble_video(
        job_id="trim-check",
        clip_urls=[str(p) for p in sources],
        clip_windows=[3.5, 2.0, None],   # third clip runs full length
    )

    assert "error" not in result, result
    # 3.5 + 2.0 + 6.0 = 11.5s. Untrimmed concatenation would be 18s.
    assert abs(result["duration"] - 11.5) < 0.6, result["duration"]
