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
    YOUTUBE_API_KEY: str
    YOUTUBE_CLIENT_ID: str
    YOUTUBE_CLIENT_SECRET: str
    YOUTUBE_REDIRECT_URI: str
    
    # --- Application Settings ---
    CLAUDE_CREATIVE_MODEL: str = "claude-opus-4-6"
    CLAUDE_FAST_MODEL: str = "claude-sonnet-4-6"
    DEFAULT_IMAGE_MODEL: str = "nanobananapro"
    DEFAULT_VIDEO_MODEL: str = "kling-v3"
    
    # Kling 3.0 Direct API (JWT auth)
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""

    # SeeDance 2.0 (via CometAPI)
    SEEDANCE_API_KEY: str = ""
    SEEDANCE_BASE_URL: str = "https://api.cometapi.xyz/v1"

    # OpenAI (GPT-Image-2)
    OPENAI_API_KEY: str = ""

    # Engine defaults
    DEFAULT_VIDEO_ENGINE: str = "kling"      # kling | seedance
    DEFAULT_IMAGE_ENGINE: str = "nanabanana"  # nanabanana | gpt_image_2

    # Feature flags
    STEM_SEPARATION_ENABLED: bool = False   # requires demucs + GPU
    UPSCALING_ENABLED: bool = False          # requires realesrgan binary

    # Local storage for intermediate generation files
    JOB_FILES_DIR: str = "./jobs"

    # FastAPI Secret Key
    SECRET_KEY: str

    # Celery Performance
    CELERY_CONCURRENCY: int = 8

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", "..", "env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
