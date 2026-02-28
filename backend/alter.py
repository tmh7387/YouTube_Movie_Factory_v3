import asyncio
import sys
import selectors
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = 'postgresql+psycopg://neondb_owner:npg_xAG7znSfdbo0@ep-patient-term-aknmpcmn-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require'

async def run():
    print("Connecting to DB...")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        try:
            print("Adding column research_summary to research_jobs...")
            await conn.execute(text('ALTER TABLE research_jobs ADD COLUMN IF NOT EXISTS research_summary TEXT;'))
            print("Column added successfully.")
        except Exception as e:
            print(f"Error adding column: {e}")

if __name__ == '__main__':
    if sys.platform == "win32":
        asyncio.run(
            run(), 
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
        )
    else:
        asyncio.run(run())
