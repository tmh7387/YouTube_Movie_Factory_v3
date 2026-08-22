"""
Model catalogue endpoints — lets the UI show which video models exist, what
each one can do, and whether it is actually usable in this deployment.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import video_models
from app.services.model_router import recommend_model

logger = logging.getLogger(__name__)
router = APIRouter()


class RecommendRequest(BaseModel):
    visual_prompt: str
    motion_prompt: str = ""
    preferred_model: Optional[str] = None


@router.get("/video")
async def list_video_models(include_planned: bool = True):
    """
    Every video model in the registry.

    `selectable` is what the UI should offer; planned models are returned too so
    the roadmap is visible, but they carry status="planned" and configured=False.
    """
    models = list(video_models.MODEL_REGISTRY.values())
    if not include_planned:
        models = [m for m in models if m.is_selectable]

    return {
        "default": video_models.default_model_id(),
        "models": [video_models.as_dict(m) for m in models],
    }


@router.get("/video/{model_id}")
async def get_video_model(model_id: str):
    key = video_models.LEGACY_ALIASES.get(model_id.lower(), model_id.lower())
    model = video_models.MODEL_REGISTRY.get(key)
    if not model:
        raise HTTPException(status_code=404, detail=f"Unknown video model: {model_id}")
    return video_models.as_dict(model)


@router.post("/video/recommend")
async def recommend(req: RecommendRequest):
    """Ask the router which model suits a scene — used by the UI's 'Auto' option."""
    return recommend_model(
        visual_prompt=req.visual_prompt,
        motion_prompt=req.motion_prompt,
        preferred_model=req.preferred_model,
    )
