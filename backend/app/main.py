import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Fix moved to top

from app.api import health, research, curation, production
from app.core.config import settings

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
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(curation.router, prefix="/api/curation", tags=["Curation"])
app.include_router(production.router, prefix="/api/production", tags=["Production"])

@app.on_event("startup")
async def startup_event():
    logger.info("YouTube Movie Factory API starting up...")
    logger.info(f"Using default image model: {settings.DEFAULT_IMAGE_MODEL}")
    logger.info(f"Using default video model: {settings.DEFAULT_VIDEO_MODEL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("YouTube Movie Factory API shutting down...")
