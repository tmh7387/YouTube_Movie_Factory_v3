# YouTube Movie Factory v3 — Stage 2 & Stage 3 Implementation Guide
### Complete Technical Reference for AI Agent Implementation in Google Antigravity
**Aviation Synergy Co., Ltd. · April 2026 · Version 1.0**

---

## Role & Purpose

You are a senior full-stack engineer implementing **Stages 2 and 3** of the YouTube Movie Factory (YMF v3) — a standalone Python/React application that automatically produces and publishes AI-generated music videos to YouTube.

This guide is self-contained. Follow every specification exactly. Ask for clarification only when a decision is not covered here.

**Stage 2** (Curation & Creative Briefing) is user-driven: the user reviews curated inspiration videos, Claude analyses them and generates a structured Creative Brief, and the user approves before production begins.

**Stage 3** (Autonomous Production) runs without user intervention from approval through to a published YouTube video.

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Database Schema — Stages 2 & 3](#2-database-schema)
3. [Stage 2 — Curation & Creative Briefing](#3-stage-2)
4. [Stage 3 — Autonomous Production Overview](#4-stage-3-overview)
5. [Phase A — Music Generation (Suno)](#5-phase-a-music)
6. [Phase B — Scene Image Generation](#6-phase-b-images)
7. [Phase C — AI Creative Direction (Claude)](#7-phase-c-direction)
8. [Phase D — Scene Animation (Kling 3.0)](#8-phase-d-animation)
9. [Phase E — Beat-Matched Assembly (FFmpeg + librosa)](#9-phase-e-assembly)
10. [Phase F — SEO & YouTube Publish](#10-phase-f-publish)
11. [Celery Task Architecture](#11-celery-tasks)
12. [Service Class Implementations](#12-services)
13. [FastAPI Endpoints](#13-endpoints)
14. [React Frontend — Polling & UI Rules](#14-frontend)
15. [Error Handling & Fallback Chain](#15-error-handling)
16. [Environment Variables & Dependencies](#16-environment)
17. [Build Order](#17-build-order)

---

## 1. Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 · FastAPI · uvicorn |
| Task Queue | Celery 5 + Redis (broker + result backend) |
| Database | Neon PostgreSQL 16 (pooled + direct URLs) |
| ORM | SQLAlchemy 2.0 async + psycopg3 |
| Image-to-Video | **Kling 3.0 direct API** (api.klingai.com) — JWT auth |
| Image Generation | NanaBanana Pro (gemini-3-pro-image) via CometAPI |
| Music Generation | Suno V5 via CometAPI |
| AI Director | Claude API (anthropic SDK) — claude-opus-4-6 |
| Beat Detection | librosa 0.11+ |
| Video Assembly | ffmpeg-python (local binary) |
| YouTube | YouTube Data API v3 (direct OAuth2) |
| Frontend | React 18 · TypeScript · Tailwind CSS · React Query |

---

## 2. Database Schema

### 2.1 `curation_jobs`

```sql
CREATE TABLE curation_jobs (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_job_id      UUID REFERENCES research_jobs(id),
    status               VARCHAR(20) NOT NULL DEFAULT 'pending',
                         -- pending | briefing | ready | approved | failed
    selected_video_ids   JSONB,           -- array of research_video UUIDs
    creative_brief       JSONB,           -- full Creative Brief object (see §3.4)
    user_approved_brief  JSONB,           -- user-edited version if modified
    num_scenes           INTEGER,
    image_model          VARCHAR(50) DEFAULT 'nanabananapro',
    video_model          VARCHAR(50) DEFAULT 'kling-v3',
    error_message        TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    approved_at          TIMESTAMPTZ
);
```

### 2.2 `production_jobs`

```sql
CREATE TABLE production_jobs (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curation_job_id          UUID REFERENCES curation_jobs(id),
    status                   VARCHAR(30) NOT NULL DEFAULT 'pending',
                             -- pending | generating_music | generating_images
                             -- animating | assembling | merging | uploading
                             -- published | failed
    job_dir                  TEXT,                -- server temp directory
    num_tracks               INTEGER DEFAULT 2,
    num_scenes               INTEGER,
    audio_duration_sec       NUMERIC,             -- populated after music concat
    beat_timestamps          JSONB,               -- librosa beat time array
    beat_interval_sec        NUMERIC,             -- seconds per beat
    tempo_bpm                NUMERIC,
    concatenated_audio_path  TEXT,
    assembled_video_path     TEXT,
    final_video_path         TEXT,
    youtube_video_id         TEXT,
    youtube_title            TEXT,
    youtube_description      TEXT,
    youtube_hashtags         TEXT,
    total_duration_sec       NUMERIC,
    file_size_bytes          BIGINT,
    error_message            TEXT,
    celery_task_id           VARCHAR(255),
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    published_at             TIMESTAMPTZ
);
```

### 2.3 `production_tracks`

```sql
CREATE TABLE production_tracks (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id             UUID REFERENCES production_jobs(id),
    track_number       INTEGER NOT NULL,
    song_prompt        TEXT,
    suno_task_id       VARCHAR(255),
    suno_status        VARCHAR(20) DEFAULT 'pending',
                       -- pending | processing | succeed | failed
    title              TEXT,
    duration_seconds   NUMERIC,
    audio_url          TEXT,
    local_audio_path   TEXT,
    error_message      TEXT,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, track_number)
);
```

### 2.4 `production_scenes` *(core — includes all animation fields)*

```sql
CREATE TABLE production_scenes (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id                  UUID REFERENCES production_jobs(id),
    scene_number            INTEGER NOT NULL,

    -- Creative Brief fields (populated by Stage 2)
    description             TEXT,
    lyric_or_timestamp      TEXT,
    target_duration_sec     NUMERIC,           -- Claude-assigned beat target
    animation_method        VARCHAR(30) DEFAULT 'kling',
                            -- 'kling' | 'ken_burns' | 'ken_burns_fallback'

    -- Kling model selection (set by Claude in creative direction)
    kling_model             VARCHAR(30) DEFAULT 'kling-v3',
    kling_mode              VARCHAR(10) DEFAULT 'std',
                            -- 'std' or 'pro'
    image_tail_scene_id     UUID REFERENCES production_scenes(id),
                            -- FK to the scene whose image is used as last frame

    -- Image generation
    image_prompt            TEXT,
    image_model             VARCHAR(50),
    image_url               TEXT,
    local_image_path        TEXT,
    image_b64_path          TEXT,              -- path to pre-processed base64 JPEG

    -- Animation
    motion_prompt           TEXT,
    negative_prompt         TEXT,
    kling_request_dur       INTEGER,           -- duration sent to Kling API (ceil of beat target)
    kling_task_id           VARCHAR(255),      -- saved immediately after submission
    kling_status            VARCHAR(20) DEFAULT 'pending',
                            -- pending | submitted | processing | succeed | failed
    raw_video_url           TEXT,
    raw_video_path          TEXT,              -- downloaded from Kling
    local_video_path        TEXT,              -- after trim + normalize

    -- Beat-matched timing
    beat_start_sec          NUMERIC,           -- absolute start in final video
    beat_end_sec            NUMERIC,           -- absolute end in final video
    beat_duration_sec       NUMERIC,           -- exact beat-matched duration
    beat_drift_ms           NUMERIC,           -- actual - target in ms

    error_message           TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, scene_number)
);
```

### 2.5 `system_config`

```sql
CREATE TABLE system_config (
    key          VARCHAR(100) PRIMARY KEY,
    value        TEXT,                    -- encrypt at application layer
    description  TEXT,
    is_secret    BOOLEAN DEFAULT TRUE,
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. Stage 2 — Curation & Creative Briefing

### 3.1 Pipeline Overview

```
User selects inspiration videos (from Stage 1)
        ↓
POST /api/curation/jobs  →  create curation_job (status=pending)
        ↓
Celery: run_briefing_pipeline(curation_job_id)
        ↓
  ├── extract_video_metadata()   — yt-dlp thumbnails + descriptions
  └── generate_creative_brief()  — Claude analyses → structured JSON
        ↓
status = 'ready'  →  React renders Creative Brief for user review
        ↓
User edits (optional) → clicks Approve
        ↓
POST /api/production/jobs  →  create production_job  →  Stage 3 begins
```

### 3.2 `extract_video_metadata` (services/ytdlp.py)

```python
# services/ytdlp.py
import yt_dlp, asyncio, aiofiles, httpx, os
from pathlib import Path

async def extract_metadata(video_ids: list[str], job_dir: str) -> list[dict]:
    """
    Extract title, description, and thumbnail for each selected video.
    Returns list of dicts: {video_id, title, description, thumbnail_url, thumbnail_b64}
    """
    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        for vid in video_ids:
            url = f"https://www.youtube.com/watch?v={vid}"
            ydl_opts = {"quiet": True, "skip_download": True}
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _ydl_extract, url, ydl_opts)

            thumb_url = info.get("thumbnail", "")
            thumb_b64 = ""
            if thumb_url:
                r = await client.get(thumb_url)
                if r.status_code == 200:
                    import base64
                    thumb_b64 = base64.b64encode(r.content).decode()

            results.append({
                "video_id":    vid,
                "title":       info.get("title", ""),
                "description": (info.get("description", "") or "")[:500],
                "thumbnail_url": thumb_url,
                "thumbnail_b64": thumb_b64,
            })
    return results

def _ydl_extract(url, opts):
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
```

### 3.3 Creative Brief JSON Schema

The Creative Brief is the contract between Stage 2 and Stage 3. Claude must return this exact structure.

```json
{
  "theme": "string — overall visual identity and narrative arc",
  "palette": ["#hex1", "#hex2", "#hex3"],
  "mood": "string — 2-4 descriptive words",
  "genre": "string — music genre inferred from inspiration",
  "total_scenes": 20,
  "audio_duration_hint_sec": 95.7,
  "scenes": [
    {
      "scene_number": 1,
      "lyric_or_timestamp": "string — lyric line or timestamp range this covers",
      "description": "string — what happens visually in this scene",
      "motion_prompt": "string — cinematic camera and motion direction for Kling",
      "negative_prompt": "string — what to avoid",
      "target_duration_sec": 4.5,
      "kling_model": "kling-v3",
      "kling_mode": "std",
      "image_tail_scene": null,
      "animation_method": "kling",
      "transition_note": "string or null — why image_tail is used here"
    }
  ],
  "suno_music_direction": {
    "genre": "string",
    "mood": "string",
    "bpm_hint": 92,
    "instruments": ["string"],
    "style_tags": ["string"]
  }
}
```

**Field rules Claude must follow:**

| Field | Rule |
|---|---|
| `target_duration_sec` | Sum of all values must be ≤ `audio_duration_hint_sec - 2.0` |
| `kling_mode` | Must be `"pro"` when `image_tail_scene` is set; `"std"` otherwise |
| `image_tail_scene` | Integer (scene_number of tail source), or `null`. Set when visual continuity between two adjacent scenes adds value |
| `animation_method` | Always `"kling"` from Claude; `"ken_burns_fallback"` is set by the system if Kling fails |
| `kling_model` | Always `"kling-v3"` for v3 API |

### 3.4 `generate_creative_brief` — Claude Prompt (services/claude.py)

```python
# services/claude.py
import anthropic, json

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

BRIEF_SYSTEM = """
You are an AI creative director for short-form music video production.
Return ONLY valid JSON matching the CreativeBrief schema. No markdown fences,
no prose, no explanation — just the raw JSON object.

STRICT RULES for the scenes array:
1. scene_number starts at 1 and increments by 1 with no gaps.
2. Sum of all target_duration_sec values MUST be ≤ (audio_duration_hint_sec - 2.0).
   Distribute time to serve the narrative. Most scenes: 4.0–5.5s.
   Hero shots or key moments: up to 8.0s. Transitions: 3.5–4.5s.
3. When image_tail_scene is set (integer), ALWAYS set kling_mode = "pro".
   When image_tail_scene is null, set kling_mode = "std".
4. image_tail_scene should be used when:
   - A scene transitions INTO the next with visual continuity
     (e.g., a character appearing to enter the next scene's location)
   - The narrative has a dissolve/morph moment
   - A repeated location/character reappears and a visual bridge adds impact
5. motion_prompt must be a specific cinematic instruction:
   camera movement (push-in, pull-out, orbit, pan, dolly, crane),
   speed (slow, ultra-slow, normal),
   and what should be happening visually.
6. negative_prompt must list specific artefacts to avoid
   (e.g., "bright flash, lens flare, face morphing, distortion, watermark").
7. suno_music_direction should reflect the mood and energy of the inspiration videos.
""".strip()

async def generate_creative_brief(
    video_metadata: list[dict],
    genre_mood: str,
    num_scenes: int,
    audio_duration_hint: float
) -> dict:
    """
    Generate a structured Creative Brief from inspiration video metadata.
    """
    # Build content blocks: text description + thumbnail images
    content = []

    intro = (
        f"Genre/mood: {genre_mood}\n"
        f"Number of scenes to plan: {num_scenes}\n"
        f"Audio duration: {audio_duration_hint:.1f}s\n\n"
        f"Inspiration videos:\n"
    )
    for v in video_metadata:
        intro += f"\n- Title: {v['title']}\n  Description: {v['description'][:200]}\n"
    content.append({"type": "text", "text": intro})

    # Include thumbnails as vision input
    for v in video_metadata:
        if v.get("thumbnail_b64"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": v["thumbnail_b64"]
                }
            })

    content.append({
        "type": "text",
        "text": (
            f"Generate a Creative Brief for a {num_scenes}-scene music video. "
            f"Return ONLY the JSON object matching the CreativeBrief schema."
        )
    })

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=6000,
        system=BRIEF_SYSTEM,
        messages=[{"role": "user", "content": content}]
    )

    raw = response.content[0].text.strip()
    # Strip any accidental markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
```

### 3.5 Celery Task: `run_briefing_pipeline`

```python
# tasks/curation.py
from celery import chain
from app.celery_app import celery_app
from app import crud
from services import ytdlp, claude

@celery_app.task(bind=True, max_retries=2)
def run_briefing_pipeline(self, curation_job_id: str):
    try:
        from db.session import SyncSessionLocal
        with SyncSessionLocal() as db:
            job = crud.get_curation_job(db, curation_job_id)
            crud.update_curation_status(db, curation_job_id, "briefing")

            # 1. Extract metadata via yt-dlp
            import asyncio
            video_meta = asyncio.run(
                ytdlp.extract_metadata(job.selected_video_ids, job_dir="")
            )

            # 2. Generate brief via Claude
            brief = asyncio.run(
                claude.generate_creative_brief(
                    video_metadata=video_meta,
                    genre_mood=job.genre_mood or "",
                    num_scenes=job.num_scenes or 20,
                    audio_duration_hint=job.audio_duration_hint or 95.0
                )
            )

            # 3. Store and mark ready
            crud.store_creative_brief(db, curation_job_id, brief)
            crud.update_curation_status(db, curation_job_id, "ready")

    except Exception as e:
        from db.session import SyncSessionLocal
        with SyncSessionLocal() as db:
            crud.update_curation_status(db, curation_job_id, "failed", str(e))
        raise self.retry(exc=e, countdown=10)
```

---

## 4. Stage 3 — Autonomous Production Overview

### 4.1 Full Pipeline Diagram

```
POST /api/production/jobs  (user approves Creative Brief)
            ↓
    create production_job (status=pending)
    create production_scenes rows from brief
            ↓
    run_production_pipeline(production_job_id)
            ↓
    ┌─────────────────────────────┬──────────────────────────────────┐
    │  PARALLEL BRANCH A          │  PARALLEL BRANCH B               │
    │  Music Generation           │  Scene Image Generation          │
    │  ──────────────────         │  ─────────────────────           │
    │  generate_music_prompts()   │  generate_image_prompts()        │
    │       ↓                     │       ↓                          │
    │  Celery group:              │  Celery group:                   │
    │  create_suno_track × N      │  generate_scene_image × N_scenes │
    │       ↓                     │       ↓                          │
    │  poll_suno_status × N       │  download_scene_image × N_scenes │
    │       ↓                     │                                  │
    │  concatenate_audio_tracks() │                                  │
    │       ↓                     │                                  │
    │  extract_beat_timestamps()  │                                  │
    └──────────────┬──────────────┴───────────────────┬─────────────┘
                   │   CHORD callback (both branches done)
                   ↓
          run_creative_direction()    ← Claude reviews each image,
                   ↓                    decides kling_mode per scene,
          Celery group:                  sets image_tail links
          animate_scene × N_scenes
          (Kling 3.0 direct → poll → download → trim+normalize)
                   ↓
          assemble_scenes()          ← beat-matched concat
                   ↓
          merge_audio_video()        ← FFmpeg final encode
                   ↓
          generate_seo_metadata()    ← Claude title/desc/tags
                   ↓
          upload_and_publish()       ← YouTube Data API v3
                   ↓
          cleanup_and_complete()     ← mark published, delete temp
```

### 4.2 Beat-Matching Strategy

Beat-matching ensures every scene cut lands on a musical beat. The flow:

1. After music tracks are generated and concatenated, run `librosa.beat.beat_track()`.
2. Walk through beat/onset boundaries and assign each scene its `beat_start_sec` and `beat_end_sec`.
3. Each scene's `beat_duration_sec` = `beat_end_sec` - `beat_start_sec`.
4. The Kling API is called with `kling_request_dur` = `ceil(beat_duration_sec)`.
5. The downloaded raw clip is **frame-perfectly trimmed** to `beat_duration_sec` using FFmpeg re-encode (see §9.3).
6. All trimmed clips are then normalized and concatenated.

---

## 5. Phase A — Music Generation

### 5.1 Suno via CometAPI

```python
# services/suno.py
import httpx, asyncio

COMET_BASE = "https://api.cometapi.com"
COMET_KEY  = None  # loaded from env: COMETAPI_API_KEY

async def create_track(prompt: str, duration_sec: int = 60) -> str:
    """Submit a Suno V5 music generation task. Returns task_id."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {COMET_KEY}"},
        timeout=30
    ) as client:
        r = await client.post(f"{COMET_BASE}/v1/audio/generations", json={
            "model": "suno-v5",
            "prompt": prompt,
            "instrumental": True,
            "duration": duration_sec,
        })
        r.raise_for_status()
        return r.json()["data"]["task_id"]

async def poll_track(task_id: str, max_retries: int = 40) -> dict:
    """Poll until complete. Returns {status, audio_url, duration_seconds}."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {COMET_KEY}"},
        timeout=30
    ) as client:
        for _ in range(max_retries):
            await asyncio.sleep(30)
            r = await client.get(f"{COMET_BASE}/v1/audio/generations/{task_id}")
            data = r.json().get("data", {})
            status = data.get("status", "processing")
            if status == "SUCCESS":
                return {
                    "status": "succeed",
                    "audio_url": data["audio_url"],
                    "duration_seconds": data.get("duration_seconds", 60),
                }
            if status == "FAILED":
                return {"status": "failed", "error": data.get("error_message")}
        return {"status": "timeout"}
```

### 5.2 Music Prompt Generation (Claude)

```python
# services/claude.py  (addition)

MUSIC_PROMPT_SYSTEM = """
You are a music director. Generate Suno V5 prompts for instrumental background music.
Return ONLY a JSON array of prompt strings. No prose.
Each prompt must include: genre, mood, BPM hint, key instruments, energy level.
Example: "lo-fi hip hop, 90 BPM, chill and nostalgic, vinyl crackle, mellow piano,
warm bass, soft brushed drums, study session energy"
""".strip()

async def generate_music_prompts(brief: dict, num_tracks: int) -> list[str]:
    md = brief.get("suno_music_direction", {})
    prompt = (
        f"Genre: {md.get('genre', brief.get('genre', 'hip hop'))}\n"
        f"Mood: {md.get('mood', brief.get('mood', 'energetic'))}\n"
        f"BPM hint: {md.get('bpm_hint', 90)}\n"
        f"Style tags: {', '.join(md.get('style_tags', []))}\n"
        f"Generate {num_tracks} distinct Suno V5 instrumental prompts."
    )
    response = client.messages.create(
        model="claude-opus-4-6", max_tokens=800,
        system=MUSIC_PROMPT_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    return json.loads(raw)
```

### 5.3 Beat Timestamp Extraction (services/audio_analysis.py)

```python
# services/audio_analysis.py
import librosa
import numpy as np
from pathlib import Path

FADE_BUFFER_SEC = 2.0   # Reserve 2s at end for fade-out

def extract_beats(audio_path: str) -> dict:
    """
    Load audio, detect beats and onsets, return timing metadata.
    """
    y, sr = librosa.load(audio_path, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)

    # Tempo + beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Onset detection for finer grid
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, units='frames', delta=0.05
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # Combined sorted boundary grid
    all_boundaries = np.unique(np.concatenate([beat_times, onset_times]))
    all_boundaries = np.concatenate([[0.0], all_boundaries[all_boundaries > 0.05]])
    all_boundaries = np.sort(all_boundaries).tolist()

    beat_interval = float(60.0 / float(np.squeeze(tempo)))

    return {
        "audio_duration_sec": float(duration),
        "tempo_bpm":          float(np.squeeze(tempo)),
        "beat_interval_sec":  beat_interval,
        "beat_times":         beat_times.tolist(),
        "onset_times":        onset_times.tolist(),
        "all_boundaries":     all_boundaries,
        "usable_duration_sec": float(duration) - FADE_BUFFER_SEC,
    }


def assign_scene_cuts(
    beat_data:      dict,
    scene_targets:  list[dict],   # [{scene_number, target_duration_sec}]
) -> list[dict]:
    """
    Snap each scene's start/end to the nearest beat/onset boundary.

    beat_data:     output of extract_beats()
    scene_targets: ordered list, must sum ≤ usable_duration_sec

    Returns list of dicts with beat_start_sec, beat_end_sec, beat_duration_sec,
    beat_drift_ms for each scene.
    """
    boundaries = np.array(beat_data["all_boundaries"])
    usable     = beat_data["usable_duration_sec"]
    beat_int   = beat_data["beat_interval_sec"]
    tolerance  = beat_int * 1.5

    results   = []
    cursor    = 0.0
    n_scenes  = len(scene_targets)

    for i, scene in enumerate(scene_targets):
        target   = scene["target_duration_sec"]
        ideal_end = cursor + target
        remaining_scenes = n_scenes - i
        # Protect future scenes: each needs at least 3.0s
        max_end = usable - (remaining_scenes - 1) * 3.0

        lo = max(cursor + 3.0, ideal_end - tolerance)
        hi = min(ideal_end + tolerance, max_end)

        candidates = boundaries[(boundaries >= lo) & (boundaries <= hi)]
        if len(candidates) > 0:
            snap = float(candidates[np.argmin(np.abs(candidates - ideal_end))])
        else:
            snap = float(min(ideal_end, max_end))

        snap = round(snap, 4)
        dur  = round(snap - cursor, 4)

        results.append({
            "scene_number":    scene["scene_number"],
            "beat_start_sec":  round(cursor, 4),
            "beat_end_sec":    snap,
            "beat_duration_sec": dur,
            "beat_drift_ms":   round((dur - target) * 1000, 1),
        })
        cursor = snap

    return results
```

---

## 6. Phase B — Scene Image Generation

### 6.1 Image Prompt Generation (Claude)

```python
# services/claude.py  (addition)

IMAGE_PROMPT_SYSTEM = """
You are a visual art director. Given a scene description and overall theme,
generate a detailed image generation prompt optimised for a 16:9 cinematic still.
Return ONLY the prompt string — no JSON, no labels, no explanation.
The prompt must specify: art style, subject, setting, lighting, camera angle,
colour palette, mood. Under 120 words. No negative prompts here.
""".strip()

async def generate_image_prompts(brief: dict) -> list[str]:
    """Generate one image prompt per scene."""
    theme   = brief["theme"]
    palette = ", ".join(brief.get("palette", []))
    prompts = []

    for scene in brief["scenes"]:
        user_msg = (
            f"Theme: {theme}\n"
            f"Palette: {palette}\n"
            f"Scene: {scene['description']}\n"
            f"Mood: {brief.get('mood', '')}\n"
            "Generate a 16:9 cinematic image generation prompt for this scene."
        )
        r = client.messages.create(
            model="claude-opus-4-6", max_tokens=200,
            system=IMAGE_PROMPT_SYSTEM,
            messages=[{"role": "user", "content": user_msg}]
        )
        prompts.append(r.content[0].text.strip())

    return prompts
```

### 6.2 Image Generation via CometAPI (services/cometapi.py)

```python
# services/cometapi.py
import httpx, base64, io
from PIL import Image

COMET_BASE = "https://api.cometapi.com"
COMET_KEY  = None  # loaded from env

MODEL_MAP = {
    "nanabananapro": "gemini-3-pro-image",
    "seedream4k":    "doubao-seedream-4-0-250828",
}

async def generate_image(
    prompt:    str,
    model_key: str = "nanabananapro",
    size:      str = "1920x1080"
) -> str:
    """Generate a 16:9 scene image. Returns URL."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {COMET_KEY}"},
        timeout=120
    ) as client:
        r = await client.post(f"{COMET_BASE}/v1/images/generations", json={
            "model":  MODEL_MAP[model_key],
            "prompt": prompt,
            "size":   size,
            "n": 1,
        })
        r.raise_for_status()
        return r.json()["data"][0]["url"]

async def download_and_prep_image(
    url:     str,
    dst:     str,
    max_dim: int = 1536
) -> str:
    """
    Download image, resize to max_dim, save as high-quality JPEG.
    Returns local path.
    """
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url)
        r.raise_for_status()

    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    img.save(dst, format="JPEG", quality=88)
    return dst
```

### 6.3 Image → Base64 Encoding (services/media.py)

```python
# services/media.py
import base64, io
from PIL import Image

def image_to_b64(path: str, max_dim: int = 1536) -> str:
    """
    Encode image as raw base64 JPEG string.
    CRITICAL: No 'data:image/jpeg;base64,' prefix — Kling rejects it.
    """
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()
```

---

## 7. Phase C — AI Creative Direction

Claude reviews each generated scene image and confirms or adjusts the animation decision made in the Creative Brief. This is particularly important for validating `image_tail` transitions after seeing the actual generated images.

### 7.1 Per-Scene Direction Prompt

```python
# services/claude.py  (addition)

DIRECTION_SYSTEM = """
You are a film director reviewing storyboard frames.
Given a scene image, its description, the overall video theme, and
the beat timestamp window, decide the optimal animation approach.
Return ONLY valid JSON with this exact schema:
{
  "scene_number": int,
  "kling_mode": "std" | "pro",
  "motion_prompt": "string — specific camera + motion direction",
  "negative_prompt": "string — artefacts to avoid",
  "image_tail_confirmed": true | false,
  "reasoning": "string — brief explanation (for logging only)"
}

RULES:
- kling_mode must be "pro" if image_tail_confirmed is true
- motion_prompt should be precise: camera type + direction + speed + subject action
- Always include in negative_prompt: distortion, watermark, face morphing
""".strip()

async def direct_scene(
    scene_image_b64: str,
    scene_desc:      str,
    theme:           str,
    beat_start:      float,
    beat_end:        float,
    has_image_tail:  bool,
) -> dict:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=400,
        system=DIRECTION_SYSTEM,
        messages=[{"role": "user", "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": scene_image_b64
                }
            },
            {
                "type": "text",
                "text": (
                    f"Scene: {scene_desc}\n"
                    f"Theme: {theme}\n"
                    f"Beat window: {beat_start:.2f}s → {beat_end:.2f}s "
                    f"({beat_end - beat_start:.2f}s)\n"
                    f"image_tail planned: {has_image_tail}\n"
                    "Confirm or adjust the animation direction."
                )
            }
        ]}]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    return json.loads(raw)
```

---

## 8. Phase D — Scene Animation (Kling 3.0 Direct)

### 8.1 Authentication — JWT Generation

Kling 3.0 uses JWT (HS256) signed with your Secret Key. Generate a fresh token for every API call — tokens expire after `exp`.

```python
# services/kling.py
import jwt, time, math, requests, json, os
import asyncio, httpx

KLING_BASE  = "https://api.klingai.com"
ACCESS_KEY  = None   # loaded from env: KLING_ACCESS_KEY
SECRET_KEY  = None   # loaded from env: KLING_SECRET_KEY
TOKEN_TTL   = 1800   # 30 minutes

def make_jwt() -> str:
    now = int(time.time())
    payload = {
        "iss": ACCESS_KEY,
        "exp": now + TOKEN_TTL,
        "nbf": now - 5,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {make_jwt()}",
        "Content-Type":  "application/json",
    }
```

### 8.2 Image-to-Video Submission

```python
# services/kling.py  (continued)

def ceil_kling_duration(beat_dur: float) -> int:
    """
    Kling v3 accepts any integer duration 3–15s.
    Request the ceiling of the beat duration to ensure we have enough footage
    to trim to the exact beat point.
    """
    return max(3, min(15, math.ceil(beat_dur)))

async def submit_animation(
    image_b64:       str,
    prompt:          str,
    negative_prompt: str,
    mode:            str,          # "std" or "pro"
    duration_sec:    int,          # integer, 3–15
    image_tail_b64:  str | None = None,
    cfg_scale:       float = 0.5,
) -> str:
    """
    Submit an image-to-video task. Returns task_id.

    CRITICAL: image_b64 and image_tail_b64 must be raw base64 strings —
    NO 'data:image/jpeg;base64,' prefix.
    image_tail is supported by both std and pro modes in kling-v3.
    """
    payload = {
        "model_name":      "kling-v3",
        "mode":            mode,
        "duration":        str(duration_sec),   # must be string, not int
        "image":           image_b64,
        "prompt":          prompt,
        "negative_prompt": negative_prompt,
        "cfg_scale":       cfg_scale,
    }
    if image_tail_b64:
        payload["image_tail"] = image_tail_b64

    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(
            f"{KLING_BASE}/v1/videos/image2video",
            headers=auth_headers(),
            json=payload
        )

    data = r.json()
    if r.status_code not in (200, 201) or data.get("code") != 0:
        raise KlingSubmitError(f"HTTP {r.status_code}: {data}")

    return data["data"]["task_id"]
```

### 8.3 Polling — Correct Response Structure

```python
# services/kling.py  (continued)

class KlingSubmitError(Exception): pass
class KlingPollError(Exception):   pass

# CRITICAL: Kling direct API response structure:
#   data.task_status = "processing" | "succeed" | "failed"   (NOT "IN_PROGRESS"/"SUCCESS")
#   data.task_result.videos[0].url = video download URL

async def poll_animation(
    task_id:     str,
    max_retries: int  = 80,
    interval_sec: int = 20,
) -> dict:
    """
    Poll until complete.
    Returns: {"status": "succeed", "video_url": str}
          or {"status": "failed",  "error":     str}
          or {"status": "timeout"}
    """
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(max_retries):
            await asyncio.sleep(interval_sec)

            r = await client.get(
                f"{KLING_BASE}/v1/videos/image2video/{task_id}",
                headers=auth_headers()
            )
            data = r.json().get("data", {})
            status = data.get("task_status", "unknown")

            if status == "succeed":
                videos = data.get("task_result", {}).get("videos", [])
                if not videos:
                    raise KlingPollError(f"succeed but no videos: {data}")
                return {"status": "succeed", "video_url": videos[0]["url"]}

            if status == "failed":
                return {
                    "status": "failed",
                    "error":  data.get("task_status_msg", "unknown error")
                }
            # still "processing" — continue
    return {"status": "timeout"}
```

### 8.4 Download Raw Clip

```python
# services/kling.py  (continued)

async def download_raw_clip(url: str, dst: str) -> str:
    """Download video file from Kling CDN URL. Returns local path."""
    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(dst, "wb") as f:
                async for chunk in r.aiter_bytes(65536):
                    f.write(chunk)
    return dst
```

### 8.5 Fallback Chain

If Kling fails after retries, the system falls back through:

1. **Kling v3/std** → primary path for all standalone scenes
2. **Kling v3/pro** → primary path for `image_tail` scenes; fallback for std
3. **Ken Burns (FFmpeg)** → local fallback, never fails

```python
# tasks/production.py

async def animate_scene_with_fallback(
    scene:       dict,   # production_scene row as dict
    image_path:  str,
    tail_path:   str | None,
    job_dir:     str,
) -> str:
    """
    Try Kling animation with fallback to Ken Burns.
    Returns path to raw video clip (before trim+normalize).
    """
    from services import kling, ffmpeg_service
    from services.media import image_to_b64

    img_b64  = image_to_b64(image_path)
    tail_b64 = image_to_b64(tail_path) if tail_path else None
    dur_int  = kling.ceil_kling_duration(scene["beat_duration_sec"])
    raw_path = os.path.join(job_dir, f"raw_{scene['scene_number']:02d}.mp4")

    # Attempt 1: Kling (mode from creative direction)
    for mode in [scene["kling_mode"], "pro", "std"]:
        for attempt in range(2):
            try:
                task_id = await kling.submit_animation(
                    image_b64       = img_b64,
                    prompt          = scene["motion_prompt"],
                    negative_prompt = scene["negative_prompt"],
                    mode            = mode,
                    duration_sec    = dur_int,
                    image_tail_b64  = tail_b64,
                )
                # Persist task_id immediately — allows resume on restart
                await crud.update_scene_task_id(scene["id"], task_id)

                result = await kling.poll_animation(task_id)
                if result["status"] == "succeed":
                    await kling.download_raw_clip(result["video_url"], raw_path)
                    await crud.update_scene_kling_status(
                        scene["id"], "succeed", mode_used=mode
                    )
                    return raw_path

            except Exception as e:
                logger.warning(f"Scene {scene['scene_number']} Kling {mode} "
                               f"attempt {attempt+1} failed: {e}")
                await asyncio.sleep(15)

    # All Kling attempts exhausted — Ken Burns fallback
    logger.warning(f"Scene {scene['scene_number']}: falling back to Ken Burns")
    raw_path = ffmpeg_service.apply_ken_burns(
        image_path   = image_path,
        output_path  = raw_path,
        duration_sec = dur_int,
    )
    await crud.update_scene_animation_method(scene["id"], "ken_burns_fallback")
    return raw_path
```

---

## 9. Phase E — Beat-Matched Assembly

### 9.1 Overview

```
For each scene:
  raw_clip (ceil(beat_dur) seconds from Kling)
      ↓
  FRAME-PERFECT TRIM to beat_duration_sec   ← single ffmpeg call with -c:v libx264
  + NORMALIZE to target resolution/fps       (combined with trim, one pass)
      ↓
  norm_clip (exact beat_duration_sec, 1920×1080, 24fps, no audio)

All norm_clips → concat demuxer → raw.mp4 (no audio)
      ↓
Mix with concatenated audio track
      ↓
2-second video + audio fade out
      ↓
final.mp4
```

### 9.2 Target Resolution & Format

| Parameter | Value | Notes |
|---|---|---|
| Resolution | 1920×1080 | Upscale from Kling native or match if larger |
| Frame rate | 24 fps | Constant FPS for concat compatibility |
| Video codec | H.264 (libx264) | CRF 17, preset slow for final |
| Pixel format | yuv420p | Required for broad compatibility |
| Audio codec | AAC 192k | |
| Container | MP4 | |

### 9.3 Frame-Perfect Trim + Normalize (CRITICAL)

Using `-c copy` for trimming is **prohibited** in this pipeline because it snaps to the nearest keyframe, introducing up to 2 seconds of timing error. Always re-encode when trimming.

```python
# services/ffmpeg_service.py
import subprocess, os, json

TARGET_RES = "1920:1080"
TARGET_FPS = "24"

def trim_and_normalize(
    raw_path:      str,
    output_path:   str,
    beat_dur_sec:  float,
    crf:           int = 17,
    preset:        str = "fast",
) -> str:
    """
    Frame-perfect trim to beat_dur_sec AND normalize to TARGET_RES @ TARGET_FPS.
    Combined into a single FFmpeg pass for efficiency.

    Uses -c:v libx264 (re-encode) to achieve frame-accurate duration.
    -c copy is NEVER used here — it snaps to keyframes and breaks beat sync.
    """
    vf = (
        f"scale={TARGET_RES}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_RES}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,"
        f"fps={TARGET_FPS}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i",  raw_path,
        "-t",  f"{beat_dur_sec:.6f}",   # exact duration, 6 decimal places
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-an",                           # no audio at this stage
        output_path,
        "-loglevel", "error"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"trim_and_normalize failed for {os.path.basename(raw_path)}: "
            f"{result.stderr[-300:]}"
        )
    return output_path


def probe_duration(path: str) -> float:
    """Get exact duration of a video file via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def probe_streams(path: str) -> dict:
    """Get video stream metadata (resolution, fps, codec)."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    streams = json.loads(r.stdout)["streams"]
    video = next((s for s in streams if s["codec_type"] == "video"), {})
    return {
        "width":  video.get("width"),
        "height": video.get("height"),
        "fps":    video.get("r_frame_rate"),
        "codec":  video.get("codec_name"),
        "duration": float(video.get("duration", 0)),
    }
```

### 9.4 Ken Burns Fallback (services/ffmpeg_service.py)

```python
def apply_ken_burns(
    image_path:  str,
    output_path: str,
    duration_sec: float,
    direction:   str = "zoom_in",   # "zoom_in" | "zoom_out" | "pan_right" | "pan_left"
    fps:         int = 24,
) -> str:
    """
    Animate a still image using FFmpeg zoompan filter.
    Output matches TARGET_RES @ fps. Never fails (pure local operation).
    """
    n_frames = int(duration_sec * fps)
    w, h     = TARGET_RES.split(":")

    direction_map = {
        "zoom_in":   f"z='min(zoom+0.0015,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        "zoom_out":  f"z='if(lte(zoom,1.0),1.08,max(zoom-0.0015,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        "pan_right": f"z=1.05:x='min(x+0.5,iw*(1-1/zoom))':y='ih/2-(ih/zoom/2)'",
        "pan_left":  f"z=1.05:x='max(x-0.5,0)':y='ih/2-(ih/zoom/2)'",
    }
    zp = direction_map.get(direction, direction_map["zoom_in"])

    vf = (
        f"scale=8000:-1,"                                      # upscale for zoom room
        f"zoompan={zp}:d={n_frames}:s={w}x{h}:fps={fps},"
        f"setsar=1"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-t",  f"{duration_sec:.6f}",
        "-vf", vf,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an",
        output_path, "-loglevel", "error"
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path
```

### 9.5 Scene Assembly (services/ffmpeg_service.py)

```python
def assemble_scenes(
    norm_clips:   list[str],   # ordered list of normalized clip paths
    output_path:  str,
) -> str:
    """
    Concatenate all normalized clips using the FFmpeg concat demuxer.
    All clips MUST be identical resolution, fps, codec (guaranteed by trim_and_normalize).
    """
    concat_file = output_path.replace(".mp4", "_concat.txt")
    with open(concat_file, "w") as f:
        for path in norm_clips:
            f.write(f"file '{path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",           # safe here — all streams already identical
        output_path,
        "-loglevel", "error"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"assemble_scenes failed: {result.stderr[-300:]}")
    return output_path


def merge_audio_video(
    video_path:   str,
    audio_path:   str,
    output_path:  str,
    fade_start:   float,     # seconds from start where 2s fade begins
    audio_dur:    float,     # total audio duration (for -shortest alignment)
) -> str:
    """
    Merge assembled video with audio track. Apply 2-second fade-out on both
    video and audio. -shortest ensures video cuts at audio end.

    fade_start = total_beat_duration - 2.0  (start fade 2s before audio end)
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v",
        "-map", "1:a",
        "-vf",  f"fade=t=out:st={fade_start:.4f}:d=2",
        "-af",  f"afade=t=out:st={fade_start:.4f}:d=2",
        "-c:v", "libx264", "-crf", "17", "-preset", "slow",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",   # web-optimised: moov atom at front
        output_path,
        "-loglevel", "warning"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"merge_audio_video failed: {result.stderr[-400:]}")
    return output_path


def verify_assembly(
    final_path: str,
    expected_scenes: int,
    expected_min_dur: float,
    expected_max_dur: float,
) -> dict:
    """
    Post-assembly verification. Raises AssemblyVerificationError if checks fail.
    """
    if not os.path.exists(final_path):
        raise FileNotFoundError(f"Final video not found: {final_path}")

    size_mb  = os.path.getsize(final_path) / 1024 / 1024
    duration = probe_duration(final_path)
    streams  = probe_streams(final_path)

    errors = []
    if not (expected_min_dur <= duration <= expected_max_dur):
        errors.append(
            f"Duration {duration:.2f}s outside expected "
            f"[{expected_min_dur:.1f}s, {expected_max_dur:.1f}s]"
        )
    if streams.get("width") != int(TARGET_RES.split(":")[0]):
        errors.append(f"Resolution mismatch: {streams}")
    if size_mb < 5:
        errors.append(f"File suspiciously small: {size_mb:.1f}MB")

    if errors:
        raise RuntimeError(f"Assembly verification failed: {'; '.join(errors)}")

    return {
        "duration_sec": duration,
        "size_mb":       size_mb,
        "resolution":    f"{streams['width']}x{streams['height']}",
        "fps":           streams["fps"],
    }
```

### 9.6 Full Assembly Celery Task

```python
# tasks/production.py  (assembly phase)

@celery_app.task(bind=True, max_retries=1)
def assemble_and_merge(self, production_job_id: str):
    """
    Step 1: trim + normalize each scene clip (frame-perfect, one FFmpeg pass each)
    Step 2: concat all normalized clips
    Step 3: merge with audio + fade
    Step 4: verify
    """
    try:
        with SyncSessionLocal() as db:
            job    = crud.get_production_job(db, production_job_id)
            scenes = crud.get_production_scenes(db, production_job_id)
            crud.update_production_status(db, production_job_id, "assembling")

        job_dir   = job.job_dir
        norm_clips = []
        total_beat_dur = 0.0

        for scene in sorted(scenes, key=lambda s: s.scene_number):
            if not scene.raw_video_path or not os.path.exists(scene.raw_video_path):
                raise RuntimeError(
                    f"Scene {scene.scene_number} missing raw video: "
                    f"{scene.raw_video_path}"
                )

            norm_path = os.path.join(
                job_dir, f"norm_{scene.scene_number:02d}.mp4"
            )

            # Frame-perfect trim + normalize in single FFmpeg pass
            ffmpeg_service.trim_and_normalize(
                raw_path     = scene.raw_video_path,
                output_path  = norm_path,
                beat_dur_sec = scene.beat_duration_sec,
            )

            actual_dur = ffmpeg_service.probe_duration(norm_path)
            drift_ms   = abs(actual_dur - scene.beat_duration_sec) * 1000
            if drift_ms > 50:   # >50ms after re-encode is unexpected
                logger.warning(
                    f"Scene {scene.scene_number} post-encode drift: {drift_ms:.1f}ms"
                )

            with SyncSessionLocal() as db:
                crud.update_scene_local_video(db, scene.id, norm_path)

            norm_clips.append(norm_path)
            total_beat_dur += scene.beat_duration_sec

        # Concat
        raw_assembled = os.path.join(job_dir, "assembled_raw.mp4")
        ffmpeg_service.assemble_scenes(norm_clips, raw_assembled)

        # Merge + fade
        final_path  = os.path.join(job_dir, "final.mp4")
        fade_start  = total_beat_dur - 2.0
        ffmpeg_service.merge_audio_video(
            video_path  = raw_assembled,
            audio_path  = job.concatenated_audio_path,
            output_path = final_path,
            fade_start  = fade_start,
            audio_dur   = job.audio_duration_sec,
        )

        # Verify
        verification = ffmpeg_service.verify_assembly(
            final_path        = final_path,
            expected_scenes   = len(scenes),
            expected_min_dur  = job.audio_duration_sec - 3.0,
            expected_max_dur  = job.audio_duration_sec + 1.0,
        )

        with SyncSessionLocal() as db:
            crud.update_production_assembled(
                db, production_job_id,
                assembled_path = final_path,
                duration_sec   = verification["duration_sec"],
                size_bytes     = int(verification["size_mb"] * 1024 * 1024),
            )

    except Exception as e:
        with SyncSessionLocal() as db:
            crud.update_production_status(
                db, production_job_id, "failed", str(e)
            )
        raise self.retry(exc=e, countdown=0, max_retries=0)
```

---

## 10. Phase F — SEO & YouTube Publish

### 10.1 SEO Metadata Generation (Claude)

```python
# services/claude.py  (addition)

SEO_SYSTEM = """
You are a YouTube SEO specialist. Given a music video brief, generate optimised
YouTube metadata. Return ONLY valid JSON with this exact schema:
{
  "title": "string — max 70 chars, compelling, keyword-rich",
  "description": "string — 3-5 sentences, includes keywords naturally, no spam",
  "tags": ["string", ...],        // 10-15 tags, mix of broad and specific
  "hashtags": ["#string", ...],   // 5-8 hashtags for description footer
  "category_id": "10"             // YouTube category: 10 = Music
}
Do not include 'AI generated' or 'AI video' in the title — it suppresses reach.
""".strip()

async def generate_seo_metadata(brief: dict, youtube_url: str = "") -> dict:
    prompt = (
        f"Music video brief:\n"
        f"Theme: {brief['theme']}\n"
        f"Genre: {brief.get('genre', '')}\n"
        f"Mood: {brief.get('mood', '')}\n"
        f"Scenes: {len(brief['scenes'])} scenes, {sum(s['target_duration_sec'] for s in brief['scenes']):.0f}s\n"
        "Generate YouTube SEO metadata."
    )
    r = client.messages.create(
        model="claude-opus-4-6", max_tokens=600,
        system=SEO_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = r.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    return json.loads(raw)
```

### 10.2 YouTube Upload (services/youtube.py)

```python
# services/youtube.py
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import json

def upload_video(
    video_path:  str,
    title:       str,
    description: str,
    tags:        list[str],
    hashtags:    list[str],
    category_id: str = "10",
    credentials_path: str = "youtube_credentials.json",
) -> str:
    """
    Upload video via resumable upload. Returns YouTube video ID.
    OAuth2 credentials must be pre-authorised (run auth flow separately).
    """
    with open(credentials_path) as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)

    youtube = build("youtube", "v3", credentials=creds)

    full_description = (
        description + "\n\n" + " ".join(hashtags)
    )

    body = {
        "snippet": {
            "title":       title[:70],
            "description": full_description,
            "tags":        tags,
            "categoryId":  category_id,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,   # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()

    return response["id"]
```

---

## 11. Celery Task Architecture

### 11.1 Complete Stage 3 Task Chain

```python
# tasks/production.py  (orchestrator)

from celery import group, chord, chain
from app.celery_app import celery_app

@celery_app.task(bind=True, max_retries=2)
def run_production_pipeline(self, production_job_id: str):
    """
    Top-level orchestrator. Runs music + image generation in parallel,
    then animates all scenes, then assembles, publishes.
    """
    try:
        with SyncSessionLocal() as db:
            job = crud.get_production_job(db, production_job_id)
            scenes = crud.get_production_scenes(db, production_job_id)
            crud.update_production_status(db, production_job_id, "generating_music")

        # Branch A: Music (runs in parallel with Branch B)
        music_chord = chord(
            group(create_suno_track.s(production_job_id, i)
                  for i in range(job.num_tracks)),
            on_all_tracks_ready.s(production_job_id)
        )

        # Branch B: Scene images
        image_group = group(
            generate_scene_image.s(production_job_id, s.id)
            for s in scenes
        )

        # Both branches → creative direction → animation → assemble
        pipeline = chord(
            group(music_chord, image_group),
            chain(
                run_creative_direction.s(production_job_id),
                chord(
                    group(animate_scene.s(production_job_id, s.id)
                          for s in scenes),
                    assemble_and_merge.s(production_job_id)
                ),
                generate_and_publish.s(production_job_id),
                cleanup_and_complete.s(production_job_id),
            )
        )
        pipeline.delay()

    except Exception as e:
        with SyncSessionLocal() as db:
            crud.update_production_status(db, production_job_id, "failed", str(e))
        raise self.retry(exc=e, countdown=10)
```

### 11.2 Individual Task Signatures

```python
# Tasks and their retry/timeout policies

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def create_suno_track(self, production_job_id, track_number): ...

@celery_app.task(bind=True, max_retries=2, default_retry_delay=15)
def on_all_tracks_ready(self, results, production_job_id): ...
# → concatenate_audio_tracks, extract_beat_timestamps, assign_scene_cuts

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_scene_image(self, production_job_id, scene_id): ...

@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def run_creative_direction(self, results, production_job_id): ...

@celery_app.task(bind=True, max_retries=1, time_limit=2400)  # 40 min max
def animate_scene(self, results, production_job_id, scene_id): ...
# Contains full Kling submit → poll → download → Ken Burns fallback chain

@celery_app.task(bind=True, max_retries=1, time_limit=1800)
def assemble_and_merge(self, results, production_job_id): ...

@celery_app.task(bind=True, max_retries=2)
def generate_and_publish(self, result, production_job_id): ...

@celery_app.task(bind=True)
def cleanup_and_complete(self, result, production_job_id): ...
```

### 11.3 `animate_scene` Task (full implementation)

```python
@celery_app.task(bind=True, max_retries=1, time_limit=2400)
def animate_scene(self, _results, production_job_id: str, scene_id: str):
    """
    Full animation task:
    1. Submit to Kling 3.0 direct API (with fallback chain)
    2. task_id persisted to DB immediately after submission
    3. Poll until complete
    4. Download raw clip
    5. Trim (frame-perfect) + normalize in one FFmpeg pass
    """
    import asyncio
    from services import kling, ffmpeg_service
    from services.media import image_to_b64

    with SyncSessionLocal() as db:
        scene = crud.get_scene(db, scene_id)
        job   = crud.get_production_job(db, production_job_id)

    raw_path  = os.path.join(job.job_dir, f"raw_{scene.scene_number:02d}.mp4")
    norm_path = os.path.join(job.job_dir, f"norm_{scene.scene_number:02d}.mp4")

    # Resolve image_tail path if applicable
    tail_path = None
    if scene.image_tail_scene_id:
        with SyncSessionLocal() as db:
            tail_scene = crud.get_scene(db, scene.image_tail_scene_id)
        tail_path = tail_scene.local_image_path

    # Animation with fallback
    asyncio.run(animate_scene_with_fallback(
        scene      = scene.__dict__,
        image_path = scene.local_image_path,
        tail_path  = tail_path,
        job_dir    = job.job_dir,
    ))

    # Frame-perfect trim + normalize
    ffmpeg_service.trim_and_normalize(
        raw_path     = raw_path,
        output_path  = norm_path,
        beat_dur_sec = scene.beat_duration_sec,
    )

    with SyncSessionLocal() as db:
        crud.update_scene_complete(db, scene_id, norm_path)
```

---

## 12. Service Class Implementations

### 12.1 CometAPI Service (image gen + Suno)

```python
# services/cometapi.py  (full class)
import httpx

class CometAPIService:
    BASE_URL = "https://api.cometapi.com"

    def __init__(self, api_key: str):
        self._key = api_key

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self._key}"}

    async def generate_image(self, prompt: str, model: str = "gemini-3-pro-image",
                              size: str = "1920x1080") -> str:
        async with httpx.AsyncClient(
            headers=self._headers, timeout=120
        ) as c:
            r = await c.post(f"{self.BASE_URL}/v1/images/generations", json={
                "model": model, "prompt": prompt, "size": size, "n": 1
            })
            r.raise_for_status()
            return r.json()["data"][0]["url"]

    async def create_suno_track(self, prompt: str) -> str:
        async with httpx.AsyncClient(
            headers=self._headers, timeout=30
        ) as c:
            r = await c.post(f"{self.BASE_URL}/v1/audio/generations", json={
                "model": "suno-v5", "prompt": prompt, "instrumental": True
            })
            r.raise_for_status()
            return r.json()["data"]["task_id"]

    async def poll_suno(self, task_id: str) -> dict:
        # Suno response: data.status = "SUCCESS" | "FAILED" | "processing"
        # data.audio_url populated on SUCCESS
        async with httpx.AsyncClient(
            headers=self._headers, timeout=30
        ) as c:
            r = await c.get(f"{self.BASE_URL}/v1/audio/generations/{task_id}")
            r.raise_for_status()
            return r.json().get("data", {})
```

### 12.2 CRUD Operations

```python
# db/crud.py  (key functions for Stages 2 & 3)

async def store_creative_brief(db, curation_job_id: str, brief: dict):
    stmt = (
        update(CurationJob)
        .where(CurationJob.id == curation_job_id)
        .values(
            creative_brief = brief,
            num_scenes     = len(brief["scenes"]),
            status         = "ready",
        )
    )
    await db.execute(stmt)
    await db.commit()

async def create_production_scenes_from_brief(db, production_job_id: str, brief: dict):
    """Create one production_scene row per scene in the approved brief."""
    for scene in brief["scenes"]:
        obj = ProductionScene(
            job_id              = production_job_id,
            scene_number        = scene["scene_number"],
            description         = scene["description"],
            lyric_or_timestamp  = scene.get("lyric_or_timestamp"),
            target_duration_sec = scene["target_duration_sec"],
            kling_model         = scene.get("kling_model", "kling-v3"),
            kling_mode          = scene.get("kling_mode", "std"),
            motion_prompt       = scene.get("motion_prompt"),
            negative_prompt     = scene.get("negative_prompt"),
            animation_method    = scene.get("animation_method", "kling"),
        )
        db.add(obj)
    await db.commit()

async def update_scene_task_id(db, scene_id: str, task_id: str):
    """Persist Kling task_id IMMEDIATELY after submission. Enables resume on restart."""
    await db.execute(
        update(ProductionScene)
        .where(ProductionScene.id == scene_id)
        .values(kling_task_id=task_id, kling_status="submitted")
    )
    await db.commit()

async def update_scene_beat_timing(
    db, scene_id: str,
    start: float, end: float, dur: float, drift_ms: float,
    kling_request_dur: int
):
    await db.execute(
        update(ProductionScene)
        .where(ProductionScene.id == scene_id)
        .values(
            beat_start_sec    = start,
            beat_end_sec      = end,
            beat_duration_sec = dur,
            beat_drift_ms     = drift_ms,
            kling_request_dur = kling_request_dur,
        )
    )
    await db.commit()
```

---

## 13. FastAPI Endpoints

### 13.1 Stage 2 Endpoints

```python
# api/curation.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from schemas.curation import CurationJobCreate, CurationJobResponse, ApproveBriefRequest
from tasks.curation import run_briefing_pipeline
from db import crud

router = APIRouter(prefix="/api/curation", tags=["curation"])

@router.post("/jobs", response_model=CurationJobResponse)
async def create_curation_job(
    payload: CurationJobCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a curation job from selected videos.
    Triggers async briefing pipeline immediately.
    """
    job = await crud.create_curation_job(db, payload)
    run_briefing_pipeline.delay(str(job.id))
    return job

@router.get("/jobs/{job_id}", response_model=CurationJobResponse)
async def get_curation_job(job_id: str, db: AsyncSession = Depends(get_db)):
    return await crud.get_curation_job(db, job_id)

@router.post("/jobs/{job_id}/approve")
async def approve_brief(
    job_id: str,
    payload: ApproveBriefRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User approves (optionally edited) Creative Brief.
    Creates a production_job and launches Stage 3 pipeline.
    """
    await crud.store_user_approved_brief(db, job_id, payload.brief)
    await crud.update_curation_status(db, job_id, "approved")

    prod_job = await crud.create_production_job(db, curation_job_id=job_id)
    await crud.create_production_scenes_from_brief(
        db, str(prod_job.id), payload.brief
    )
    from tasks.production import run_production_pipeline
    run_production_pipeline.delay(str(prod_job.id))

    return {"production_job_id": str(prod_job.id)}
```

### 13.2 Stage 3 Endpoints

```python
# api/production.py
router = APIRouter(prefix="/api/production", tags=["production"])

@router.get("/jobs/{job_id}")
async def get_production_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job    = await crud.get_production_job(db, job_id)
    scenes = await crud.get_production_scenes(db, job_id)
    return {
        "job": job,
        "scenes": scenes,
        "progress": {
            "scenes_animating":  sum(1 for s in scenes if s.kling_status == "submitted"),
            "scenes_complete":   sum(1 for s in scenes if s.local_video_path),
            "scenes_fallback":   sum(1 for s in scenes if s.animation_method == "ken_burns_fallback"),
            "total_scenes":      len(scenes),
        }
    }

@router.get("/jobs/{job_id}/scenes")
async def get_scenes(job_id: str, db: AsyncSession = Depends(get_db)):
    return await crud.get_production_scenes(db, job_id)
```

---

## 14. React Frontend — Polling & UI Rules

### 14.1 Polling Intervals

```typescript
// hooks/useJobPolling.ts
const POLL_INTERVALS = {
  curation_briefing: 5_000,   // 5s while status = "briefing"
  production_animating: 8_000, // 8s while any scenes are processing
  production_assembling: 5_000, // 5s during assemble/merge/upload
  stop_conditions: ["published", "failed", "ready"],
};

function useProductionJob(jobId: string) {
  return useQuery({
    queryKey: ["production", jobId],
    queryFn:  () => fetchProductionJob(jobId),
    refetchInterval: (data) => {
      const status = data?.job?.status;
      if (!status || POLL_INTERVALS.stop_conditions.includes(status)) return false;
      if (status === "assembling" || status === "uploading") return 5_000;
      return 8_000;
    },
    staleTime: 0,
  });
}
```

### 14.2 Scene Card — Status Badges

Each scene card in the Production Studio must show:

| `kling_status` | Badge colour | Label |
|---|---|---|
| `pending` | Grey | Queued |
| `submitted` | Blue | Rendering |
| `processing` | Amber | Rendering… |
| `succeed` | Green | Done |
| `failed` | Red | AI Failed |

| `animation_method` | Badge | Meaning |
|---|---|---|
| `kling` | Purple chip | Kling 3.0 AI |
| `ken_burns_fallback` | Orange chip | Ken Burns (fallback) |

The `image_tail_scene_id` link: when set, draw a connector arrow from this scene card to the target scene card with label "→ transitions to scene N".

### 14.3 Creative Brief Editor (Stage 2 UI)

Required fields the user can edit per scene before approving:

- `description` (textarea)
- `target_duration_sec` (number input, 3.0–15.0, step 0.5)
- `kling_mode` (select: std / pro — auto-forced to pro when image_tail is set)
- `image_tail_scene` (number input or null toggle)
- `motion_prompt` (textarea)
- `negative_prompt` (textarea)

Live validation:
- Show running sum of `target_duration_sec` vs `audio_duration_hint_sec - 2.0`
- Red warning if sum exceeds usable audio
- Orange warning if any scene < 3.0s or > 12.0s

---

## 15. Error Handling & Fallback Chain

### 15.1 Animation Fallback Decision Table

| Attempt | Engine | Mode | image_tail | Retries | On exhaustion |
|---|---|---|---|---|---|
| 1 | Kling v3 | Per brief (std/pro) | If in brief | 2 | → Attempt 2 |
| 2 | Kling v3 | Pro | If in brief | 2 | → Attempt 3 |
| 3 | Kling v3 | Std | Drop image_tail | 2 | → Ken Burns |
| 4 | Ken Burns | FFmpeg local | N/A | N/A | Never fails |

### 15.2 Universal Task Error Pattern

Every Celery task must use this pattern:

```python
@celery_app.task(bind=True, max_retries=N)
def my_task(self, job_id: str, ...):
    try:
        # ... task logic ...
    except SomeRetryableError as e:
        logger.warning(f"{self.name} retrying: {e}")
        raise self.retry(exc=e, countdown=30)
    except Exception as e:
        logger.error(f"{self.name} failed: {e}", exc_info=True)
        with SyncSessionLocal() as db:
            crud.update_job_status(db, job_id, "failed", str(e))
        raise   # Celery marks as FAILURE — stops chain
```

### 15.3 Kling API Error Codes

| Code | Meaning | Action |
|---|---|---|
| 1303 | Parallel task limit exceeded | Wait 30s × attempt number, retry |
| 400 | Invalid base64 | Check for `data:` prefix — must be raw base64 |
| 400 | image_tail not supported | Wrong model — verify model = "kling-v3" |
| 401 | JWT expired | Regenerate token (token TTL = 30min) |
| 429 | Rate limited | Exponential backoff: 30s, 60s, 120s |

---

## 16. Environment Variables & Dependencies

### 16.1 Required Environment Variables

```env
# Database
DATABASE_URL=postgresql+psycopg://user:pass@host/db?sslmode=require
DATABASE_URL_DIRECT=postgresql+psycopg://user:pass@host-direct/db
REDIS_URL=redis://localhost:6379/0

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
COMETAPI_API_KEY=sk-...          # for image gen + Suno
KLING_ACCESS_KEY=AtEpRt...       # Kling 3.0 direct
KLING_SECRET_KEY=nnNtgC...       # Kling 3.0 direct

# YouTube
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback

# App
SECRET_KEY=<openssl rand -hex 32>
JOB_FILES_DIR=/var/ymf/jobs
CELERY_CONCURRENCY=4
DEFAULT_IMAGE_MODEL=nanabananapro
DEFAULT_VIDEO_MODEL=kling-v3
```

### 16.2 Python Dependencies

```
fastapi>=0.115
uvicorn[standard]>=0.29
sqlalchemy[asyncio]>=2.0
psycopg[binary]>=3.1
alembic>=1.13
celery[redis]>=5.3
redis>=5.0
httpx>=0.27
pydantic>=2.0
pydantic-settings>=2.0
anthropic>=0.40
PyJWT>=2.8                # Kling JWT auth
google-api-python-client>=2.120
google-auth-oauthlib>=1.2
yt-dlp>=2025.1
ffmpeg-python>=0.2
librosa>=0.11
soundfile>=0.12           # librosa audio I/O backend
numpy>=1.25
Pillow>=10.0
aiofiles>=23.0
python-multipart>=0.0.9
isodate>=0.6
```

---

## 17. Build Order

Follow this exact sequence. Confirm each phase is fully working with an end-to-end test before starting the next.

### Phase 1 — Foundation
1. Provision server. Install Python 3.12, Node 20, Redis, FFmpeg, yt-dlp, libsndfile.
2. Initialize project. Create `/backend` and `/frontend` directories.
3. `backend/app/core/config.py` — Pydantic Settings loading all env vars.
4. Create Neon DB. Run `pgcrypto` extension. Write Alembic migration for all 5 tables.
5. `tasks/celery_app.py` — Celery init, Redis broker, result backend.
6. `GET /api/health` — DB ping, Redis ping, Kling auth test, CometAPI balance check.
7. Initialize React. Build Settings page — store API keys, model selections.
8. **Test**: health endpoint returns all green.

### Phase 2 — Research Pipeline (Stage 1)
*(Prerequisite for Stage 2 — not covered in this guide)*

### Phase 3 — Stage 2: Curation & Creative Briefing
9. `services/ytdlp.py`: `extract_metadata()`
10. `services/claude.py`: `generate_creative_brief()` with full schema
11. `tasks/curation.py`: `run_briefing_pipeline()` chain
12. `POST /api/curation/jobs` + `GET` + `POST /{id}/approve` endpoints
13. React Curation Board: selected video tiles + Generate Brief button
14. React Creative Brief editor: scene cards, model selectors, duration sum validation, Approve button
15. **Test**: select 3 videos → Claude brief appears → user edits → approves → production_job created

### Phase 4 — Music + Image Generation
16. `services/suno.py`: `create_track()` + `poll_track()`
17. `services/cometapi.py`: `generate_image()` full class
18. `services/media.py`: `image_to_b64()`, `download_and_prep_image()`
19. `services/claude.py`: `generate_music_prompts()` + `generate_image_prompts()`
20. `services/audio_analysis.py`: `extract_beats()` + `assign_scene_cuts()`
21. Celery chord: parallel music + image branches
22. React Production Studio: music track cards + scene image cards updating live
23. **Test**: approve brief → music tracks appear → scene images generate → beat plan assigned

### Phase 5 — Animation & Assembly
24. `services/kling.py`: `make_jwt()`, `submit_animation()`, `poll_animation()`, `download_raw_clip()`
25. `services/claude.py`: `direct_scene()` per-scene creative direction
26. `services/ffmpeg_service.py`: `trim_and_normalize()`, `apply_ken_burns()`, `assemble_scenes()`, `merge_audio_video()`, `verify_assembly()`
27. `tasks/production.py`: `animate_scene` task with full fallback chain
28. `tasks/production.py`: `assemble_and_merge` task
29. React: per-scene animation status badges, Ken Burns fallback indicator
30. **Test**: all scenes animate → trim_and_normalize (frame-perfect) → concat → final.mp4 correct duration

### Phase 6 — Publish & Polish
31. YouTube OAuth2 flow. `services/youtube.py`: `upload_video()`
32. `services/claude.py`: `generate_seo_metadata()`
33. React YouTube Preview: title/desc/hashtags before publish
34. React Dashboard: stats cards, recent jobs, quick-start
35. React Video Library: filter by status/genre/date
36. Nginx reverse proxy + SSL. systemd for uvicorn + Celery workers.
37. **Full end-to-end test**: genre input → published YouTube video with correct metadata

---

## Appendix A — Kling 3.0 API Quick Reference

| Property | Value |
|---|---|
| Base URL | `https://api.klingai.com` |
| Auth | `Authorization: Bearer <JWT>` |
| JWT algorithm | HS256 |
| JWT payload | `{iss: ACCESS_KEY, exp: now+1800, nbf: now-5}` |
| Submit endpoint | `POST /v1/videos/image2video` |
| Poll endpoint | `GET /v1/videos/image2video/{task_id}` |
| Model name | `"kling-v3"` |
| Modes | `"std"` (default) · `"pro"` |
| Duration format | String integer `"3"` through `"15"` |
| Duration range | 3–15 seconds (both std and pro) |
| image_tail | Supported in **both** std and pro |
| image encoding | Raw base64 JPEG — **no** `data:image/...` prefix |
| image max dim | 1536×1536 recommended before encoding |
| Poll status field | `data.task_status` |
| Status values | `"processing"` · `"succeed"` · `"failed"` |
| Video URL path | `data.task_result.videos[0].url` |
| Parallel limit | ~5 concurrent tasks (submit sequentially, poll to completion) |
| Retry on 429 | code 1303 — wait 30s × attempt, max 5 attempts |

## Appendix B — Frame-Perfect Trim: Why `-c copy` is Prohibited

H.264 video contains keyframes (I-frames) spaced every 2–4 seconds by default. When FFmpeg trims with `-c copy` (stream copy), it snaps to the nearest keyframe, producing timing errors of up to 2 seconds. In a beat-matched music video this is unacceptable — even 200ms of drift is audible.

The correct approach (`-c:v libx264` with `-t {exact_duration}`) forces FFmpeg to re-encode the output starting from the exact frame at `t=0` and ending at exactly `t={duration}`. The output contains exactly the right number of frames at 24fps for the target duration.

Cost: re-encoding adds ~2–5s per clip on modern hardware. This is the correct trade-off for beat accuracy.

```bash
# PROHIBITED — snaps to keyframe, timing error up to 2s
ffmpeg -i raw.mp4 -t 4.621 -c copy trimmed.mp4

# CORRECT — frame-accurate, 2-5s additional processing
ffmpeg -i raw.mp4 -t 4.621 -c:v libx264 -crf 17 -preset fast trimmed.mp4
```

## Appendix C — Beat Matching Tuning

If the beat detector produces poor results (e.g., doubles the true BPM or halves it), adjust `librosa.beat.beat_track()` with these parameters:

```python
# If tempo is detected at 2x true BPM (e.g., 184 when song is 92 BPM):
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=90, tightness=100)

# If onset density is too high (too many boundaries):
onset_frames = librosa.onset.onset_detect(y=y, sr=sr, delta=0.08)  # increase delta

# Use bar boundaries (every 4 beats) as primary snap points for visual rhythm:
bar_times = beat_times[::4]
```

Target: one snap boundary every 0.5–1.5 seconds in the combined grid. For most 90–110 BPM tracks this is achieved with beat + onset detection at default settings.

---

*YouTube Movie Factory v3 · Stage 2 & 3 Agent Guide · Aviation Synergy Co., Ltd. · April 2026*
