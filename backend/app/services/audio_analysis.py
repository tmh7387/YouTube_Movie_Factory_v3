"""
AudioAnalysisService — beat tracking and the scene/beat grid.

analyze_beats() reports where the beats are. map_scenes_to_beats() turns that grid
into per-scene cut points and the integer clip duration each generator is actually
asked for. The two are separate on purpose: the first touches audio, the second is
pure arithmetic and is the part worth testing.

THE QUANTISATION RULE
---------------------
Video generators take **integer** seconds. Musical durations are not integers: at
128 BPM one bar is 1.875s, so a 5s clip is 2.67 bars and always lands off-grid.
Rounding each scene independently makes the error compound — twenty scenes each
rounded up by 400ms puts the last cut 8 seconds late, which is audible as the video
sliding off the music.

So:

1. Cut points come from the **absolute** ideal grid (scene i starts at
   i * audio_duration / scene_count), snapped to the nearest beat. Starts are never
   accumulated from previous durations, so a start can never be more than half a beat
   interval away from where it belongs, no matter how many scenes precede it.
2. The integer duration requested from the generator aims at
   `musical_window - carried`, where `carried` is how much longer the generated
   footage already runs than the music it covers. Rounding residue is paid back on
   the next scene instead of accumulating.
3. The signed residual for each scene is recorded in beat_drift_ms.
4. Generation is never warped to fit. Cut points are corrected at assembly, where
   each clip is trimmed to its beat_end - beat_start window.
"""
import logging
from typing import Any, Dict, List, Optional

import librosa
import numpy as np

logger = logging.getLogger(__name__)

# Seedance 2.0 accepts 4–15 integer seconds; Kling's range sits inside that.
MIN_CLIP_SECONDS = 4
MAX_CLIP_SECONDS = 15


class AudioAnalysisService:
    def __init__(self):
        pass

    def analyze_beats(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze audio file to find tempo and beat timestamps.
        Useful for syncing video cuts to music.
        """
        try:
            y, sr = librosa.load(audio_path)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

            # Convert beat frames to timestamps
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            # librosa returns tempo as a 1-element array in recent versions.
            tempogram_tempo = float(np.atleast_1d(tempo)[0])
            # The tempogram estimate comes off a log-spaced grid whose spacing is set by
            # hop_length: at the default hop the representable values either side of 120
            # BPM are ~117.5 and ~123.1, so a clean 120 BPM click track reports 117.5.
            # The beat positions themselves are unbiased — only the per-gap quantisation
            # is not — so the tempo actually reported is the least-squares slope through
            # (beat index, beat time), which is also what the scene grid is built from.
            beat_tempo = self._tempo_from_beats(beat_times)

            return {
                "tempo": beat_tempo if beat_tempo is not None else tempogram_tempo,
                "tempogram_tempo": tempogram_tempo,
                "beat_count": len(beat_times),
                "beat_intervals": beat_times.tolist(),
                "duration": float(librosa.get_duration(y=y, sr=sr)),
            }
        except Exception as e:
            logger.error(f"Audio analysis error for {audio_path}: {e}")
            return {"error": str(e)}

    def extract_segments(self, audio_path: str, top_db: int = 30) -> List[Dict[str, Any]]:
        """
        Detect non-silent segments in the audio.
        """
        try:
            y, sr = librosa.load(audio_path)
            intervals = librosa.effects.split(y, top_db=top_db)
            times = librosa.frames_to_time(intervals, sr=sr)

            return [
                {"start": float(start), "end": float(end)}
                for start, end in times
            ]
        except Exception as e:
            logger.error(f"Segment extraction error: {e}")
            return []

    # -----------------------------------------------------------------------
    # Scene/beat grid
    # -----------------------------------------------------------------------

    def _tempo_from_beats(self, beat_times) -> Optional[float]:
        """BPM implied by the detected beat positions, or None when unmeasurable."""
        interval = self.mean_beat_interval(beat_times)
        if interval is None or interval <= 0:
            return None
        return 60.0 / interval

    @staticmethod
    def mean_beat_interval(beat_times) -> Optional[float]:
        """
        Seconds per beat, as the least-squares slope through (beat index, beat time).

        Not the median gap: beat times are quantised to the analysis frame (~23ms at
        the default hop), which biases individual gaps but not the positions. Fitting
        the whole sequence averages that quantisation out.
        """
        # `beat_times or []` is unsafe here — a numpy array has no truth value.
        beats = np.sort(np.asarray([] if beat_times is None else list(beat_times), dtype=float))
        if beats.size < 2:
            return None
        if beats.size == 2:
            return float(beats[1] - beats[0])
        slope = float(np.polyfit(np.arange(beats.size), beats, 1)[0])
        return slope if slope > 0 else None

    @staticmethod
    def _nearest_beat(beats: List[float], t: float, min_index: int) -> Optional[int]:
        """Index of the beat closest to t, never below min_index."""
        if min_index >= len(beats):
            return None
        best_index = min_index
        best_gap = abs(beats[min_index] - t)
        for i in range(min_index + 1, len(beats)):
            gap = abs(beats[i] - t)
            if gap <= best_gap:
                best_index, best_gap = i, gap
            elif beats[i] > t:
                # Beats are sorted; once we pass t the gap only grows.
                break
        return best_index

    def map_scenes_to_beats(
        self,
        beat_times: List[float],
        scene_count: int,
        audio_duration: float,
        min_duration: int = MIN_CLIP_SECONDS,
        max_duration: int = MAX_CLIP_SECONDS,
    ) -> List[Dict[str, float]]:
        """
        Distribute `scene_count` scenes across the beat grid.

        Returns one dict per scene, in order:
            beat_start_sec, beat_end_sec  — the musical window, cuts land on beats
            beat_duration_sec             — beat_end_sec - beat_start_sec
            requested_duration_sec        — the integer seconds asked of the generator
            beat_drift_ms                 — signed (requested - musical), milliseconds
                                            positive = clip runs longer than its window

        With no beats detected the windows fall back to an even split of the track —
        still better than the old fixed 5s, and the drift columns stay honest about it.
        Returns [] only when there is nothing at all to map: no scenes, or no audio.
        """
        beats = sorted(float(b) for b in ([] if beat_times is None else list(beat_times)))
        if scene_count <= 0 or audio_duration <= 0:
            return []

        # --- Boundaries: absolute ideal grid, snapped to beats ---------------
        boundaries: List[float] = []
        used = -1
        for i in range(scene_count):
            ideal = audio_duration * i / scene_count
            index = self._nearest_beat(beats, ideal, used + 1) if beats else None
            if index is None:
                # More scenes than beats — fall back to the ideal time, still monotonic.
                boundaries.append(max(ideal, boundaries[-1] if boundaries else 0.0))
            else:
                boundaries.append(max(beats[index], boundaries[-1] if boundaries else 0.0))
                used = index
        # The final cut is the end of the track, not a beat: nothing follows it.
        boundaries.append(max(audio_duration, boundaries[-1]))

        # --- Integer durations with the residual carried forward -------------
        rows: List[Dict[str, float]] = []
        carried = 0.0  # seconds of generated footage in excess of music covered so far

        for i in range(scene_count):
            start, end = boundaries[i], boundaries[i + 1]
            musical = max(end - start, 0.0)

            requested = int(round(musical - carried))
            requested = max(min_duration, min(max_duration, requested))

            residual = requested - musical
            carried += residual
            # When windows sit outside [min_duration, max_duration] no integer choice
            # can absorb the residual, and carried would run away over a long sequence.
            # Assembly trimming is what fixes those cuts, so cap the carry.
            carried = max(-float(max_duration), min(float(max_duration), carried))

            rows.append({
                "beat_start_sec": start,
                "beat_end_sec": end,
                "beat_duration_sec": musical,
                "requested_duration_sec": float(requested),
                "beat_drift_ms": residual * 1000.0,
            })

        return rows


audio_analysis_service = AudioAnalysisService()
