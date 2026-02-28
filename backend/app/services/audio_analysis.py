import librosa
import numpy as np
import logging
from typing import Dict, Any, List
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

audio_analysis_service = AudioAnalysisService()
