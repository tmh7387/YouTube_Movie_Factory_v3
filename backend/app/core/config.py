from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    
    # --- Task Queue & Broker ---
    REDIS_URL: str
    
    # --- Core API Keys ---
    COMETAPI_API_KEY: str
    ANTHROPIC_API_KEY: str
    
    # --- YouTube API ---
    YOUTUBE_CLIENT_ID: str
    YOUTUBE_CLIENT_SECRET: str
    YOUTUBE_REDIRECT_URI: str
    
    # --- Application Settings ---
    DEFAULT_IMAGE_MODEL: str = "nanobananapro"
    DEFAULT_VIDEO_MODEL: str = "kling3"
    
    # Local storage for intermediate generation files
    JOB_FILES_DIR: str = "./jobs"
    
    # FastAPI Secret Key
    SECRET_KEY: str
    
    # Celery Performance
    CELERY_CONCURRENCY: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
