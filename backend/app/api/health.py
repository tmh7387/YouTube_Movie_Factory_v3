import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
import redis.asyncio as redis
from app.core.config import settings
import httpx

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check the health of the application.
    Checks:
    1. Database connection
    2. Redis connection
    3. CometAPI connectivity / balance check (stub)
    """
    health_status = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown",
        "cometapi": "unknown"
    }
    
    # 1. Check Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "ok"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "error"

    # 2. Check Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        health_status["redis"] = "ok"
        await redis_client.aclose()
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "error"
        
    # 3. Check CometAPI
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://api.cometapi.com/v1/dashboard/billing/subscription",
                headers={"Authorization": f"Bearer {settings.COMETAPI_API_KEY}"}
            )
            if response.status_code == 200:
                health_status["cometapi"] = "ok"
            elif response.status_code == 401:
                health_status["cometapi"] = "unauthorized"
            else:
                health_status["cometapi"] = f"api_error: {response.status_code}"
    except Exception as e:
        health_status["cometapi"] = f"error: {str(e)}"

    return health_status
