# YouTube Movie Factory v3

## Overview
A standalone desktop application replacing the n8n workflows for automated YouTube video creation.

## Stage 1 Architecture Setup
See `docs/YouTube_Movie_Factory_v3.docx` for the full technical specifications.

### Running Backend Stack (Python 3.12, FastAPI, Celery, Neon DB)
1. Set up `.env` from `.env.example`
2. `cd backend`
3. `python -m venv venv`
4. `source venv/Scripts/activate` (Windows)
5. `pip install -r requirements.txt`
6. Run server: `uvicorn app.main:app --reload`
7. Run worker: `celery -A tasks.celery_app worker --loglevel=info`

### Running Frontend Stack (React 18, Vite, Tailwind)
1. `cd frontend`
2. `npm install`
3. `npm run dev`
