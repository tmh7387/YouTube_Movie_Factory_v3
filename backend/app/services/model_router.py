"""
ModelRouter — Smart model selection based on scene analysis.

Analyzes scene prompts to recommend the optimal animation model
based on content characteristics (motion intensity, character focus, etc.)
"""
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Model capability profiles
MODEL_PROFILES = {
    "kling-v2-master": {
        "display_name": "Kling v2 Master",
        "strengths": ["character_closeup", "facial_expression", "slow_motion", "portrait"],
        "weaknesses": ["fast_action", "wide_landscape"],
        "cost_tier": "high",
        "max_duration": 10,
        "default_mode": "pro",
    },
    "kling-v1-6": {
        "display_name": "Kling v1.6",
        "strengths": ["general_purpose", "moderate_motion", "landscape"],
        "weaknesses": ["complex_character"],
        "cost_tier": "medium",
        "max_duration": 10,
        "default_mode": "std",
    },
    "doubao-seedance-2-0": {
        "display_name": "Seedance 2.0",
        "strengths": ["dance", "fast_action", "dynamic_camera", "character_movement", "wide_shot"],
        "weaknesses": ["subtle_expression"],
        "cost_tier": "medium",
        "max_duration": 10,
        "default_mode": "std",
    },
    "wan-pro": {
        "display_name": "Wan Pro",
        "strengths": ["cinematic", "atmospheric", "slow_reveal", "landscape", "abstract"],
        "weaknesses": ["fast_action", "dialogue"],
        "cost_tier": "low",
        "max_duration": 5,
        "default_mode": "std",
    },
}

# Keywords that signal scene characteristics
SCENE_SIGNALS = {
    "character_closeup": ["close-up", "closeup", "face", "portrait", "expression", "eyes", "emotional"],
    "fast_action": ["explosion", "chase", "running", "fight", "fast", "action", "crash", "battle"],
    "dance": ["dance", "dancing", "choreograph", "rhythm", "groove", "moves"],
    "slow_motion": ["slow motion", "slow-mo", "time lapse", "gradual", "gentle"],
    "landscape": ["wide shot", "panoramic", "aerial", "landscape", "establishing", "skyline", "horizon"],
    "dynamic_camera": ["tracking shot", "dolly", "crane", "steadicam", "orbit", "circle"],
    "atmospheric": ["fog", "mist", "ethereal", "dreamlike", "surreal", "abstract", "particles"],
    "cinematic": ["cinematic", "film grain", "anamorphic", "bokeh", "shallow depth"],
}


def analyze_scene(visual_prompt: str, motion_prompt: str = "") -> dict:
    """
    Analyze a scene's prompts and return detected characteristics.
    """
    combined = f"{visual_prompt} {motion_prompt}".lower()
    detected = {}

    for signal, keywords in SCENE_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            detected[signal] = score

    return detected


def recommend_model(
    visual_prompt: str,
    motion_prompt: str = "",
    preferred_model: Optional[str] = None,
    bible_camera_specs: Optional[dict] = None,
) -> dict:
    """
    Recommend the best animation model for a given scene.

    Returns:
        {
            "model": "model-id",
            "display_name": "Model Name",
            "mode": "std|pro",
            "confidence": 0.0-1.0,
            "reasoning": "Why this model was chosen",
            "alternatives": [{"model": ..., "score": ...}],
        }
    """
    signals = analyze_scene(visual_prompt, motion_prompt)

    if not signals:
        # No strong signals — use preferred or default
        model_id = preferred_model or settings.SEEDANCE_VIDEO_MODEL
        profile = MODEL_PROFILES.get(model_id, {})
        return {
            "model": model_id,
            "display_name": profile.get("display_name", model_id),
            "mode": profile.get("default_mode", "std"),
            "confidence": 0.5,
            "reasoning": "No strong scene signals detected — using default model",
            "alternatives": [],
        }

    # Score each model
    scores = {}
    for model_id, profile in MODEL_PROFILES.items():
        score = 0
        for signal, weight in signals.items():
            if signal in profile["strengths"]:
                score += weight * 2
            if signal in profile["weaknesses"]:
                score -= weight * 1.5
        scores[model_id] = score

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_id, best_score = ranked[0]
    best_profile = MODEL_PROFILES[best_id]

    # If preferred model is close enough to best, honor user preference
    if preferred_model and preferred_model in scores:
        pref_score = scores[preferred_model]
        if pref_score >= best_score * 0.7:
            best_id = preferred_model
            best_profile = MODEL_PROFILES.get(preferred_model, {})
            best_score = pref_score

    top_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)[:3]
    reasoning = f"Detected: {', '.join(s for s, _ in top_signals)}. " \
                f"Best match: {best_profile.get('display_name', best_id)} (strengths align with scene content)"

    alternatives = [
        {"model": mid, "display_name": MODEL_PROFILES[mid].get("display_name", mid), "score": round(sc, 2)}
        for mid, sc in ranked[1:3] if sc > 0
    ]

    return {
        "model": best_id,
        "display_name": best_profile.get("display_name", best_id),
        "mode": best_profile.get("default_mode", "std"),
        "confidence": min(1.0, max(0.3, best_score / 6)),
        "reasoning": reasoning,
        "alternatives": alternatives,
    }


def estimate_credits(scenes: list, model_overrides: Optional[dict] = None) -> dict:
    """
    Estimate total credit cost for a production run.
    Returns per-scene and total estimates.
    """
    cost_map = {"high": 3.0, "medium": 2.0, "low": 1.0}
    total = 0.0
    per_scene = []

    for i, scene in enumerate(scenes):
        model_id = (model_overrides or {}).get(str(i), settings.SEEDANCE_VIDEO_MODEL)
        profile = MODEL_PROFILES.get(model_id, {})
        cost = cost_map.get(profile.get("cost_tier", "medium"), 2.0)
        total += cost
        per_scene.append({"scene": i + 1, "model": model_id, "credits": cost})

    return {"total_credits": total, "per_scene": per_scene, "scene_count": len(scenes)}
