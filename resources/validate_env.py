import os
import sys

# Define required environment variables for YouTube Movie Factory v3
REQUIRED_VARS = [
    "DATABASE_URL",
    "REDIS_URL",
    "COMETAPI_API_KEY",
    "ANTHROPIC_API_KEY",
    "YOUTUBE_API_KEY",
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REDIRECT_URI"
]

def validate():
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        print(f"[ERROR] Missing required env vars: {', '.join(missing)}")
        print("Copy env/.env.example to env/.env and fill in values.")
        sys.exit(1)
    print("[OK] All required environment variables present.")

if __name__ == "__main__":
    validate()
