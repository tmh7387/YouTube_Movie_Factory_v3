"""
ModelRouter — Smart model selection based on scene analysis.

Analyzes scene prompts to recommend the optimal animation model
based on content characteristics (motion intensity, character focus, etc.)

Model capabilities live in app/services/video_models.py; this module only
scores scenes against them. A user-chosen model always wins — auto-routing
is a suggestion engine, not an override.
"""
import logging
from typing import Optional

from app.services import video_models
from app.services.video_models import VideoModel

logger = logging.getLogger(__name__)

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
    "dialogue": ["says", "speaks", "dialogue", "conversation", "voiceover", "line:", "talking"],
    "native_audio": ["sound design", "diegetic", "ambient sound", "sfx", "soundscape"],
    "long_form": ["one-shot", "long take", "oner", "continuous shot", "extended sequence"],
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


def _candidates(allowed_models: Optional[list[str]] = None) -> list[VideoModel]:
    """Models auto-routing is allowed to pick from."""
    if allowed_models:
        picked = [video_models.resolve(m) for m in allowed_models]
        # resolve() never fails, so drop anything that fell back to the default
        # unless it was genuinely asked for.
        wanted = {(m or "").strip().lower() for m in allowed_models}
        return [m for m in picked if m.id in wanted or m.id in {
            video_models.LEGACY_ALIASES.get(w, w) for w in wanted
        }] or video_models.selectable_models()
    return [m for m in video_models.selectable_models() if video_models.is_configured(m)] \
        or video_models.selectable_models()


def _describe(model: VideoModel) -> dict:
    return {
        "model": model.id,
        "display_name": model.display_name,
        "mode": model.default_mode,
    }


def recommend_model(
    visual_prompt: str,
    motion_prompt: str = "",
    preferred_model: Optional[str] = None,
    bible_camera_specs: Optional[dict] = None,
    lock_preferred: bool = False,
    allowed_models: Optional[list[str]] = None,
) -> dict:
    """
    Recommend the best animation model for a given scene.

    preferred_model  — the user's pick. Honoured outright when lock_preferred is
                       set; otherwise it wins any close-run scoring.
    lock_preferred   — the user explicitly chose this model, so do not route away
                       from it no matter what the scene text says.

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
    if lock_preferred and preferred_model:
        model = video_models.resolve(preferred_model)
        return {
            **_describe(model),
            "confidence": 1.0,
            "reasoning": f"{model.display_name} selected by the user — auto-routing disabled",
            "alternatives": [],
        }

    signals = analyze_scene(visual_prompt, motion_prompt)
    candidates = _candidates(allowed_models)

    if not signals:
        model = video_models.resolve(preferred_model or video_models.default_model_id())
        return {
            **_describe(model),
            "confidence": 0.5,
            "reasoning": "No strong scene signals detected — using default model",
            "alternatives": [],
        }

    # Score each model
    scores: dict[str, float] = {}
    for model in candidates:
        score = 0.0
        for signal, weight in signals.items():
            if signal in model.strengths:
                score += weight * 2
            if signal in model.weaknesses:
                score -= weight * 1.5
        scores[model.id] = score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_id, best_score = ranked[0]
    best = video_models.resolve(best_id)

    # If preferred model is close enough to best, honor user preference
    if preferred_model:
        pref = video_models.resolve(preferred_model)
        if pref.id in scores and scores[pref.id] >= best_score * 0.7:
            best, best_score = pref, scores[pref.id]

    top_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)[:3]
    reasoning = (
        f"Detected: {', '.join(s for s, _ in top_signals)}. "
        f"Best match: {best.display_name} (strengths align with scene content)"
    )

    alternatives = [
        {
            "model": mid,
            "display_name": video_models.resolve(mid).display_name,
            "score": round(sc, 2),
        }
        for mid, sc in ranked[1:3]
        if sc > 0 and mid != best.id
    ]

    return {
        **_describe(best),
        "confidence": min(1.0, max(0.3, best_score / 6)),
        "reasoning": reasoning,
        "alternatives": alternatives,
    }


def recommend_for_storyboard(
    scenes: list[dict],
    model_overrides: Optional[dict] = None,
    preferred_model: Optional[str] = None,
    lock_preferred: bool = False,
) -> list[dict]:
    """
    Recommend a model per scene across a whole storyboard.

    model_overrides maps a scene index (as a string) to a model id, letting a
    user pin individual scenes while the rest auto-route.
    """
    results = []
    for i, scene in enumerate(scenes):
        override = (model_overrides or {}).get(str(i))
        if override:
            model = video_models.resolve(override)
            results.append({
                "scene_index": i,
                **_describe(model),
                "confidence": 1.0,
                "reasoning": "Pinned for this scene by the user",
                "alternatives": [],
            })
            continue

        results.append({
            "scene_index": i,
            **recommend_model(
                visual_prompt=scene.get("visual_prompt", "") or scene.get("description", ""),
                motion_prompt=scene.get("motion_prompt", ""),
                preferred_model=preferred_model,
                lock_preferred=lock_preferred,
            ),
        })
    return results
