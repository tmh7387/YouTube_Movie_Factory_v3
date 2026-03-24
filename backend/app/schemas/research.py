"""Pydantic schemas for Research Brief Intake."""

from pydantic import BaseModel
from typing import List, Optional


class FilterOverrides(BaseModel):
    min_duration_sec: Optional[int] = None
    max_duration_sec: Optional[int] = None
    date_after: Optional[str] = None  # "YYYY-MM-DD"
    min_views: Optional[int] = None


class AudioMetadata(BaseModel):
    estimated_bpm: Optional[float] = None
    duration_sec: Optional[float] = None


class ResearchBriefSchema(BaseModel):
    intent_summary: str
    mood: str
    visual_style: str
    audio_character: str
    youtube_search_queries: List[str]
    filter_overrides: FilterOverrides = FilterOverrides()
    negative_constraints: List[str] = []
    reference_image_descriptions: List[str] = []
    audio_metadata: Optional[AudioMetadata] = None


class ResearchBriefResponse(BaseModel):
    research_brief: ResearchBriefSchema
    clarifying_question: Optional[str] = None
    is_complete: bool
