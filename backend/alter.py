"""Add music_url, music_filename, beat_sync_enabled columns to production_jobs."""
import asyncio, sys
sys.path.insert(0, '.')
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def migrate():
    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            ALTER TABLE production_jobs
            ADD COLUMN IF NOT EXISTS music_url TEXT,
            ADD COLUMN IF NOT EXISTS music_filename TEXT,
            ADD COLUMN IF NOT EXISTS beat_sync_enabled BOOLEAN DEFAULT FALSE;
        """))
        await db.commit()
        print("OK: music columns added")

asyncio.run(migrate())
