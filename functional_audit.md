# YouTube Movie Factory v3 — Functional Audit

> **Tested**: April 27, 2026 | **Backend**: uvicorn on port 8000 | **Frontend**: Vite on port 5174

---

## Health & Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| **FastAPI Backend** | ✅ Running | Starts cleanly with venv Python, all routes registered |
| **Neon PostgreSQL** | ✅ Connected | Pooled + direct connections both working |
| **Redis** | 🚫 Removed | Fully removed — no longer needed |
| **Celery** | 🚫 Removed | All tasks now use FastAPI BackgroundTasks |
| **Frontend (React/Vite)** | ✅ Running | Serves on port 5174 |

---

## Stage 1: Research (YouTube Discovery + AI Analysis)

| What it does | Status |
|---|---|
| **Creative Brief Intake** — You describe what kind of video you want to make (topic, style, mood). Claude Sonnet processes your input into a structured research brief. | ✅ Working |
| **YouTube Search** — The app searches YouTube for relevant source videos using the YouTube Data API, based on your topic and expanded queries. | ✅ Working |
| **AI Relevance Scoring** — Each found video is scored for relevance by Gemini, with reasoning about why each video matters for your project. | ⚠️ Partial — scoring works but some fields (views, channel, duration) are null in older jobs |
| **Research Summary** — Claude generates a documentary-style research report with executive summary, key points, and 3 narrative angles to choose from. | ✅ Working — verified with real data (e.g., "future spaceships test" job) |

**What you get**: A list of scored YouTube videos plus an AI-written research report with 3 narrative options. You pick the direction before moving to Stage 2.

**Data in DB**: 8 research jobs (1 completed, 1 in-progress, 6 failed due to early testing). The completed job has 5 videos and a rich research summary.

> [!NOTE]
> The YouTube API key and Anthropic API key are both configured and functional. The Gemini scoring model (`gemini-3.1-pro-preview`) is also set.

---

## Stage 2: Curation (Creative Brief + Storyboard)

| What it does | Status |
|---|---|
| **Video Selection** — You pick which YouTube videos from Stage 1 to use as source material. | ✅ Working |
| **Creative Brief Generation** — Claude Opus generates a full creative brief: title, hook, narrative goal, music mood, color palette, and a complete scene-by-scene storyboard. | ✅ Working |
| **Storyboard** — Each scene includes: narration text, visual prompt (for image AI), motion prompt (for video AI), negative prompt, Kling mode (std/pro), target duration, and scene-chaining info. | ✅ Working — verified with 20-scene Persian architecture storyboard |
| **Music Direction** — AI generates a detailed Suno music prompt describing the exact instrumental arrangement, tempo, mood progression, and cultural elements. | ✅ Working |
| **Brief Approval** — You review and approve/edit the brief before production starts. | ✅ Working (UI + backend) |

**What you get**: A production-ready creative package — 20 scenes with exact visual/motion prompts, a music generation prompt, and editorial direction. This is the "blueprint" for the video.

**Data in DB**: 3 curation jobs (1 completed with a beautiful 20-scene storyboard, 2 failed from early testing).

> [!WARNING]
> The creative brief JSON structure in the `ready` curation job uses a `scenes` key with detailed storyboard data, but the frontend `curation.ts` service expects a `storyboard` key. This mismatch may cause issues in the UI display. The backend curation task generates a different schema (`scene_number`, `visual_prompt`, `motion_prompt`, `kling_mode`) than the frontend `StoryboardScene` type (`scene_index`, `narration`, `visual_prompt`, `pacing`, `duration`).

---

## Stage 3: Production (Asset Generation + Assembly)

| What it does | Status |
|---|---|
| **Image Generation** — Takes each scene's visual prompt and generates a still image via CometAPI (SeeDream4K model). | ❌ **Blocked** — CometAPI key returns `unauthorized` |
| **Video Animation** — Takes each generated image and animates it using Kling 3.0 or Wan2.6 models with the motion prompt. | 🟡 Placeholder — `animate_image()` returns a stub, not connected to a real API yet |
| **Music Generation** — Sends the music direction prompt to Suno AI (via CometAPI gateway) for instrumental track generation. | ❌ **Blocked** — Same CometAPI key issue |
| **Beat Analysis** — Analyzes the generated audio to find beat timestamps for scene-cut synchronization. | 🟡 Code exists (`audio_analysis.py`) but not triggered — depends on Suno generating a track first |
| **Video Assembly (ffmpeg)** — Concatenates scene clips with beat-matched cuts, adds narration, overlays music. | 🟡 Not implemented — the assembly pipeline code doesn't exist yet |
| **YouTube Upload** — Publishes the final video with AI-generated title, description, and hashtags. | 🟡 Not implemented — OAuth flow exists but no upload code |

**What you get today**: Nothing — the production pipeline can create job scaffolding (scenes + track rows in DB) but can't execute because:
1. The CometAPI key is invalid/expired
2. The animation endpoint is a placeholder
3. No ffmpeg assembly pipeline exists

**Data in DB**: 0 production jobs.

**Frontend UI**: Has a polished Production Studio page with scene grid, soundtrack player, and progress tracking — but it's all empty state since no jobs have ever run.

> [!CAUTION]
> **CometAPI Key Invalid**: The health endpoint confirms `"cometapi": "unauthorized"`. This key (`sk-DzpCsYr2...`) needs to be replaced with a valid one before image/music generation can work. This blocks the entire Stage 3 pipeline.

---

## Stage 4: Knowledge Ingest (NEW — Tutorial Analyzer)

| What it does | Status |
|---|---|
| **YouTube Tutorial Ingestion** — You submit a YouTube tutorial URL. Gemini 3.1 Pro watches the video and extracts production techniques. | ✅ API ready, ⚠️ untested (no jobs submitted yet) |
| **Technique Extraction** — Category-specific schemas extract: exact prompts, tool names, workflow steps, key settings, and a narrative summary. | ✅ Code complete |
| **Comment/Description Mining** — Scrapes resource links from the video's description and top comments. | ✅ Code complete |
| **Skill Synthesis** — Claude Sonnet synthesizes extracted techniques into reusable, tool-agnostic `SKILL.md` files stored in DB + disk. | ✅ Code complete |
| **Skills Query API** — Production pipeline can query skills by category/video_type and inject relevant techniques into Claude's brief generation. | ✅ API responding (empty — no skills ingested yet) |

**What you get**: An automated learning system. Feed it YouTube tutorials, and it builds a library of reusable production techniques that improve future video briefs.

**Data in DB**: 0 entries (tables just created, no tutorials ingested yet).

**Frontend UI**: ❌ **No UI pages exist** — Knowledge and Skills are API-only. No navigation links, no pages, no frontend service files for these endpoints.

---

## External API Key Status

| Service | Key Configured | Status |
|---------|---------------|--------|
| **Neon PostgreSQL** | ✅ | ✅ Connected and working |
| **Anthropic (Claude)** | ✅ `sk-ant-api03-...` | ✅ Working — powers research summaries & creative briefs |
| **YouTube Data API** | ✅ `AIzaSyBv...` | ✅ Working — video search returns results |
| **Gemini** | ✅ `AIzaSyAv...` | ✅ Configured — used for video scoring + tutorial analysis |
| **CometAPI** | ✅ `sk-DzpCsY...` | ❌ **Unauthorized** — blocks image gen, music gen, video gen |
| **Kling 3.0** | ✅ Access + Secret keys | 🟡 Configured but not yet integrated into animation pipeline |
| **YouTube OAuth** | ✅ Client ID + Secret | 🟡 Configured but upload pipeline not built |

---

## Frontend Pages

| Page | Route | Status | What it shows |
|------|-------|--------|---------------|
| **Dashboard** | `/` | 🟡 Placeholder | Shows "Dashboard Overview" text only |
| **Research** | `/research/*` | ✅ Functional | Full intake form, job list, video cards, research detail view |
| **Curation** | `/curation/*` | ✅ Functional | Brief generation, scene list, approval flow |
| **Production** | `/production/*` | ✅ UI ready | Scene grid + soundtrack player (empty state — no production data) |
| **Settings** | `/settings` | ✅ Functional | App configuration page |
| **Knowledge** | — | ❌ Missing | No page, no route, no nav link |
| **Skills** | — | ❌ Missing | No page, no route, no nav link |

---

## Summary: What Works End-to-End Today

```
✅ WORKING END-TO-END:
   Research → You type a topic → YouTube search + AI scoring + narrative report → Done
   Curation → Select videos → AI creative brief with 20-scene storyboard → Approve → Done

⚠️ PARTIALLY BUILT:
   Knowledge Ingest → Backend API complete, no frontend, untested pipeline
   Production → Job creation works, but zero actual asset generation

❌ BLOCKED:
   Image/Music Generation → CometAPI key expired
   Video Animation → Placeholder code only
   Video Assembly (ffmpeg) → Not built
   YouTube Upload → Not built
```

## Priority Actions

1. **🔑 Replace CometAPI key** — This unblocks the entire Stage 3 pipeline
2. **🖥️ Build Knowledge/Skills UI** — Backend is ready, just needs frontend pages
3. **🎬 Build animation integration** — Connect Kling 3.0 keys to the animation pipeline
4. **🔧 Fix frontend type mismatch** — Curation UI types don't match what the backend returns
5. **📼 Build ffmpeg assembly** — The final video assembly pipeline
