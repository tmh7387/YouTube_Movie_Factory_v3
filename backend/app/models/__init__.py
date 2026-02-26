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
