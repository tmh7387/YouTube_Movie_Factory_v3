import librosa
import numpy as np
import logging
from typing import Dict, Any, List, Optional
logger = logging.getLogger(__name__)

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
            
            return {
                "tempo": float(tempo),
                "beat_count": len(beat_times),
                "beat_intervals": beat_times.tolist(),
                "duration": float(librosa.get_duration(y=y, sr=sr))
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

    def stem_reactive_ffmpeg_filter(
        self,
        stem_hint: Optional[str],
        beat_duration: float,
    ) -> str:
        """
        Phase 4 — Return an FFmpeg video filter string that adds a subtle
        reactive effect to a scene based on which stem dominates it.

        drums   → quick zoom-in pulse at scene start
        bass    → slow brightness oscillation
        vocals  → gentle vignette fade-in
        other   → no additional filter (passthrough)
        """
        if not stem_hint or stem_hint == "other":
            return "null"

        if stem_hint == "drums":
            # Quick scale pulse from 1.0 → 1.05 over first 0.3s then back
            return (
                "scale=iw*1.05:ih*1.05,crop=iw/1.05:ih/1.05,"
                "zoompan=z='if(lte(on,8),1.05,1.0)':d=1:s=1280x720"
            )
        if stem_hint == "bass":
            # Subtle brightness oscillation (EQ filter on luma)
            return f"eq=brightness='0.05*sin(2*PI*t/{max(beat_duration, 0.1)})'"
        if stem_hint == "vocals":
            # Soft vignette fade from black edges
            return (
                "vignette=angle=PI/4:mode=backward:eval=frame,"
                "fade=t=in:st=0:d=0.3"
            )
        return "null"


audio_analysis_service = AudioAnalysisService()
