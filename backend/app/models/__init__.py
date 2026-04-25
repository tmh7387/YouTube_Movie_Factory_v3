from sqlalchemy import Column, String, Integer, BigInteger, Numeric, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
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
    status = Column(String(20))  # pending | briefing | ready | approved | failed
    selected_video_ids = Column(JSONB)
    creative_brief = Column(JSONB)
    user_approved_brief = Column(JSONB)
    num_scenes = Column(Integer)
    image_model = Column(String(50), default='nanabananapro')
    video_model = Column(String(50), default='kling-v3')
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))

class ProductionJob(Base):
    __tablename__ = 'production_jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curation_job_id = Column(UUID(as_uuid=True), ForeignKey('curation_jobs.id'))
    status = Column(String(30))  # pending | generating_music | generating_images | animating | assembling | merging | uploading | published | failed
    job_dir = Column(Text)
    num_tracks = Column(Integer, default=2)
    num_scenes = Column(Integer)
    audio_duration_sec = Column(Numeric)
    beat_timestamps = Column(JSONB)
    beat_interval_sec = Column(Numeric)
    tempo_bpm = Column(Numeric)
    concatenated_audio_path = Column(Text)
    assembled_video_path = Column(Text)
    final_video_path = Column(Text)
    youtube_video_id = Column(Text)
    youtube_title = Column(Text)
    youtube_description = Column(Text)
    youtube_hashtags = Column(Text)
    total_duration_sec = Column(Numeric)
    file_size_bytes = Column(BigInteger)
    error_message = Column(Text)
    celery_task_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True))

class ProductionTrack(Base):
    __tablename__ = 'production_tracks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('production_jobs.id'))
    track_number = Column(Integer, nullable=False)
    song_prompt = Column(Text)
    suno_task_id = Column(String(255))
    suno_status = Column(String(20), default='pending')  # pending | processing | succeed | failed
    title = Column(Text)
    duration_seconds = Column(Numeric)
    audio_url = Column(Text)
    local_audio_path = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('job_id', 'track_number'),)

class ProductionScene(Base):
    """
    Core scene table — includes all fields for Creative Brief,
    image generation, Kling animation, and beat-matched timing.
    Matches guide §2.4 exactly.
    """
    __tablename__ = 'production_scenes'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('production_jobs.id'))
    scene_number = Column(Integer, nullable=False)

    # Creative Brief fields (populated by Stage 2)
    description = Column(Text)
    lyric_or_timestamp = Column(Text)
    target_duration_sec = Column(Numeric)
    animation_method = Column(String(30), default='kling')  # kling | ken_burns | ken_burns_fallback

    # Kling model selection (set by Claude in creative direction)
    kling_model = Column(String(30), default='kling-v3')
    kling_mode = Column(String(10), default='std')  # std | pro
    image_tail_scene_id = Column(UUID(as_uuid=True), ForeignKey('production_scenes.id'), nullable=True)

    # Image generation
    image_prompt = Column(Text)
    image_model = Column(String(50))
    image_url = Column(Text)
    local_image_path = Column(Text)
    image_b64_path = Column(Text)

    # Animation
    motion_prompt = Column(Text)
    negative_prompt = Column(Text)
    kling_request_dur = Column(Integer)
    kling_task_id = Column(String(255))
    kling_status = Column(String(20), default='pending')  # pending | submitted | processing | succeed | failed
    raw_video_url = Column(Text)
    raw_video_path = Column(Text)
    local_video_path = Column(Text)

    # Beat-matched timing
    beat_start_sec = Column(Numeric)
    beat_end_sec = Column(Numeric)
    beat_duration_sec = Column(Numeric)
    beat_drift_ms = Column(Numeric)

    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('job_id', 'scene_number'),)

class SystemConfig(Base):
    __tablename__ = 'system_config'
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    description = Column(Text)
    is_secret = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
