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

    # --- Ported from neural-frames review: optional feature services ---
    OPENAI_API_KEY: str = ""                 # reference-anchored image generation
    # Model id for the OpenAI images endpoints. Settable because the gpt-image family
    # has moved names more than once; a wrong id here should be a config change, not a
    # code change. gpt-image-2 confirmed working against a live account 2026-08-16.
    OPENAI_IMAGE_MODEL: str = "gpt-image-2"
    # low | medium | high | auto. Measured on a live account: "high" took 112s for one
    # picture, so a 20-scene job would spend over half an hour on stills alone.
    # "medium" is the default because scene stills are only the input to animation —
    # the video model resamples them anyway.
    OPENAI_IMAGE_QUALITY: str = "medium"
    STEM_SEPARATION_ENABLED: bool = False    # requires demucs + GPU
    UPSCALING_ENABLED: bool = False          # requires realesrgan binary

    # --- Higgsfield: the primary generator ---
    # Driven through the CLI (npm i -g @higgsfield/cli), because Higgsfield publishes
    # no HTTP API. A human runs `higgsfield auth login` once per machine; the CLI
    # refreshes the token itself after that. When it is unavailable or a call fails,
    # generation falls back to CometAPI — nothing stops, it just changes supplier.
    HIGGSFIELD_ENABLED: bool = True
    HIGGSFIELD_CLI: str = "higgsfield"
    # Model ids are Higgsfield's own (underscores), NOT the CometAPI names.
    HIGGSFIELD_IMAGE_MODEL: str = "seedream_v5_pro"
    # Reference-anchored stills. Nano Banana Pro is the reference/character model.
    HIGGSFIELD_REFERENCE_IMAGE_MODEL: str = "nano_banana_2"
    HIGGSFIELD_VIDEO_MODEL: str = "seedance_2_5"
    HIGGSFIELD_MAX_REFERENCES: int = 3
    # Passed to the CLI's --wait-timeout. Its own format, e.g. "20m".
    HIGGSFIELD_WAIT_TIMEOUT: str = "20m"
    # Our own ceiling on the subprocess, in seconds. Must exceed the wait timeout.
    HIGGSFIELD_TIMEOUT_SECONDS: float = 1500.0

    # --- Application Settings ---
    CLAUDE_CREATIVE_MODEL: str = "claude-opus-4-6"
    CLAUDE_FAST_MODEL: str = "claude-sonnet-4-6"
    # Image generation (CometAPI SeeDream)
    DEFAULT_IMAGE_MODEL: str = "doubao-seedream-4-0-250828"
    # Video animation models
    DEFAULT_VIDEO_MODEL: str = "kling_video"
    SEEDANCE_VIDEO_MODEL: str = "doubao-seedance-2-0"
    
    # --- QA gate on generated clips ---
    QA_ENABLED: bool = True
    # A character_match or style_match below this marks the scene a failure.
    QA_FAIL_THRESHOLD: float = 0.6

    # --- Job execution ---
    # True keeps today's behaviour: /start runs the pipeline in the web process via
    # BackgroundTasks. Set False in any deployment running `python -m worker`, so the
    # web process only enqueues. Both are safe together — the job claim decides.
    RUN_JOBS_INLINE: bool = True
    # A claimed job whose heartbeat is older than this is treated as abandoned and may
    # be taken over. Must exceed the longest gap between heartbeats, which is one
    # scene animation (CometAPI polls for up to 10 minutes).
    JOB_HEARTBEAT_STALE_SECONDS: int = 900
    # How often the worker looks for claimable work.
    WORKER_POLL_SECONDS: int = 10

    # Local storage for intermediate generation files
    JOB_FILES_DIR: str = "./jobs"
    
    # FastAPI Secret Key
    SECRET_KEY: str

    # --- Supabase Storage (audio file hosting for Seedance beat-sync) ---
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_AUDIO_BUCKET: str = "production-audio"
    # Reference sheets and image-board uploads are PNGs. They cannot go in the audio
    # bucket: it restricts mime types, so every picture upload came back
    # 415 invalid_mime_type. Pictures get their own bucket.
    SUPABASE_ASSET_BUCKET: str = "production-assets"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", "..", "env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
