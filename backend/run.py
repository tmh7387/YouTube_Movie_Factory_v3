import asyncio
import sys
import uvicorn
import os
import selectors

# Import app factory or instance
from app.main import app

async def start_server():
    config = uvicorn.Config(
        app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    # Ensure we are in the backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting YouTube Movie Factory v3 API with SelectorEventLoop...")
    
    if sys.platform == "win32":
        # Use SelectorEventLoop specifically for psycopg3 compatibility on Windows
        asyncio.run(
            start_server(), 
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
        )
    else:
        asyncio.run(start_server())
