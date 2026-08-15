from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    
    # --- Core API Keys ---
    COMETAPI_API_KEY: str
    ANTHROPIC_API_KEY: str
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.1-pro-preview"
    
    # --- YouTube API ---
    YOUTUBE_API_KEY: str
    YOUTUBE_CLIENT_ID: str
    YOUTUBE_CLIENT_SECRET: str
    YOUTUBE_REDIRECT_URI: str
    
    # --- Kling 3.0 Direct API ---
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""

    # --- Application Settings ---
    CLAUDE_CREATIVE_MODEL: str = "claude-opus-4-6"
    CLAUDE_FAST_MODEL: str = "claude-sonnet-4-6"
    # Image generation (CometAPI SeeDream)
    DEFAULT_IMAGE_MODEL: str = "doubao-seedream-4-0-250828"
    # Video animation models
    DEFAULT_VIDEO_MODEL: str = "kling_video"
    SEEDANCE_VIDEO_MODEL: str = "doubao-seedance-2-0"
    
    # Local storage for intermediate generation files
    JOB_FILES_DIR: str = "./jobs"
    
    # FastAPI Secret Key
    SECRET_KEY: str

    # --- Supabase Storage (audio file hosting for Seedance beat-sync) ---
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_AUDIO_BUCKET: str = "production-audio"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", "..", "env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
