"""
Phase 4 — Audio stem separation using Demucs.
Separates a mixed audio track into drums, bass, vocals, and other stems,
then computes per-stem RMS energy envelopes for reactive cut timing.

Requires: pip install demucs torch torchaudio
Gate: settings.STEM_SEPARATION_ENABLED must be True.
"""
import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List

import numpy as np

logger = logging.getLogger(__name__)

STEMS = ["drums", "bass", "vocals", "other"]


class StemService:
    """
    Wraps Demucs CLI for stem separation, then uses librosa to compute
    per-stem RMS energy and onset events.
    """

    async def separate(self, audio_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Run Demucs on audio_path. Writes stems to output_dir/<model>/<track>/.
        Returns {"stems": {stem_name: path}, "error": str|None}.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        cmd = [
            "python", "-m", "demucs",
            "--two-stems", "vocals",   # fast: vocals vs. accompaniment
            "-o", str(out),
            audio_path,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
            if proc.returncode != 0:
                err = stderr.decode()
                logger.error(f"Demucs failed: {err}")
                return {"stems": {}, "error": err}
        except asyncio.TimeoutError:
            return {"stems": {}, "error": "Demucs timed out after 10 minutes"}
        except FileNotFoundError:
            return {"stems": {}, "error": "demucs not installed (pip install demucs)"}
        except Exception as e:
            return {"stems": {}, "error": str(e)}

        # Locate output files (demucs writes htdemucs/<track_name>/<stem>.wav)
        stem_paths: Dict[str, str] = {}
        track_name = Path(audio_path).stem
        for model_dir in sorted(out.iterdir()):
            track_dir = model_dir / track_name
            if track_dir.exists():
                for wav in track_dir.glob("*.wav"):
                    stem_paths[wav.stem] = str(wav)
                break

        if not stem_paths:
            return {"stems": {}, "error": "No stem files found after Demucs run"}

        return {"stems": stem_paths, "error": None}

    def compute_energy_envelopes(
        self,
        stem_paths: Dict[str, str],
        hop_length: int = 512,
    ) -> Dict[str, Any]:
        """
        For each stem, compute an RMS energy envelope and onset times.
        Returns {stem: {"rms": [...], "onsets_sec": [...], "sr": int, "hop": int}}.
        """
        try:
            import librosa
        except ImportError:
            return {"error": "librosa not installed"}

        envelopes: Dict[str, Any] = {}
        for stem, path in stem_paths.items():
            try:
                y, sr = librosa.load(path, sr=None, mono=True)
                rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
                onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
                envelopes[stem] = {
                    "rms": rms.tolist(),
                    "onsets_sec": onsets.tolist(),
                    "sr": sr,
                    "hop": hop_length,
                }
            except Exception as e:
                logger.warning(f"Energy envelope failed for {stem}: {e}")
                envelopes[stem] = {"error": str(e)}

        return envelopes

    def assign_stem_hints(
        self,
        scene_beat_starts: List[float],
        envelopes: Dict[str, Any],
        sr: int = 44100,
        hop_length: int = 512,
    ) -> List[str]:
        """
        For each scene's beat_start time, find which stem has the highest
        peak energy within a short window around that timestamp.
        Returns a list of stem names (one per scene).
        """
        hints: List[str] = []
        window_sec = 0.1

        valid_stems = {k: v for k, v in envelopes.items() if "rms" in v}
        if not valid_stems:
            return ["other"] * len(scene_beat_starts)

        for beat_start in scene_beat_starts:
            best_stem = "other"
            best_energy = -1.0
            for stem, data in valid_stems.items():
                rms = np.array(data["rms"])
                stem_sr = data.get("sr", sr)
                stem_hop = data.get("hop", hop_length)
                frames_per_sec = stem_sr / stem_hop
                start_frame = max(0, int((beat_start - window_sec) * frames_per_sec))
                end_frame = min(len(rms), int((beat_start + window_sec) * frames_per_sec))
                if end_frame > start_frame:
                    peak = float(rms[start_frame:end_frame].max())
                    if peak > best_energy:
                        best_energy = peak
                        best_stem = stem
            hints.append(best_stem)

        return hints


stem_service = StemService()
