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

from app.api import health, research, curation, production, knowledge, skills
from app.core.config import settings

app = FastAPI(
    title="YouTube Movie Factory v3 API",
    description="Backend API for managing video research, curation, and production.",
    version="3.0.0",
)

# CORS middleware — allow any localhost port for local development
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(curation.router, prefix="/api/curation", tags=["Curation"])
app.include_router(production.router, prefix="/api/production", tags=["Production"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])

@app.on_event("startup")
async def startup_event():
    logger.info("YouTube Movie Factory API starting up...")
    logger.info(f"Using default image model: {settings.DEFAULT_IMAGE_MODEL}")
    logger.info(f"Using default video model: {settings.DEFAULT_VIDEO_MODEL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("YouTube Movie Factory API shutting down...")
