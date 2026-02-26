# YouTube Movie Factory v3 - Master Task Plan

This document outlines the phased implementation plan for the YouTube Movie Factory v3, a standalone Python/React application using CometAPI as the unified AI gateway.

## Phase 1: Foundation (Core Workspace Setup)
- [ ] Provision environment (Python 3.12, Node 20, Redis, ffmpeg, yt-dlp)
- [ ] Initialize project directories (`/backend`, `/frontend`)
- [ ] Set up Backend:
  - [ ] Create `backend/app/core/config.py` for Pydantic Settings
  - [ ] Set up Neon DB connection and Alembic migrations for 7 tables
  - [ ] Create `tasks/celery_app.py` for Celery & Redis
  - [ ] Implement `GET /api/health`
- [ ] Set up Frontend:
  - [ ] Initialize React 18 + Vite + TypeScript project
  - [ ] Install Tailwind CSS, React Query
  - [ ] Build Settings page (API keys, default models)
- [ ] Verify End-to-End: Health endpoint green, Celery worker starts, CometAPI test succeeds.

## Phase 2: Research Pipeline
- [ ] Backend Services:
  - [ ] `services/youtube.py` (search_videos, get_video_details)
  - [ ] `services/research_filter.py` (duration, relevance, quality filters)
  - [ ] `services/cometapi.py` (Gemini scoring)
  - [ ] `tasks/research.py` (Celery chain tasks)
- [ ] API Endpoints: `POST /api/research/jobs`, `GET` endpoints
- [ ] Frontend React Research Hub:
  - [ ] Genre input form
  - [ ] Ranked video card grid (thumbnail, title, channel, score, reasoning, select)
- [ ] Verify End-to-End: Genre input yields ranked videos with Gemini scores.

## Phase 3: Curation & Creative Brief
- [ ] Backend Services:
  - [ ] `services/ytdlp.py` (extract metadata)
  - [ ] `services/claude.py` (generate_creative_brief)
  - [ ] `tasks/curation.py` (run_briefing_pipeline)
- [ ] API Endpoints: `POST /api/curation/jobs`, `GET` endpoints
- [ ] Frontend React Curation Board:
  - [ ] Selected video tiles
  - [ ] Creative Brief viewer (scene cards, mood tags, animation recommendations)
- [ ] Verify End-to-End: Selected videos generate Claude brief correctly.

## Phase 4: Music + Image Generation
- [ ] Backend Services:
  - [ ] `services/claude.py` (music and image prompts)
  - [ ] `services/cometapi.py` (NanoBananaPro, SeeDream4K)
  - [ ] `services/suno.py` / CometAPI Suno path (create_track, poll)
  - [ ] `services/audio_analysis.py` (extract_beats via librosa)
- [ ] Tasks: Parallel Celery chord for music and images
- [ ] Frontend React Production Studio:
  - [ ] Progress view with live-updating music tracks and scene cards
- [ ] Verify End-to-End: Brief approval triggers parallel music and image generation.

## Phase 5: Animation & Assembly
- [ ] Backend Services:
  - [ ] `services/claude.py` (run_creative_direction)
  - [ ] `services/cometapi.py` (animate_image for Kling3, SeeDance, Wan2.6)
  - [ ] `services/ffmpeg_service.py` (apply_ken_burns, trim_clip, assemble_scenes, merge_audio_video)
  - [ ] `services/audio_analysis.py` (calculate_cut_points)
- [ ] Tasks: `animate_scene` Celery task with animation fallback chain
- [ ] Frontend React Animation Progress: Per-scene status cards
- [ ] Verify End-to-End: Scenes animate, assemble with beat cuts, final video ready.

## Phase 6: Publish & Polish
- [ ] Backend Services:
  - [ ] YouTube OAuth2 flow
  - [ ] `services/youtube.py` (upload_video, publish_video)
  - [ ] `services/claude.py` (generate_seo_metadata)
- [ ] Frontend Dashboard & Library:
  - [ ] YouTube Preview component
  - [ ] Dashboard stats cards, recent jobs feed
  - [ ] Video Library
  - [ ] Analytics view
- [ ] Deployment: Nginx reverse proxy + SSL, systemd services
- [ ] Final Verify End-to-End: Full pipeline execution to published YouTube video.
