



YouTube Movie Factory
Complete Architecture & Build Plan  —  Version 3.0
Research  ·  Curation  ·  AI Creative Direction  ·  Scene Generation  ·  Animation  ·  Music  ·  Publish
Standalone Python/React Application  —  No n8n  —  CometAPI as Unified AI Gateway
Attribute	Value
Backend	Python 3.12 · FastAPI · Celery + Redis
Frontend	React 18 · TypeScript · Tailwind CSS · React Query
Database	Neon (PostgreSQL 16)
AI Gateway	CometAPI (single API key → 500+ models)
Image Generation	NanoBananaPro (Gemini 3 Pro Image) · SeeDream 4K
img2video — Primary	Kling 3 (Kling-video-3.0-pro via CometAPI)
img2video — Secondary	SeeDance 1.5 Pro · Wan 2.6
Ken Burns (fallback)	ffmpeg-python zoompan filter (local)
Music Generation	Suno V5 via CometAPI (or kie.ai direct)
AI Creative Director	Claude API — scene planning, animation decisions
Research Scoring	Google Gemini via CometAPI
Video Download	yt-dlp (self-hosted)
Video Assembly	ffmpeg-python (local binary) — beat-matched cuts
YouTube Publishing	YouTube Data API v3 (direct)
Deployment	Cloud server · Nginx · systemd · Redis AOF persistence
 
1. The Three-Stage Pipeline — User Journey
The application consists of three sequential stages. Stages 1 and 2 are user-facing with explicit decision points. Stage 3 runs autonomously once the user has made their selections.

Stage 1 — Research & Discovery (User-Driven)
The user enters a music genre, topic, or mood (e.g. 'lofi chill beats', 'ambient forest sounds').
The system searches YouTube, scores videos using Gemini AI, and presents ranked results.
User interaction: Browse scored videos, watch previews, read AI analysis — then SELECT favourites.

Stage 2 — Curation & Creative Briefing (User-Driven)
The user reviews their selected inspiration videos in a 'Curation Board'.
Claude AI analyses the selected videos and generates a Creative Brief:
  · Visual mood, colour palette, scene descriptions
  · Recommended animation style per scene (Ken Burns vs AI animated)
  · Number of scenes and suggested transitions
User interaction: Review the brief, adjust if needed — then APPROVE to launch production.

Stage 3 — Autonomous Production (AI-Driven)
Once approved, the entire production runs without user intervention:
  · Suno generates music tracks  →  Claude generates scene image prompts
  →  CometAPI generates 16:9 scene images  →  CometAPI animates images to video clips
  →  ffmpeg assembles clips with beat-matched cuts  →  Suno audio merged
  →  Claude generates SEO metadata  →  YouTube Data API publishes
User returns to: a published YouTube video with a direct link.

 
2. Detailed Pipeline — Every Step Explained
2.1 Stage 1 — Research & Discovery
Step	What Happens	Python Component	Key API
1	User enters genre/topic/mood in React form	React: ResearchForm.tsx	—
2	POST /api/research/jobs — job created in Neon	FastAPI: api/research.py	Neon DB
3	Celery dispatches search_all_queries task	tasks/research.py	Redis
4	YouTube Data API searched with 3–6 expanded query variants	services/youtube.py: search_videos()	YouTube Data API v3
5	Results split and fetched for full metadata (stats + contentDetails)	services/youtube.py: get_video_details()	YouTube Data API v3
6	Duration converted from ISO-8601 to seconds	services/research_filter.py: parse_duration()	isodate lib
7	Hard filters: min 10K views, 100 likes, post Dec 2023, under 61s	services/research_filter.py: filter_by_quality()	—
8	Duplicate video IDs removed across query results	tasks/research.py: deduplicate()	—
9	Gemini AI scores each video: content quality, engagement, mood fit	services/gemini.py: score_videos()	CometAPI → Gemini
10	Videos sorted descending by score, top-N stored in Neon DB	tasks/research.py: sort_and_store()	Neon DB
11	React dashboard updates — user sees ranked video cards with scores	React: ResearchResults.tsx	FastAPI polling
12	User selects 1–5 favourite videos and clicks 'Use as Inspiration'	React: CurationBoard.tsx	POST /api/curation/jobs

2.2 Stage 2 — Curation & Creative Briefing
Step	What Happens	Python Component	Key API
13	Curation job created in Neon with selected video IDs	FastAPI: api/curation.py	Neon DB
14	yt-dlp fetches video thumbnails and extracts title/description metadata	services/ytdlp.py: extract_metadata()	yt-dlp
15	Claude receives: selected video titles, descriptions, thumbnails, user's genre/mood	services/claude.py: generate_creative_brief()	Anthropic Claude
16	Claude returns structured Creative Brief (JSON):     · Overall visual theme and colour palette     · Number of scenes (user-adjustable)     · Per-scene: description, mood, animation recommendation     · Recommended transitions: beat-matched crossfade     · Music direction for Suno prompts	services/claude.py	Anthropic Claude
17	Creative Brief stored in Neon, displayed to user in React	React: CreativeBrief.tsx	Neon DB
18	User reviews brief — can edit scene count and theme — then clicks Approve	React: CreativeBrief.tsx	POST /api/production/jobs

2.3 Stage 3 — Autonomous Production
Phase A — Music Generation (Parallel with image work)
Step	What Happens	Python Component	Key API
19	Claude generates N Suno music prompts from Creative Brief theme + mood	services/claude.py: generate_music_prompts()	Anthropic Claude
20	Celery group: one create_suno_track task per prompt (parallel)	tasks/production.py: generate_tracks_group()	CometAPI → Suno V5
21	Each track polled every 30s until status=SUCCESS (max 40 retries)	tasks/production.py: poll_suno_status()	CometAPI → Suno
22	Completed audio files downloaded to job directory	services/media.py: download_audio()	httpx
23	Suno audio files concatenated into one long-form audio track	services/ffmpeg_service.py: concatenate_audio()	ffmpeg-python
24	Beat timestamps extracted from concatenated audio using librosa	services/audio_analysis.py: extract_beats()	librosa

Phase B — Scene Image Generation
Step	What Happens	Python Component	Key API
25	For each scene in Creative Brief: Claude generates a detailed 16:9 image prompt	services/claude.py: generate_image_prompts()	Anthropic Claude
26	User's preferred image model selected (NanoBananaPro or SeeDream 4K)	services/cometapi.py: get_image_model()	Config / user pref
27	Celery group: one generate_scene_image task per scene (parallel)	tasks/production.py: generate_images_group()	CometAPI
28a	NanoBananaPro path: POST api.cometapi.com with model=gemini-3-pro-image, ratio=16:9	services/cometapi.py: generate_image()	CometAPI → NanoBananaPro
28b	SeeDream 4K path: POST with model=doubao-seedream-4-0-250828, ratio=16:9	services/cometapi.py: generate_image()	CometAPI → SeeDream4K
29	Generated images downloaded and stored in job directory as scene_01.png etc.	services/media.py: download_image()	httpx

Phase C — AI Creative Direction: Animation Decision Per Scene
Claude as Creative Director
For EACH scene, Claude receives:
  · The generated scene image (base64)
  · The scene description from the Creative Brief
  · The audio beat timestamps for that scene's time window
  · The overall video theme and mood

Claude returns a per-scene animation decision:
  { 'method': 'ai_animation', 'model': 'kling3', 'motion_prompt': '...',
    'duration_sec': 8, 'camera': 'slow push-in' }
  OR:
  { 'method': 'ken_burns', 'direction': 'zoom_in', 'start_scale': 1.0,
    'end_scale': 1.08, 'pan_x': 20, 'duration_sec': 8 }

Fallback rule: if AI animation API fails or times out after 2 retries → Ken Burns automatically.

Phase D — Scene Animation (img2video)
Step	What Happens	Python Component	Key API
30	Claude's animation decisions retrieved from Neon for each scene	tasks/production.py	Neon DB
31	Celery group: one animate_scene task per scene (parallel)	tasks/production.py: animate_scenes_group()	—
32a	AI animation path: POST to CometAPI with selected model + motion prompt + image	services/cometapi.py: animate_image()	CometAPI
32b	Kling 3 model string: kling-video-3.0-pro, duration: scene length, ratio: 16:9	services/cometapi.py	CometAPI → Kling 3
32c	SeeDance 1.5 fallback: bytedance-seedance-1-0-pro, same params	services/cometapi.py	CometAPI → SeeDance
32d	Wan 2.6 second fallback: wan-2-6-pro model string	services/cometapi.py	CometAPI → Wan 2.6
33	Poll animation status every 20s until complete (max 60 retries ~20 min)	tasks/production.py: poll_animation_status()	CometAPI
34	Ken Burns path: ffmpeg zoompan filter applied to still image → video clip	services/ffmpeg_service.py: apply_ken_burns()	ffmpeg-python
35	All scene video clips downloaded to job directory as scene_01.mp4 etc.	services/media.py	httpx

Phase E — Assembly, Merge & Publish
Step	What Happens	Python Component	Key API
36	Beat timestamps from Step 24 used to calculate cut point for each scene clip	services/audio_analysis.py: calculate_cut_points()	librosa
37	Each scene clip trimmed to its beat-matched duration	services/ffmpeg_service.py: trim_clip()	ffmpeg-python
38	Scene clips assembled in order with crossfade dissolve transitions (0.5s)	services/ffmpeg_service.py: assemble_scenes()	ffmpeg-python
39	Assembled video merged with concatenated Suno audio track	services/ffmpeg_service.py: merge_audio_video()	ffmpeg-python
40	Final video: 1920x1080, libx264, AAC audio, -shortest flag	services/ffmpeg_service.py	ffmpeg-python
41	Claude generates YouTube SEO: title, description, hashtags, tags	services/claude.py: generate_seo_metadata()	Anthropic Claude
42	Final MP4 uploaded to YouTube via resumable upload API	services/youtube.py: upload_video()	YouTube Data API v3
43	Video published with Claude-generated metadata	services/youtube.py: publish_video()	YouTube Data API v3
44	Job marked complete in Neon, YouTube URL stored, temp files cleaned	db/crud.py: mark_complete()	Neon DB
45	React dashboard shows: Published ✓ with YouTube link and video thumbnail	React: ProductionDetail.tsx	FastAPI polling

 
3. CometAPI Service — Single Gateway Design
Because CometAPI uses an OpenAI-compatible REST interface, a single Python service class handles all AI model calls. The model string is the only parameter that changes between providers.

3.1 CometAPI Model Reference
Capability	User Selection	CometAPI Model String	Endpoint Pattern
Image Gen — Primary	NanoBananaPro	gemini-3-pro-image (Nano Banana Pro)	POST /v1/images/generations
Image Gen — Secondary	SeeDream 4K	doubao-seedream-4-0-250828	POST /v1/images/generations
img2video — Primary	Kling 3	kling-video-3.0-pro	POST /kling/v1/videos/image2video
img2video — Fallback 1	SeeDance 1.5 Pro	bytedance-seedance-1-0-pro	POST /volc/v3/contents/generations/tasks
img2video — Fallback 2	Wan 2.6	wan-2-6-pro	POST /v1/videos/generations
Music Generation	Suno V5	suno-v5	POST /v1/audio/generations
LLM Research Scoring	Gemini	gemini-1.5-flash	POST /v1/chat/completions
LLM Creative/SEO	Claude (direct)	claude-opus-4-6	Anthropic SDK (direct)

3.2 CometAPI Service Class Structure
# services/cometapi.py
class CometAPIService:
    BASE_URL = 'https://api.cometapi.com'
    def __init__(self, api_key: str):
        self.client = httpx.AsyncClient(
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=120.0)

    async def generate_image(self, prompt: str, model: str,
                             ratio='16:9') -> str:  # returns image URL
        ...

    async def animate_image(self, image_url: str, motion_prompt: str,
                            model: str, duration_sec: int) -> str:  # task_id
        ...

    async def poll_animation(self, task_id: str, model: str) -> dict:
        ...  # returns {status, video_url}

    async def generate_music(self, prompt: str, model='suno-v5') -> str:
        ...  # returns task_id

    async def get_model_for_capability(self, capability: str,
                                        user_pref: str) -> str:
        MODEL_MAP = {
          'image': {'nanobananapro': 'gemini-3-pro-image',
                    'seedream4k': 'doubao-seedream-4-0-250828'},
          'video': {'kling3': 'kling-video-3.0-pro',
                    'seedance': 'bytedance-seedance-1-0-pro',
                    'wan26': 'wan-2-6-pro'},
        }
        return MODEL_MAP[capability][user_pref]

3.3 Animation Fallback Chain
Fallback Logic (in animate_scene Celery task)
1. Try Kling 3 (kling-video-3.0-pro)  →  poll 20s intervals, max 60 retries
   On success: return video clip path
   On timeout or API error after 2 retries:

2. Try SeeDance 1.5 Pro  →  same polling pattern
   On success: return video clip path
   On timeout or API error after 2 retries:

3. Try Wan 2.6  →  same polling pattern
   On success: return video clip path
   On timeout or API error after 2 retries:

4. Ken Burns fallback (local ffmpeg — never fails, completes in seconds)
   Log fallback reason, mark scene.animation_method = 'ken_burns_fallback'

 
4. Complete Neon Database Schema
4.1 research_jobs
id UUID PK DEFAULT gen_random_uuid()
status VARCHAR(20)   -- pending|searching|scoring|completed|failed
genre_topic TEXT NOT NULL           -- user's input: 'lofi chill beats'
expanded_queries JSONB              -- Claude-expanded query variants
filters JSONB                       -- {min_views, min_likes, max_sec, date_after}
top_n INTEGER DEFAULT 10
gemini_model VARCHAR(100)
error_message TEXT
created_at TIMESTAMPTZ DEFAULT NOW(), completed_at TIMESTAMPTZ

4.2 research_videos
id UUID PK, job_id UUID FK, video_id VARCHAR(50)
title TEXT, channel VARCHAR, published_at TIMESTAMPTZ
views BIGINT, likes BIGINT, duration_seconds INTEGER
description TEXT, thumbnail_url TEXT, url TEXT
relevance_score INTEGER, gemini_reasoning TEXT
selected_for_curation BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ
UNIQUE(job_id, video_id)

4.3 curation_jobs
id UUID PK DEFAULT gen_random_uuid()
research_job_id UUID FK REFERENCES research_jobs(id)
status VARCHAR(20)   -- pending|briefing|ready|approved|failed
selected_video_ids JSONB          -- array of research_video IDs
creative_brief JSONB              -- full Claude Creative Brief object
user_approved_brief JSONB         -- user-edited version
num_scenes INTEGER
image_model VARCHAR(50)           -- 'nanobananapro' | 'seedream4k'
video_model VARCHAR(50)           -- 'kling3' | 'seedance' | 'wan26'
created_at TIMESTAMPTZ, approved_at TIMESTAMPTZ

4.4 production_jobs
id UUID PK DEFAULT gen_random_uuid()
curation_job_id UUID FK REFERENCES curation_jobs(id)
status VARCHAR(30)
  -- pending|generating_music|generating_images|animating
  -- assembling|merging|uploading|published|failed
job_dir TEXT                      -- server temp dir path
num_tracks INTEGER, num_scenes INTEGER
concatenated_audio_path TEXT
beat_timestamps JSONB             -- list of beat times in seconds
assembled_video_path TEXT
final_video_path TEXT
youtube_video_id TEXT, youtube_title TEXT
youtube_description TEXT, youtube_hashtags TEXT
total_duration_sec NUMERIC, file_size_bytes BIGINT
error_message TEXT, celery_task_id VARCHAR
created_at TIMESTAMPTZ, published_at TIMESTAMPTZ

4.5 production_tracks
id UUID PK, job_id UUID FK, track_number INTEGER
song_prompt TEXT, suno_task_id VARCHAR
suno_status VARCHAR(20)           -- pending|processing|SUCCESS|failed
title TEXT, duration_seconds NUMERIC
audio_url TEXT, local_audio_path TEXT
error_message TEXT, created_at TIMESTAMPTZ
UNIQUE(job_id, track_number)

4.6 production_scenes
id UUID PK, job_id UUID FK, scene_number INTEGER
description TEXT                  -- from Creative Brief
image_prompt TEXT                 -- Claude-generated image prompt
image_model VARCHAR(50)           -- model used for image gen
image_url TEXT                    -- CometAPI returned URL
local_image_path TEXT
animation_method VARCHAR(30)      -- 'ai_animation'|'ken_burns'|'ken_burns_fallback'
animation_model VARCHAR(50)       -- 'kling3'|'seedance'|'wan26'
animation_decision JSONB          -- full Claude decision object
motion_prompt TEXT
cometapi_task_id VARCHAR
animation_status VARCHAR(20)      -- pending|processing|completed|failed
local_video_path TEXT             -- final animated clip
duration_seconds NUMERIC
beat_cut_start_sec NUMERIC        -- beat-matched start time in final video
beat_cut_end_sec NUMERIC
created_at TIMESTAMPTZ
UNIQUE(job_id, scene_number)

4.7 system_config
key VARCHAR(100) PK, value TEXT (encrypted), description TEXT
is_secret BOOLEAN DEFAULT TRUE, updated_at TIMESTAMPTZ

 
5. Celery Task Architecture
5.1 Stage 1 — Research Chain
run_research_pipeline(job_id)
  |
  ├── search_all_queries(job_id)          # parallel group — one per query variant
  |     └── YouTube Data API search.list()
  |
  ├── fetch_video_details(job_id)          # parallel group — batch YT API calls
  |
  ├── filter_and_deduplicate(job_id)       # hard quality + relevance filters
  |
  ├── score_with_gemini(job_id)            # Gemini via CometAPI — structured JSON score
  |
  └── sort_and_store(job_id)               # sort desc, store top_n in Neon
                                           # → status = 'completed', UI updates

5.2 Stage 2 — Creative Briefing Chain
run_briefing_pipeline(curation_job_id)
  |
  ├── extract_video_metadata(curation_job_id)   # yt-dlp thumbnails + metadata
  |
  └── generate_creative_brief(curation_job_id)  # Claude: full Creative Brief JSON
                                                 # → status = 'ready', UI shows brief

5.3 Stage 3 — Production Chain (Full)
run_production_pipeline(production_job_id)       # CHORD: music + images in parallel
  |
  ├── PARALLEL BRANCH A: Music
  |   ├── generate_music_prompts(job_id)         # Claude → N Suno prompts
  |   └── chord(
  |         group(create_suno_track.s(job_id, i) for i in range(num_tracks)),
  |         on_all_tracks_ready.s(job_id)        # callback
  |       )
  |         └── concatenate_audio_tracks(job_id) # ffmpeg concat
  |         └── extract_beat_timestamps(job_id)  # librosa beat detection
  |
  ├── PARALLEL BRANCH B: Scene Images
  |   ├── generate_image_prompts(job_id)         # Claude → N scene prompts
  |   └── group(
  |         generate_scene_image.s(job_id, scene_id) for each scene
  |       )
  |
  ├── [wait for both A and B complete via chord callback]
  |
  ├── run_creative_direction(job_id)             # Claude reviews each image
  |                                              # decides: AI animate vs Ken Burns
  |
  ├── group(
  |     animate_scene.s(job_id, scene_id)        # parallel — Kling3/SeeDance/Wan26/KB
  |     for each scene
  |   )
  |
  ├── assemble_scenes(job_id)                    # ffmpeg: trim + crossfade transitions
  |                                              # beat-matched cuts from librosa data
  |
  ├── merge_audio_video(job_id)                  # ffmpeg final merge
  |
  ├── generate_seo_metadata(job_id)              # Claude → title/desc/hashtags
  |
  ├── upload_and_publish_youtube(job_id)         # YouTube Data API v3
  |
  └── cleanup_and_complete(job_id)               # delete temp files, set published

 
6. Benchmark: n8n Workflows vs Our Application
This section compares the original n8n workflows against the YouTube Movie Factory. Green rows indicate areas where our app is significantly stronger.

6.1 Feature Comparison
Capability	n8n Workflows	Our Application	Advantage
User Interface	n8n form trigger (basic)	Full React dashboard with real-time progress	Ours ✓
Research Trigger	Manual trigger — no genre input	User enters genre/topic/mood — drives everything	Ours ✓
Query Expansion	Hardcoded 6 queries in Set node	Claude expands user's genre into optimal queries	Ours ✓
Video Scoring	OpenAI rule-based numeric score	Gemini AI with reasoning text per video	Ours ✓
User Curation	Not present — no selection step	Explicit curation board — user selects inspiration	Ours ✓
Creative Brief	Not present	Claude analyses selections → full Creative Brief	Ours ✓ (new)
Scene Image Generation	Not present — uses static background video	NanoBananaPro or SeeDream 4K via CometAPI	Ours ✓ (new)
Animation Style	Not present — static video only	Kling 3 / SeeDance / Wan 2.6 / Ken Burns	Ours ✓ (new)
AI Creative Director	Not present	Claude decides animation method per scene	Ours ✓ (new)
Beat-matched Cuts	Not present — -shortest flag only	librosa beat detection → precise cut points	Ours ✓ (new)
Music Prompts	AI agent (hardcoded 5 songs, ignores input)	Claude generates N prompts, respects user count	Ours ✓
Music Generation	Suno via kie.ai	Suno V5 via CometAPI	Equivalent
Audio Concatenation	ffmpeg-api cloud service (paid per GB)	Local ffmpeg-python (zero extra cost)	Ours ✓
Video Processing	ffmpeg-api cloud service	Local ffmpeg-python	Ours ✓
YouTube Publishing	Blotato intermediary (extra service)	YouTube Data API v3 direct	Ours ✓
Job Persistence	Google Sheets (fragile, row-order dependent)	Neon PostgreSQL (robust, indexed)	Ours ✓
Error Recovery	n8n IF/retry nodes (limited)	Celery retry chains with max_retries + fallbacks	Ours ✓
Parallel Execution	n8n batch processing (sequential batches)	Celery group/chord (true parallel)	Ours ✓
Duplication Bug	Song title duplicated (Tilte_Song bug)	No bug — proper Pydantic model validation	Ours ✓
Track Count Bug	Always generates 5 regardless of input	Respects user's num_tracks exactly	Ours ✓
API Gateway	5 separate services to manage	CometAPI single key for image + video + music	Ours ✓
Deployment	n8n cloud or self-hosted	Cloud server — full control, no per-execution fees	Ours ✓
Cost Model	Per-execution fees (n8n cloud)	Fixed server cost + API usage only	Ours ✓

6.2 Key Improvements Over n8n
Critical Bugs Fixed
•	n8n always generates exactly 5 songs regardless of user input — our app respects num_tracks precisely.
•	n8n duplicates song titles in the Google Sheets log (Tilte_Song concatenated twice) — our Pydantic schemas prevent this.
•	n8n Upload Song node has hardcoded filename ('Cellular DawnCellular Dawn_727') — our service uses dynamic file paths.
•	n8n SEO agent references 'Music Theme' (capital T) but form field is 'Music theme' — our codebase uses consistent naming throughout.
•	n8n background video is a static user-uploaded file — our app generates unique AI scenes per video, creating genuinely original content every time.

Architectural Improvements
•	Google Sheets dependency eliminated — Neon DB provides ACID guarantees, proper indexing, and row-level updates without fragile row_number matching.
•	Blotato intermediary eliminated — direct YouTube Data API v3 integration removes a paid dependency and a potential failure point.
•	ffmpeg-api cloud service eliminated — local ffmpeg-python runs at zero marginal cost and keeps video files on-server (no upload/download round-trips).
•	FetchMedia.io dependency eliminated — yt-dlp handles all video downloading natively in Python.
•	True parallel execution via Celery chord — music generation and image generation run simultaneously rather than sequentially, cutting total production time significantly.
•	Beat-matched assembly — librosa provides frame-accurate beat timestamps so scene cuts align with the music. n8n had no concept of this.

 
7. Environment Variables & Dependencies
7.1 Environment Variables
Variable	Purpose
DATABASE_URL	Neon pooled connection string
DATABASE_URL_DIRECT	Neon direct URL for Alembic migrations only
REDIS_URL	Redis broker URL (redis://localhost:6379/0)
COMETAPI_API_KEY	Single key for all CometAPI models (images, video, music, Gemini)
ANTHROPIC_API_KEY	Claude API — creative brief, prompts, SEO, animation direction
YOUTUBE_CLIENT_ID	Google Cloud Console OAuth2 client ID
YOUTUBE_CLIENT_SECRET	Google Cloud Console OAuth2 client secret
YOUTUBE_REDIRECT_URI	OAuth2 callback URL matching Google Cloud Console
DEFAULT_IMAGE_MODEL	'nanobananapro' or 'seedream4k' (user can override per job)
DEFAULT_VIDEO_MODEL	'kling3' (user can override per job)
JOB_FILES_DIR	Server path for temp files (e.g. /var/ymf/jobs)
SECRET_KEY	App signing key (openssl rand -hex 32)
CELERY_CONCURRENCY	Parallel worker count (recommend: CPU count × 2)

7.2 Python Dependencies (requirements.txt)
Package	Version	Purpose
fastapi	>=0.110	Web framework
uvicorn[standard]	>=0.29	ASGI server
sqlalchemy[asyncio]	>=2.0	Async ORM
psycopg[binary]	>=3.1	Neon PostgreSQL driver
alembic	>=1.13	DB migrations
celery[redis]	>=5.3	Task queue + parallel execution
redis	>=5.0	Redis Python client
httpx	>=0.27	Async HTTP — CometAPI, downloads
pydantic	>=2.0	Data validation
pydantic-settings	>=2.0	Env var management
anthropic	>=0.25	Claude API SDK
google-generativeai	>=0.5	Gemini (backup if not via CometAPI)
google-api-python-client	>=2.120	YouTube Data API v3
google-auth-oauthlib	>=1.2	YouTube OAuth2 flow
yt-dlp	>=2024.4	YouTube metadata + thumbnail extraction
ffmpeg-python	>=0.2	Audio concat, video assembly, Ken Burns
librosa	>=0.10	Beat detection for beat-matched cuts
isodate	>=0.6	ISO 8601 duration parsing
aiofiles	>=23.0	Async file I/O
Pillow	>=10.0	Image file handling and validation
python-multipart	>=0.0.9	File upload support

 
8. Phased Implementation Plan
Phase 1 — Foundation (Week 1)
Goal: Running stack, DB schema, health check, Settings page.
1.	Provision cloud server. Install Python 3.12, Node 20, Redis, ffmpeg, yt-dlp, libsndfile (for librosa).
2.	Initialize Antigravity IDE project. Create /backend and /frontend directories.
3.	Create backend/app/core/config.py — Pydantic Settings loading all env vars.
4.	Create Neon DB. Run pgcrypto extension. Write Alembic migration for all 7 tables.
5.	Create tasks/celery_app.py — Celery init, Redis broker, result backend.
6.	Implement GET /api/health — DB ping, Redis ping, CometAPI balance check.
7.	Initialize React project. Build Settings page — store API keys, default model selections.
8.	Verify: health endpoint green, Celery worker starts, CometAPI test call succeeds.

Phase 2 — Research Pipeline (Week 2)
Goal: Full Stage 1 working — genre input to ranked video cards.
9.	Implement services/youtube.py: search_videos() + get_video_details().
10.	Implement services/research_filter.py: parse_duration(), filter_by_relevance(), filter_by_quality().
11.	Implement services/cometapi.py: Gemini scoring call via CometAPI.
12.	Implement all tasks/research.py Celery chain tasks.
13.	Implement POST /api/research/jobs + GET endpoints.
14.	Build React Research Hub: genre input form + ranked video card grid.
15.	Build video card: thumbnail, title, channel, score, AI reasoning tooltip, Select button.
16.	End-to-end test: enter 'lofi chill' → ranked videos appear with Gemini scores.

Phase 3 — Curation & Creative Brief (Week 3)
Goal: Full Stage 2 — user selects videos, Claude generates Creative Brief.
17.	Implement services/ytdlp.py: extract_metadata() for thumbnails and descriptions.
18.	Implement services/claude.py: generate_creative_brief() — structured JSON output.
19.	Implement tasks/curation.py: run_briefing_pipeline() chain.
20.	Implement POST /api/curation/jobs + GET endpoints.
21.	Build React Curation Board: selected video tiles + 'Generate Brief' button.
22.	Build Creative Brief viewer: scene cards, mood tags, animation recommendations, edit + Approve button.
23.	End-to-end test: select 3 videos → Claude brief appears with scene descriptions and animation plan.

Phase 4 — Music + Image Generation (Week 4)
Goal: Parallel music and scene image generation working.
24.	Implement services/claude.py: generate_music_prompts() + generate_image_prompts().
25.	Implement services/cometapi.py: generate_image() for NanoBananaPro and SeeDream4K.
26.	Implement services/suno.py or CometAPI Suno path: create_track() + poll.
27.	Implement services/audio_analysis.py: extract_beats() using librosa.
28.	Implement parallel Celery chord for music + images (both branches).
29.	Build React Production Studio progress view: music tracks + scene image cards updating live.
30.	End-to-end test: approve brief → music tracks appear + scene images generate.

Phase 5 — Animation & Assembly (Week 5)
Goal: Full animation pipeline — scene clips animated and assembled with beat-matched cuts.
31.	Implement services/claude.py: run_creative_direction() — per-scene animation decision.
32.	Implement services/cometapi.py: animate_image() for Kling3, SeeDance, Wan2.6.
33.	Implement services/ffmpeg_service.py: apply_ken_burns(), trim_clip(), assemble_scenes(), merge_audio_video().
34.	Implement services/audio_analysis.py: calculate_cut_points() using beat timestamps.
35.	Implement animate_scene Celery task with full fallback chain.
36.	Build React scene animation progress: per-scene status cards showing method chosen.
37.	End-to-end test: all scenes animate → ffmpeg assembles with beat cuts → final video ready.

Phase 6 — Publish & Polish (Week 6)
Goal: YouTube publishing, full dashboard, analytics, deployment.
38.	Implement YouTube OAuth2 flow. Implement services/youtube.py: upload_video() + publish_video().
39.	Implement services/claude.py: generate_seo_metadata() for YouTube title/description/hashtags.
40.	Build YouTube Preview component: title, description, hashtag chips before publish.
41.	Build Dashboard: stats cards, recent jobs feed, quick-start buttons.
42.	Build Video Library: all produced videos, filter by status/genre/date.
43.	Build Analytics: jobs over time, success rate, model usage breakdown.
44.	Configure Nginx reverse proxy + SSL. Create systemd services for uvicorn + Celery workers.
45.	Full end-to-end QA: genre input → published YouTube video with correct metadata.

 
9. AI Agent Prompt — Antigravity IDE
Paste this complete prompt at the start of your Antigravity IDE build session.

# ═══════════════════════════════════════════════════════════════
# YOUTUBE MOVIE FACTORY v3 — COMPLETE BUILD PROMPT
# Three-Stage Pipeline: Research → Curation → Production
# Standalone Python/React — No n8n — CometAPI as AI Gateway
# ═══════════════════════════════════════════════════════════════

▶ ROLE
  You are a senior full-stack engineer building the YouTube Movie Factory.
  This is a standalone application — no n8n, no automation middleware.
  CometAPI (api.cometapi.com) is the SINGLE gateway for all AI model calls
  except Claude which uses the Anthropic SDK directly.

▶ THREE-STAGE USER JOURNEY
  Stage 1 — RESEARCH (user-driven):
    User enters genre/topic/mood → YouTube search → Gemini scoring
    → user reviews ranked video cards → selects favourites → moves to Stage 2

  Stage 2 — CURATION (user-driven):
    Claude analyses selected videos → generates Creative Brief JSON:
      {theme, palette, scenes: [{description, animation_recommendation}]}
    User reviews/edits brief → clicks Approve → triggers Stage 3

  Stage 3 — PRODUCTION (autonomous):
    Parallel: [music gen via Suno] + [scene image gen via CometAPI]
    → Claude creative direction: per-scene animation decision
    → Parallel: animate each scene (Kling3 → SeeDance → Wan2.6 → Ken Burns)
    → librosa beat detection → ffmpeg beat-matched assembly
    → Claude SEO metadata → YouTube Data API v3 publish

▶ TECH STACK — STRICT
  Backend : Python 3.12, FastAPI, uvicorn, SQLAlchemy 2.0 async, psycopg3
  Tasks   : Celery 5 + Redis (broker + result backend)
  Database: Neon PostgreSQL (pooled URL for app, direct for Alembic)
  AI Gate : CometAPI — single api_key, single service class
  Claude  : anthropic SDK directly (not via CometAPI)
  Media   : yt-dlp (metadata), ffmpeg-python (assembly), librosa (beats)
  YouTube : google-api-python-client v3 direct (no Blotato)
  Frontend: React 18, TypeScript, Tailwind, React Query, react-hook-form+zod

▶ COMETAPI SERVICE — ONE CLASS, MODEL SWITCHING
  BASE_URL = 'https://api.cometapi.com'
  Auth: Authorization: Bearer {COMETAPI_API_KEY}

  Image generation (NanoBananaPro):
    POST /v1/images/generations
    { model: 'gemini-3-pro-image', prompt: '...', size: '1920x1080' }

  Image generation (SeeDream 4K):
    POST /v1/images/generations
    { model: 'doubao-seedream-4-0-250828', prompt: '...', size: '1920x1080' }

  img2video (Kling 3 — PRIMARY):
    POST /kling/v1/videos/image2video
    { model: 'kling-video-3.0-pro', image: image_url,
      prompt: motion_prompt, duration: sec, aspect_ratio: '16:9' }

  img2video (SeeDance 1.5 — FALLBACK 1):
    POST /volc/v3/contents/generations/tasks
    { model: 'bytedance-seedance-1-0-pro', image: image_url,
      prompt: motion_prompt, duration: sec }

  img2video (Wan 2.6 — FALLBACK 2):
    POST /v1/videos/generations
    { model: 'wan-2-6-pro', image: image_url, prompt: motion_prompt }

  Ken Burns (FINAL FALLBACK — local ffmpeg, never fails):
    ffmpeg zoompan filter: scale=2*iw,zoompan=z='zoom+0.001':d=duration*fps

  Music (Suno V5):
    POST /v1/audio/generations
    { model: 'suno-v5', prompt: music_prompt, instrumental: true }

▶ CLAUDE API PATTERNS
  # Creative Brief generation:
  response = client.messages.create(
    model='claude-opus-4-6', max_tokens=4000,
    system='Return ONLY valid JSON matching CreativeBrief schema. No markdown.',
    messages=[{'role':'user','content': [
      {'type':'text','text': brief_prompt},
      *[{'type':'image','source':{'type':'url','url':thumb}} for thumb in thumbs]
    ]}])

  # Animation decision (per scene):
  response = client.messages.create(
    model='claude-opus-4-6', max_tokens=500,
    system='Return ONLY valid JSON: {method, model, motion_prompt, duration_sec}',
    messages=[{'role':'user','content':[
      {'type':'image','source':{'type':'base64','media_type':'image/png','data':b64}},
      {'type':'text','text': f'Scene: {desc}. Theme: {theme}. Choose animation.'}
    ]}])

▶ BEAT-MATCHED ASSEMBLY PATTERN
  import librosa
  y, sr = librosa.load(audio_path)
  tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
  beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
  # Assign scene cuts at beat_times intervals
  # Each scene clip trimmed to its beat window duration
  # ffmpeg crossfade dissolve: 0.5s between clips

▶ DATABASE — 7 TABLES
  research_jobs, research_videos, curation_jobs,
  production_jobs, production_tracks, production_scenes, system_config
  (Full schema in Section 4 of project plan document)

▶ ANIMATION FALLBACK CHAIN (in animate_scene Celery task)
  1. Try Kling 3 → poll 20s, max 60 retries
  2. On 2 consecutive failures → try SeeDance 1.5 Pro → same polling
  3. On 2 consecutive failures → try Wan 2.6 → same polling
  4. On 2 consecutive failures → Ken Burns via local ffmpeg (instant)
  Log fallback reason. Store animation_method in production_scenes.

▶ REACT POLLING RULES
  Research job   : 10s interval while status IN ['searching','scoring']
  Curation job   : 5s interval while status IN ['briefing']
  Production job : 8s interval while status NOT IN ['published','failed']
  Per-scene cards: show animation_method badge — update live
  Stop all polling when status IN ['completed','published','failed']

▶ ERROR HANDLING — EVERY CELERY TASK
  try:
    ... task logic ...
  except Exception as e:
    await crud.update_job_status(db, job_id, 'failed', str(e))
    logger.error(f'{task_name} failed: {e}', exc_info=True)
    raise  # Celery marks FAILURE

▶ BUILD ORDER
  Phase 1: config, DB, Celery, /api/health, Settings UI
  Phase 2: Research pipeline (YouTube → Gemini scoring → video cards)
  Phase 3: Curation pipeline (video selection → Claude Creative Brief)
  Phase 4: Music + image generation (parallel Celery chord)
  Phase 5: Animation + ffmpeg assembly (beat-matched cuts)
  Phase 6: YouTube publish + Dashboard + Analytics + deployment

  Confirm each phase is fully working before starting the next.
  Ask for clarification before any architectural decision not covered here.


YouTube Movie Factory  ·  Architecture v3.0  ·  Aviation Synergy Co., Ltd.  ·  February 2026
