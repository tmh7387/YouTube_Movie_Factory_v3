from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Movie Factory v3 API",
    description="Backend API for managing video research, curation, and production.",
    version="3.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])

@app.on_event("startup")
async def startup_event():
    logger.info("YouTube Movie Factory API starting up...")
    logger.info(f"Using default image model: {settings.DEFAULT_IMAGE_MODEL}")
    logger.info(f"Using default video model: {settings.DEFAULT_VIDEO_MODEL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("YouTube Movie Factory API shutting down...")
