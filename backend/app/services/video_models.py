"""
Video model registry — the single source of truth for every animation model
the platform can route a scene to.

Everything that used to be scattered across model_router.MODEL_PROFILES,
tasks/production.py's model_mode_map and media_gen_service's name sniffing now
reads from here, so adding a model is one entry in MODEL_REGISTRY plus (if it
speaks a new API) one adapter in media_gen_service.

Each entry describes three separate things — keep them distinct:

  * capability  — what the model can do (durations, modes, audio, references)
  * routing     — what kind of scene it is good/bad at (used by model_router)
  * transport   — which backend actually runs it, and under what identifier

`status` gates whether users may pick a model:
  available  — wired end to end, selectable in the UI
  preview    — adapter exists but needs credentials/verification before use
  planned    — documented target, not callable yet (shown greyed out)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings

# --- Prompt dialects -------------------------------------------------------
# Which prompt grammar a model expects. The skill loader and the Claude prompt
# builders branch on this rather than on substring-matching the model id.
DIALECT_SEEDANCE_2_0 = "seedance-2.0"   # @image refs, "Shot N", no timestamps
DIALECT_SEEDANCE_2_5 = "seedance-2.5"   # @image/@video refs, integer-second timestamps
DIALECT_KLING = "kling"                 # single motion sentence + mode
DIALECT_GENERIC = "generic"             # plain cinematic motion description
DIALECT_MINIMAX_H3 = "minimax-h3"       # integrated_multimodal_description + soundscape fields

# --- Transports ------------------------------------------------------------
TRANSPORT_COMETAPI = "cometapi"         # CometAPI gateway (/v1/videos)
TRANSPORT_BYTEPLUS_ARK = "byteplus_ark" # BytePlus ModelArk contents/generations/tasks
TRANSPORT_MINIMAX_API = "minimax_api"   # MiniMax open platform /v2/video_generation
TRANSPORT_COMFYUI = "comfyui"           # local ComfyUI workflow submission

# --- Generation modes ------------------------------------------------------
MODE_T2V = "t2v"            # text only
MODE_I2V = "i2v"            # first frame (the pipeline's default today)
MODE_FL2V = "fl2v"          # first + last frame
MODE_R2V = "r2v"            # arbitrary image/video/audio references
MODE_EDIT = "edit"          # instruction editing of an existing video
MODE_EXTEND = "extend"      # continue an existing video forward/backward


@dataclass(frozen=True)
class VideoModel:
    id: str                      # our stable internal id — stored on scenes
    display_name: str
    family: str                  # seedance | kling | wan | minimax
    transport: str
    remote_model: str            # identifier the transport expects
    dialect: str
    status: str = "available"

    # capability
    min_duration: int = 4
    max_duration: int = 10
    modes: tuple[str, ...] = (MODE_I2V,)
    native_audio: bool = False
    max_reference_images: int = 0
    max_reference_videos: int = 0
    max_reference_audio: int = 0
    resolutions: tuple[str, ...] = ("720p",)
    ratios: tuple[str, ...] = ("16:9",)
    supports_timestamps: bool = False

    # routing
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    cost_tier: str = "medium"    # low | medium | high
    default_mode: str = "std"    # CometAPI std/pro knob; ignored elsewhere

    notes: str = ""

    @property
    def is_selectable(self) -> bool:
        return self.status in ("available", "preview")


MODEL_REGISTRY: dict[str, VideoModel] = {
    # ---------------------------------------------------------------- Seedance
    "doubao-seedance-2-0": VideoModel(
        id="doubao-seedance-2-0",
        display_name="Seedance 2.0",
        family="seedance",
        transport=TRANSPORT_COMETAPI,
        remote_model="doubao-seedance-2-0",
        dialect=DIALECT_SEEDANCE_2_0,
        status="available",
        max_duration=15,
        modes=(MODE_T2V, MODE_I2V, MODE_FL2V, MODE_R2V),
        native_audio=True,
        max_reference_images=4,
        resolutions=("720p", "1080p"),
        ratios=("16:9", "9:16", "1:1", "4:3", "3:4", "21:9"),
        supports_timestamps=False,
        strengths=("dance", "fast_action", "dynamic_camera", "character_movement", "wide_shot"),
        weaknesses=("subtle_expression",),
        cost_tier="medium",
        notes="Responds to shot numbers, not timestamps. Six fixed output ratios.",
    ),
    "dreamina-seedance-2-5": VideoModel(
        id="dreamina-seedance-2-5",
        display_name="Seedance 2.5",
        family="seedance",
        transport=TRANSPORT_BYTEPLUS_ARK,
        remote_model="dreamina-seedance-2-5-260628",
        dialect=DIALECT_SEEDANCE_2_5,
        status="preview",
        max_duration=30,
        modes=(MODE_T2V, MODE_I2V, MODE_FL2V, MODE_R2V, MODE_EDIT, MODE_EXTEND),
        native_audio=True,
        max_reference_images=30,
        max_reference_videos=10,
        max_reference_audio=10,
        resolutions=("480p", "720p", "1080p"),
        ratios=("16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"),
        supports_timestamps=True,
        strengths=(
            "dance", "fast_action", "dynamic_camera", "character_movement",
            "wide_shot", "cinematic", "dialogue", "long_form",
        ),
        weaknesses=(),
        cost_tier="high",
        notes=(
            "Up to 30s and 50 reference assets. Editing/extension tasks lock ratio "
            "(must send ratio=adaptive) and editing also locks duration (send -1); "
            "prefer output_format=mov for edit and extend."
        ),
    ),
    # ------------------------------------------------------------------ Kling
    "kling-v2-master": VideoModel(
        id="kling-v2-master",
        display_name="Kling v2 Master",
        family="kling",
        transport=TRANSPORT_COMETAPI,
        remote_model=settings.DEFAULT_VIDEO_MODEL,
        dialect=DIALECT_KLING,
        status="available",
        modes=(MODE_I2V, MODE_T2V),
        strengths=("character_closeup", "facial_expression", "slow_motion", "portrait"),
        weaknesses=("fast_action", "wide_landscape"),
        cost_tier="high",
        default_mode="pro",
    ),
    "kling-v1-6": VideoModel(
        id="kling-v1-6",
        display_name="Kling v1.6",
        family="kling",
        transport=TRANSPORT_COMETAPI,
        remote_model=settings.DEFAULT_VIDEO_MODEL,
        dialect=DIALECT_KLING,
        status="available",
        modes=(MODE_I2V, MODE_T2V),
        strengths=("general_purpose", "moderate_motion", "landscape"),
        weaknesses=("complex_character",),
        cost_tier="medium",
        default_mode="std",
    ),
    # -------------------------------------------------------------------- Wan
    "wan-pro": VideoModel(
        id="wan-pro",
        display_name="Wan Pro",
        family="wan",
        transport=TRANSPORT_COMETAPI,
        remote_model="wan_pro",
        dialect=DIALECT_GENERIC,
        status="available",
        max_duration=5,
        modes=(MODE_I2V,),
        strengths=("cinematic", "atmospheric", "slow_reveal", "landscape", "abstract"),
        weaknesses=("fast_action", "dialogue"),
        cost_tier="low",
    ),
    # ---------------------------------------------------------------- MiniMax
    "minimax-h3": VideoModel(
        id="minimax-h3",
        display_name="MiniMax H3 (API)",
        family="minimax",
        transport=TRANSPORT_MINIMAX_API,
        remote_model="MiniMax-H3",
        dialect=DIALECT_MINIMAX_H3,
        status="preview",
        min_duration=4,
        max_duration=15,
        modes=(MODE_T2V, MODE_I2V, MODE_FL2V, MODE_R2V),
        native_audio=True,
        max_reference_images=9,
        max_reference_videos=3,
        max_reference_audio=3,
        resolutions=("768P", "2K"),
        ratios=("adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"),
        supports_timestamps=True,
        strengths=(
            "dialogue", "character_closeup", "facial_expression", "cinematic",
            "atmospheric", "native_audio",
        ),
        weaknesses=("long_form",),
        cost_tier="high",
        notes=(
            "Native stereo audio at 32kHz. Keyframe and reference roles are mutually "
            "exclusive in one request. Text-to-video must name a concrete ratio; "
            "image-to-video always resolves to adaptive."
        ),
    ),
    "minimax-h3-local": VideoModel(
        id="minimax-h3-local",
        display_name="MiniMax H3 (local ComfyUI)",
        family="minimax",
        transport=TRANSPORT_COMFYUI,
        remote_model="MiniMax-H3",
        dialect=DIALECT_MINIMAX_H3,
        status="planned",
        min_duration=4,
        max_duration=15,
        modes=(MODE_T2V, MODE_I2V, MODE_FL2V, MODE_R2V),
        native_audio=True,
        max_reference_images=9,
        max_reference_videos=3,
        max_reference_audio=3,
        resolutions=("768P",),
        ratios=("adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"),
        supports_timestamps=True,
        strengths=("dialogue", "character_closeup", "cinematic", "native_audio"),
        weaknesses=("long_form",),
        cost_tier="low",
        notes=(
            "Self-hosted H3-Base only — 768p, no H3-Regenerate-2K. Needs the "
            "Context-IR prompt rewrite done locally (see the H3 prompt reference) "
            "or via the hosted Context-IR API. See docs/MINIMAX_H3_INTEGRATION_PLAN.md."
        ),
    ),
}

# Legacy ids that used to be written to production_scenes.animation_model or
# curation_jobs.video_model before this registry existed.
LEGACY_ALIASES: dict[str, str] = {
    "kling-v3": "kling-v2-master",
    "kling_video": "kling-v2-master",
    "seedance": "doubao-seedance-2-0",
    "seedance-2-0": "doubao-seedance-2-0",
    "doubao-seedance-2-5": "dreamina-seedance-2-5",
    "seedance-2-5": "dreamina-seedance-2-5",
    "dreamina-seedance-2-5-260628": "dreamina-seedance-2-5",
    "minimax-h3-api": "minimax-h3",
    "wan_pro": "wan-pro",
}


def resolve(model_id: Optional[str]) -> VideoModel:
    """Look up a model by id, tolerating legacy aliases and casing.

    Falls back to the configured default rather than raising — a stale id on an
    old scene row must not take down a production run.
    """
    key = (model_id or "").strip().lower()
    key = LEGACY_ALIASES.get(key, key)
    model = MODEL_REGISTRY.get(key)
    if model:
        return model
    return MODEL_REGISTRY[default_model_id()]


def is_known(model_id: Optional[str]) -> bool:
    """True when `model_id` names a real registry entry (or a legacy alias of one)."""
    key = (model_id or "").strip().lower()
    return LEGACY_ALIASES.get(key, key) in MODEL_REGISTRY


def default_model_id() -> str:
    """The model used when the user expresses no preference."""
    configured = (settings.DEFAULT_ANIMATION_MODEL or "").strip().lower()
    configured = LEGACY_ALIASES.get(configured, configured)
    if configured in MODEL_REGISTRY:
        return configured
    return "doubao-seedance-2-0"


def selectable_models() -> list[VideoModel]:
    """Models a user may actually pick, most capable families first."""
    order = {"seedance": 0, "minimax": 1, "kling": 2, "wan": 3}
    return sorted(
        (m for m in MODEL_REGISTRY.values() if m.is_selectable),
        key=lambda m: (order.get(m.family, 9), m.display_name),
    )


def as_dict(model: VideoModel) -> dict:
    """Serialise a model for the API / UI."""
    return {
        "id": model.id,
        "display_name": model.display_name,
        "family": model.family,
        "status": model.status,
        "transport": model.transport,
        "dialect": model.dialect,
        "min_duration": model.min_duration,
        "max_duration": model.max_duration,
        "modes": list(model.modes),
        "native_audio": model.native_audio,
        "max_reference_images": model.max_reference_images,
        "max_reference_videos": model.max_reference_videos,
        "max_reference_audio": model.max_reference_audio,
        "resolutions": list(model.resolutions),
        "ratios": list(model.ratios),
        "supports_timestamps": model.supports_timestamps,
        "strengths": list(model.strengths),
        "weaknesses": list(model.weaknesses),
        "cost_tier": model.cost_tier,
        "default_mode": model.default_mode,
        "notes": model.notes,
        "configured": is_configured(model),
    }


def is_configured(model: VideoModel) -> bool:
    """Whether the credentials/endpoint this model's transport needs are present."""
    if model.transport == TRANSPORT_COMETAPI:
        return bool(settings.COMETAPI_API_KEY)
    if model.transport == TRANSPORT_BYTEPLUS_ARK:
        return bool(settings.ARK_API_KEY)
    if model.transport == TRANSPORT_MINIMAX_API:
        return bool(settings.MINIMAX_API_KEY)
    if model.transport == TRANSPORT_COMFYUI:
        return bool(settings.COMFYUI_BASE_URL)
    return False


def clamp_duration(model: VideoModel, duration: int) -> int:
    """Keep a requested duration inside what the model actually accepts."""
    return max(model.min_duration, min(model.max_duration, int(duration)))
