from sqlalchemy import Column, String, Integer, BigInteger, Numeric, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.session import Base

class ResearchJob(Base):
    __tablename__ = 'research_jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20))
    genre_topic = Column(Text, nullable=False)
    expanded_queries = Column(JSONB)
    filters = Column(JSONB)
    top_n = Column(Integer, default=10)
    gemini_model = Column(String(100))
    error_message = Column(Text)
    research_summary = Column(Text)
    research_brief = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class ResearchVideo(Base):
    __tablename__ = 'research_videos'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('research_jobs.id'))
    video_id = Column(String(50))
    title = Column(Text)
    channel = Column(String)
    published_at = Column(DateTime(timezone=True))
    views = Column(BigInteger)
    likes = Column(BigInteger)
    duration_seconds = Column(Integer)
    description = Column(Text)
    thumbnail_url = Column(Text)
    url = Column(Text)
    relevance_score = Column(Integer)
    gemini_reasoning = Column(Text)
    selected_for_curation = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CurationJob(Base):
    __tablename__ = 'curation_jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_job_id = Column(UUID(as_uuid=True), ForeignKey('research_jobs.id'))
    status = Column(String(20))
    selected_video_ids = Column(JSONB)
    creative_brief = Column(JSONB)
    user_approved_brief = Column(JSONB)
    num_scenes = Column(Integer)
    image_model = Column(String(50))
    video_model = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))

class ProductionJob(Base):
    __tablename__ = 'production_jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curation_job_id = Column(UUID(as_uuid=True), ForeignKey('curation_jobs.id'))
    status = Column(String(30))
    job_dir = Column(Text)
    num_tracks = Column(Integer)
    num_scenes = Column(Integer)
    concatenated_audio_path = Column(Text)
    beat_timestamps = Column(JSONB)
    assembled_video_path = Column(Text)
    final_video_path = Column(Text)
    youtube_video_id = Column(Text)
    youtube_title = Column(Text)
    youtube_description = Column(Text)
    youtube_hashtags = Column(Text)
    total_duration_sec = Column(Numeric)
    file_size_bytes = Column(BigInteger)
    error_message = Column(Text)
    celery_task_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True))

class ProductionTrack(Base):
    __tablename__ = 'production_tracks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('production_jobs.id'))
    track_number = Column(Integer)
    song_prompt = Column(Text)
    suno_task_id = Column(String)
    suno_status = Column(String(20))
    title = Column(Text)
    duration_seconds = Column(Numeric)
    audio_url = Column(Text)
    local_audio_path = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProductionScene(Base):
    __tablename__ = 'production_scenes'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('production_jobs.id'))
    scene_number = Column(Integer)
    description = Column(Text)
    image_prompt = Column(Text)
    image_model = Column(String(50))
    image_url = Column(Text)
    local_image_path = Column(Text)
    animation_method = Column(String(30))
    animation_model = Column(String(50))
    animation_decision = Column(JSONB)
    motion_prompt = Column(Text)
    cometapi_task_id = Column(String)
    animation_status = Column(String(20))
    local_video_path = Column(Text)
    duration_seconds = Column(Numeric)
    beat_cut_start_sec = Column(Numeric)
    beat_cut_end_sec = Column(Numeric)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemConfig(Base):
    __tablename__ = 'system_config'
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    description = Column(Text)
    is_secret = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class VideoProductionSkill(Base):
    """
    A tool-agnostic, reusable production skill synthesized from tutorial analysis.
    Stored both here (for querying) and as a SKILL.md file on disk (for Git tracking).
    """
    __tablename__ = 'video_production_skills'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Slug is the unique filesystem-safe identifier, e.g. "multi-shot-camera-coverage"
    slug = Column(String(200), unique=True, nullable=False)
    name = Column(String(200), nullable=False)

    # SKILL.md frontmatter fields
    description = Column(Text)           # triggering description — what + when to use
    skill_body = Column(Text)            # full SKILL.md markdown body

    # Categorisation
    category = Column(String(30))        # music_video | product_brand | asmr | general
    applicable_video_types = Column(JSONB)  # e.g. ["music_video", "product_brand"]
    tags = Column(JSONB)                 # e.g. ["consistency", "camera-angles", "storyboard"]

    # Core reusable content
    prompt_template = Column(Text)       # template with {placeholder} syntax
    example_prompts = Column(JSONB)      # list of verbatim example prompts
    workflow_steps = Column(JSONB)       # ordered step-by-step instructions

    # Tool info kept separate so skill body stays tool-agnostic
    tools_tested_with = Column(JSONB)    # tools where this has been verified

    difficulty = Column(String(20))      # beginner | intermediate | advanced

    # Provenance
    source_video_url = Column(Text)
    source_knowledge_entry_id = Column(UUID(as_uuid=True), ForeignKey('tutorial_knowledge.id'))

    # Quality and usage
    confidence_score = Column(Numeric)   # 0.0–1.0
    usage_count = Column(Integer, default=0)

    # Path to the SKILL.md file written to skills/ on disk
    skill_file_path = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TutorialKnowledgeEntry(Base):
    """
    One row per ingested tutorial video or external resource (Notion page, etc).
    Stores the full Gemini analysis plus mined resources from comments/descriptions.
    """
    __tablename__ = 'tutorial_knowledge'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    youtube_url = Column(Text, nullable=False)
    video_id = Column(String(50))
    # music_video | product_brand | asmr | general
    category = Column(String(30), default='general')
    status = Column(String(20), default='pending')  # pending | analyzing | completed | failed

    # Gemini video analysis output
    gemini_analysis = Column(JSONB)           # full structured JSON from Gemini
    standout_tip = Column(Text)
    exact_prompts = Column(JSONB)             # list of verbatim prompts extracted
    tool_names = Column(JSONB)               # list of AI tools mentioned
    workflow_steps = Column(JSONB)           # ordered workflow sequence
    key_settings = Column(JSONB)             # model params / settings found
    category_specific = Column(JSONB)        # category-focused extraction fields
    full_technique_summary = Column(Text)    # 2-3 para narrative summary

    # Comment + description resource mining
    description_resources = Column(JSONB)    # extracted from video description
    comment_resources = Column(JSONB)        # top resource-bearing comments
    aggregated_resources = Column(JSONB)     # de-duped URL list across both

    # External resource content fetched and parsed (Notion pages, etc.)
    external_resources = Column(JSONB)       # {url: {page_title, prompt_library, ...}}

    error_message = Column(Text)
    gemini_model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
