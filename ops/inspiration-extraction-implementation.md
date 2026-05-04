# YouTube Movie Factory v3 — Video Inspiration Extraction Pipeline

## Context

You are implementing a new feature in the YouTube Movie Factory v3 project
(D:\App development\YouTube_Movie_Factory_v3), a FastAPI + React video
production platform. The backend is Python with AsyncSession PostgreSQL via
SQLAlchemy. The frontend is React 18 + TypeScript + TailwindCSS + TanStack
React Query.

This prompt covers a 3-phase plan. Implement Phase 1 in full. Scaffold
Phases 2 and 3 as described.

---

## The Problem

The Research stage collects Single Video analysis but currently only infers
content from YouTube metadata — it cannot actually watch the video. The
Pre-Production Bible (PreProductionBible model) stores characters[],
environments[], style_lock, and camera_specs, but nothing from research
automatically populates it. Curation briefs are generated without bible
constraints, meaning characters and environments are invented fresh each time.

## The Solution (3 Phases)

- Phase 1: Add a user-triggered "Extract inspiration to Bible" flow on the
  Single Video research detail view. Claude watches the video frame-by-frame
  and extracts character/environment inspiration, which the user reviews
  and applies to a chosen bible.
- Phase 2: Extend the same extraction to multi-video research (YouTube Search),
  aggregating signals across the top results into the bible.
- Phase 3: Modify the curation service to accept a locked bible as a constraint
  layer, ensuring generated scenes reference established characters and
  environments.

---

## Phase 1 — Single Video → Bible Extraction (IMPLEMENT IN FULL)

### 1A. New Backend Service

Create `backend/app/services/video_inspiration_service.py`.

This service downloads a YouTube video, extracts frames, sends them to Claude
as a vision batch, and returns structured inspiration data matching the
PreProductionBible schema.

```python
"""
VideoInspirationService — Watch a video and extract bible inspiration data.

Uses yt-dlp to download, ffmpeg to extract frames, Claude vision to analyze.
Returns structured InspirationData matching the PreProductionBible schema.
"""
import asyncio
import base64
import glob
import json
import logging
import os
import subprocess
import tempfile
from typing import Optional

import yt_dlp
from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum frames to send to Claude (cost control)
MAX_FRAMES = 80
# Extract 1 frame every N seconds
FRAME_INTERVAL_SECONDS = 3


async def extract_inspiration_from_video(video_url: str) -> dict:
    """
    Main entry point. Downloads video, extracts frames, sends to Claude,
    returns InspirationData dict.

    Returns:
        {
          "characters": [...],
          "environments": [...],
          "style_signals": {...},
          "camera_signals": {...},
          "source_video_url": str,
          "source_video_title": str,
          "error": str | None
        }
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # Step 1: Download video
            video_path, video_title = await asyncio.to_thread(
                _download_video, video_url, tmp_dir
            )
            if not video_path:
                return {"error": "Failed to download video", "source_video_url": video_url}

            logger.info(f"Downloaded: {video_title} -> {video_path}")

            # Step 2: Extract frames
            frame_paths = await asyncio.to_thread(
                _extract_frames, video_path, tmp_dir
            )
            if not frame_paths:
                return {"error": "Failed to extract frames", "source_video_url": video_url}

            logger.info(f"Extracted {len(frame_paths)} frames")

            # Step 3: Convert frames to Claude vision content
            image_blocks = _frames_to_content_blocks(frame_paths)

            # Step 4: Send to Claude and parse response
            result = await _analyze_with_claude(image_blocks, video_title, video_url)
            return result

        except Exception as e:
            logger.error(f"Inspiration extraction failed: {e}", exc_info=True)
            return {"error": str(e), "source_video_url": video_url}


def _download_video(video_url: str, output_dir: str) -> tuple[Optional[str], str]:
    """Download video with yt-dlp. Returns (file_path, title)."""
    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": os.path.join(output_dir, "video.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    title = "Unknown"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get("title", "Unknown") if info else "Unknown"
    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}")
        return None, title

    files = glob.glob(os.path.join(output_dir, "video.*"))
    return (files[0] if files else None), title


def _extract_frames(video_path: str, output_dir: str) -> list[str]:
    """Extract frames with ffmpeg at FRAME_INTERVAL_SECONDS, capped at MAX_FRAMES."""
    frame_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    try:
        subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vf", f"fps=1/{FRAME_INTERVAL_SECONDS},scale=768:-1",
                "-frames:v", str(MAX_FRAMES),
                "-q:v", "3",
                frame_pattern,
                "-y", "-loglevel", "error",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg frame extraction failed: {e.stderr.decode()}")
        return []

    return sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))


def _frames_to_content_blocks(frame_paths: list[str]) -> list[dict]:
    """Convert frame JPEG files to Anthropic vision content blocks."""
    blocks = []
    for path in frame_paths:
        with open(path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": data,
            },
        })
    return blocks


async def _analyze_with_claude(
    image_blocks: list[dict],
    video_title: str,
    video_url: str,
) -> dict:
    """Send frames to Claude and extract structured inspiration data."""

    system_prompt = """\
You are a creative director analyzing video frames to extract character and
environment inspiration for an AI video production bible.

Your goal is creative mood/style capture — not hyper-literal frame description.
Extract the visual essence of what you see so it can inspire AI-generated
recreations of similar characters and environments.

Return ONLY a valid JSON object with this exact schema (no markdown fences):
{
  "characters": [
    {
      "name": "Descriptive creative label (e.g. 'The Ritual Dancer', 'The Elder')",
      "physical": "Physical description — build, skin tone, hair style and color, age range, distinguishing features",
      "wardrobe": "Clothing style, specific garments, colors, textures, accessories",
      "expressions": ["emotional states observed, e.g. 'contemplative', 'fierce'"],
      "role": "protagonist | supporting | background | unclear",
      "visual_keywords": ["3-6 evocative style keywords, e.g. 'avant-garde', 'sculptural', 'high-fashion'"],
      "confidence": "high | medium | low"
    }
  ],
  "environments": [
    {
      "name": "Descriptive creative label (e.g. 'The Dark Studio', 'Neon Corridor')",
      "description": "Setting description and visual character — what makes it unique",
      "lighting": "Lighting description — source, direction, quality, color temperature",
      "mood": "Atmospheric mood — 2-4 evocative words",
      "color_palette_description": "Dominant colors and overall temperature",
      "time_of_day": "dawn | day | dusk | night | timeless | unknown",
      "confidence": "high | medium | low"
    }
  ],
  "style_signals": {
    "color_grade": "Overall color treatment observed across the video",
    "visual_aesthetic": "1-3 aesthetic labels (e.g. 'dark editorial', 'cyberpunk minimalism')",
    "cinematography_notes": "Notable camera or lighting techniques that define the visual style"
  },
  "camera_signals": {
    "dominant_shot_types": ["e.g. 'medium close-up', 'extreme wide'"],
    "movement_style": "Movement description (e.g. 'slow dolly with deliberate stillness')",
    "lens_feel": "Lens character (e.g. 'slight telephoto compression, shallow DOF')"
  }
}

Rules:
- Include ALL distinct characters you observe across all frames
- Include ALL distinct environments you observe
- If you are uncertain about a detail, note it in the description rather than
  guessing — e.g. 'appears to be' or 'likely a studio setting'
- confidence: 'high' means clearly visible, 'medium' means partially visible
  or inferred, 'low' means mostly inferred from limited frames
- Do not include characters if you see only a hand or shadow with no
  usable description
"""

    # Build the user message: frames first, then text instruction
    user_content = image_blocks + [
        {
            "type": "text",
            "text": (
                f"Video title: {video_title}\n"
                f"Source: {video_url}\n\n"
                "These frames are sampled at regular intervals across the full video. "
                "Analyze them to extract character and environment inspiration. "
                "Return the JSON object as specified."
            ),
        }
    ]

    try:
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.CLAUDE_CREATIVE_MODEL,  # claude-opus-4-6
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        data["source_video_url"] = video_url
        data["source_video_title"] = video_title
        data["error"] = None

        logger.info(
            f"Inspiration extracted: {len(data.get('characters', []))} characters, "
            f"{len(data.get('environments', []))} environments"
        )
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Claude inspiration JSON parse error: {e}")
        return {"error": f"Failed to parse inspiration JSON: {e}", "source_video_url": video_url}
    except Exception as e:
        logger.error(f"Claude inspiration analysis error: {e}", exc_info=True)
        return {"error": str(e), "source_video_url": video_url}
```

---

### 1B. New API Endpoints in bible.py

Add the following to `backend/app/api/bible.py`.

Add these Pydantic schemas after the existing schemas section:

```python
class InspirationExtractRequest(BaseModel):
    video_url: str

class ApplyCharacter(BaseModel):
    name: str
    physical: str
    wardrobe: str
    expressions: Optional[list] = []
    role: Optional[str] = "unclear"
    visual_keywords: Optional[list] = []
    confidence: Optional[str] = "medium"
    ref_sheet_url: Optional[str] = None

class ApplyEnvironment(BaseModel):
    name: str
    description: str
    lighting: str
    mood: str
    color_palette_description: Optional[str] = ""
    time_of_day: Optional[str] = "unknown"
    confidence: Optional[str] = "medium"
    ref_sheet_url: Optional[str] = None

class ApplySuggestionsRequest(BaseModel):
    characters: Optional[list[ApplyCharacter]] = []
    environments: Optional[list[ApplyEnvironment]] = []
    style_signals: Optional[dict] = None   # maps to style_lock if apply_style is True
    camera_signals: Optional[dict] = None  # maps to camera_specs if apply_camera is True
    apply_style: bool = False
    apply_camera: bool = False
    source_video_url: str
    source_video_title: Optional[str] = ""
```

Add these two endpoints at the end of `backend/app/api/bible.py`,
before any existing final routes:

```python
@router.post("/extract-inspiration")
async def extract_inspiration(data: InspirationExtractRequest):
    """
    Download a YouTube video, extract frames, and use Claude vision to
    identify characters and environments for bible population.

    This is a long-running operation (30-90 seconds). Returns structured
    InspirationData that the frontend presents for user review before
    applying to a specific bible.
    """
    from app.services.video_inspiration_service import extract_inspiration_from_video
    result = await extract_inspiration_from_video(data.video_url)

    if result.get("error"):
        raise HTTPException(
            status_code=500,
            detail=f"Inspiration extraction failed: {result['error']}"
        )
    return result


@router.post("/{bible_id}/apply-suggestions", response_model=BibleResponse)
async def apply_suggestions(
    bible_id: UUID,
    data: ApplySuggestionsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Merge user-selected inspiration suggestions into an existing bible.

    Characters and environments are appended to existing lists.
    style_lock is deep-merged if apply_style is True.
    camera_specs is replaced if apply_camera is True.
    """
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")
    if bible.status == "locked":
        raise HTTPException(status_code=409, detail="Bible is locked")

    # Append characters
    if data.characters:
        existing = list(bible.characters or [])
        for char in data.characters:
            existing.append({
                "name": char.name,
                "physical": char.physical,
                "wardrobe": char.wardrobe,
                "expressions": char.expressions or [],
                "role": char.role,
                "visual_keywords": char.visual_keywords or [],
                "ref_sheet_url": char.ref_sheet_url,
                "source": data.source_video_url,
            })
        bible.characters = existing

    # Append environments
    if data.environments:
        existing = list(bible.environments or [])
        for env in data.environments:
            existing.append({
                "name": env.name,
                "description": env.description,
                "lighting": env.lighting,
                "mood": env.mood,
                "color_palette_description": env.color_palette_description,
                "time_of_day": env.time_of_day,
                "ref_sheet_url": env.ref_sheet_url,
                "source": data.source_video_url,
            })
        bible.environments = existing

    # Merge style_lock if requested
    if data.apply_style and data.style_signals:
        style = dict(bible.style_lock or {})
        style.update({
            "color_grade": data.style_signals.get("color_grade", ""),
            "visual_aesthetic": data.style_signals.get("visual_aesthetic", ""),
            "cinematography_notes": data.style_signals.get("cinematography_notes", ""),
        })
        bible.style_lock = style

    # Replace camera_specs if requested
    if data.apply_camera and data.camera_signals:
        bible.camera_specs = {
            "dominant_shot_types": data.camera_signals.get("dominant_shot_types", []),
            "movement_style": data.camera_signals.get("movement_style", ""),
            "lens_feel": data.camera_signals.get("lens_feel", ""),
        }

    # Append to process log
    import datetime as _dt
    log = list(bible.process_log or [])
    char_count = len(data.characters or [])
    env_count = len(data.environments or [])
    log.append({
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "agent": "video_inspiration",
        "action": "Inspiration applied from video",
        "outcome": (
            f"Added {char_count} character(s), {env_count} environment(s) "
            f"from '{data.source_video_title or data.source_video_url}'"
        ),
    })
    bible.process_log = log

    await db.commit()
    await db.refresh(bible)
    logger.info(f"Applied inspiration to bible {bible_id}: {char_count} chars, {env_count} envs")
    return bible
```

---

### 1C. Register Route in Main App

In `backend/app/main.py`, confirm that the bible router is already registered.
If not, add:

```python
from app.api.bible import router as bible_router
app.include_router(bible_router, prefix="/bible", tags=["bible"])
```

---

### 1D. Frontend Service Additions

In `frontend/src/services/bible.ts`, add these two functions to the existing
`bibleService` object (or export them alongside the existing service):

```typescript
extractInspiration: async (videoUrl: string): Promise<InspirationData> => {
  const response = await fetch('/bible/extract-inspiration', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_url: videoUrl }),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Inspiration extraction failed');
  }
  return response.json();
},

applysuggestions: async (
  bibleId: string,
  payload: ApplySuggestionsPayload
): Promise<Bible> => {
  const response = await fetch(`/bible/${bibleId}/apply-suggestions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to apply suggestions');
  }
  return response.json();
},
```

Add these TypeScript types in `frontend/src/services/bible.ts` or a
co-located `types.ts` file:

```typescript
export interface InspirationCharacter {
  name: string;
  physical: string;
  wardrobe: string;
  expressions: string[];
  role: string;
  visual_keywords: string[];
  confidence: 'high' | 'medium' | 'low';
}

export interface InspirationEnvironment {
  name: string;
  description: string;
  lighting: string;
  mood: string;
  color_palette_description: string;
  time_of_day: string;
  confidence: 'high' | 'medium' | 'low';
}

export interface InspirationData {
  characters: InspirationCharacter[];
  environments: InspirationEnvironment[];
  style_signals: {
    color_grade: string;
    visual_aesthetic: string;
    cinematography_notes: string;
  };
  camera_signals: {
    dominant_shot_types: string[];
    movement_style: string;
    lens_feel: string;
  };
  source_video_url: string;
  source_video_title: string;
  error: string | null;
}

export interface ApplySuggestionsPayload {
  characters: InspirationCharacter[];
  environments: InspirationEnvironment[];
  style_signals?: InspirationData['style_signals'];
  camera_signals?: InspirationData['camera_signals'];
  apply_style: boolean;
  apply_camera: boolean;
  source_video_url: string;
  source_video_title: string;
}
```

---

### 1E. New Frontend Component — InspirationExtractor

Create `frontend/src/components/InspirationExtractor.tsx`:

```tsx
/**
 * InspirationExtractor — extracts character/environment inspiration from a
 * Single Video research result and stages it for bible population.
 *
 * Props:
 *   videoUrl: the YouTube URL from the research job source_data
 *
 * Flow:
 *   1. User clicks "Extract Inspiration to Bible"
 *   2. Extraction runs (calls POST /bible/extract-inspiration)
 *   3. Results shown in staging panel: characters, environments, style, camera
 *   4. User toggles which items to include
 *   5. User selects target bible from dropdown
 *   6. User clicks "Apply to Bible" -> calls POST /bible/{id}/apply-suggestions
 *   7. Success state + link to BibleWorkspace
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sparkles, CheckCircle, XCircle, BookOpen,
  Loader2, ChevronDown,
} from 'lucide-react';
import { bibleService } from '../services/bible';
import type {
  InspirationData,
  InspirationCharacter,
  InspirationEnvironment,
} from '../services/bible';

interface Props {
  videoUrl: string;
}

export default function InspirationExtractor({ videoUrl }: Props) {
  const queryClient = useQueryClient();
  const [inspiration, setInspiration] = useState<InspirationData | null>(null);
  const [selectedCharacters, setSelectedCharacters] = useState<Set<number>>(new Set());
  const [selectedEnvironments, setSelectedEnvironments] = useState<Set<number>>(new Set());
  const [applyStyle, setApplyStyle] = useState(false);
  const [applyCamera, setApplyCamera] = useState(false);
  const [targetBibleId, setTargetBibleId] = useState<string>('');
  const [applied, setApplied] = useState(false);

  const { data: bibles = [] } = useQuery({
    queryKey: ['bibles'],
    queryFn: bibleService.list,
  });

  const extractMutation = useMutation({
    mutationFn: () => bibleService.extractInspiration(videoUrl),
    onSuccess: (data) => {
      setInspiration(data);
      // Pre-select all high- and medium-confidence items
      setSelectedCharacters(
        new Set(
          data.characters
            .map((_, i) => i)
            .filter(i => data.characters[i].confidence !== 'low')
        )
      );
      setSelectedEnvironments(
        new Set(
          data.environments
            .map((_, i) => i)
            .filter(i => data.environments[i].confidence !== 'low')
        )
      );
    },
  });

  const applyMutation = useMutation({
    mutationFn: () => {
      if (!inspiration || !targetBibleId) throw new Error('Select a bible first');
      return bibleService.applysuggestions(targetBibleId, {
        characters: Array.from(selectedCharacters).map(i => inspiration.characters[i]),
        environments: Array.from(selectedEnvironments).map(i => inspiration.environments[i]),
        style_signals: applyStyle ? inspiration.style_signals : undefined,
        camera_signals: applyCamera ? inspiration.camera_signals : undefined,
        apply_style: applyStyle,
        apply_camera: applyCamera,
        source_video_url: inspiration.source_video_url,
        source_video_title: inspiration.source_video_title,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bibles'] });
      setApplied(true);
    },
  });

  const confidenceBadge = (c: string) => {
    const colors: Record<string, string> = {
      high: 'bg-green-500/20 text-green-400',
      medium: 'bg-yellow-500/20 text-yellow-400',
      low: 'bg-gray-500/20 text-gray-400',
    };
    return (
      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${colors[c] ?? colors.medium}`}>
        {c}
      </span>
    );
  };

  const toggleChar = (i: number) =>
    setSelectedCharacters(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  const toggleEnv = (i: number) =>
    setSelectedEnvironments(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  const nothingSelected =
    selectedCharacters.size === 0 &&
    selectedEnvironments.size === 0 &&
    !applyStyle &&
    !applyCamera;

  if (applied) {
    return (
      <div className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-xl text-green-400 flex items-center gap-3">
        <CheckCircle className="w-5 h-5 shrink-0" />
        <div>
          <p className="font-medium text-sm">Inspiration applied to bible</p>
          <a href="/bible" className="text-xs underline opacity-70 hover:opacity-100">
            Open Bible Workspace →
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4">
      {/* Trigger button */}
      {!inspiration && (
        <button
          onClick={() => extractMutation.mutate()}
          disabled={extractMutation.isPending}
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600/20 border border-purple-500/30 text-purple-400 rounded-xl hover:bg-purple-600/30 transition-all text-sm font-medium disabled:opacity-50"
        >
          {extractMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Watching video… (~60 seconds)
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Extract Inspiration to Bible
            </>
          )}
        </button>
      )}

      {extractMutation.isError && (
        <p className="mt-2 text-red-400 text-sm">
          {(extractMutation.error as Error).message}
        </p>
      )}

      {/* Staging Panel */}
      {inspiration && (
        <div className="mt-4 space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold text-white">
              Inspiration from "{inspiration.source_video_title}"
            </h3>
          </div>

          {/* Characters */}
          {inspiration.characters.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Characters ({inspiration.characters.length})
              </p>
              {inspiration.characters.map((char, i) => (
                <div
                  key={i}
                  onClick={() => toggleChar(i)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedCharacters.has(i)
                      ? 'bg-purple-600/15 border-purple-500/40'
                      : 'bg-gray-800/40 border-white/5 opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {selectedCharacters.has(i)
                          ? <CheckCircle className="w-4 h-4 text-purple-400" />
                          : <XCircle className="w-4 h-4 text-gray-600" />
                        }
                        <span className="text-sm font-semibold text-white">{char.name}</span>
                        {confidenceBadge(char.confidence)}
                        <span className="text-[10px] text-gray-600">{char.role}</span>
                      </div>
                      <p className="text-xs text-gray-400">{char.physical}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{char.wardrobe}</p>
                      {char.visual_keywords.length > 0 && (
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {char.visual_keywords.map((k, j) => (
                            <span
                              key={j}
                              className="text-[10px] px-1.5 py-0.5 bg-gray-700/60 text-gray-400 rounded"
                            >
                              {k}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Environments */}
          {inspiration.environments.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Environments ({inspiration.environments.length})
              </p>
              {inspiration.environments.map((env, i) => (
                <div
                  key={i}
                  onClick={() => toggleEnv(i)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedEnvironments.has(i)
                      ? 'bg-blue-600/15 border-blue-500/40'
                      : 'bg-gray-800/40 border-white/5 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {selectedEnvironments.has(i)
                      ? <CheckCircle className="w-4 h-4 text-blue-400" />
                      : <XCircle className="w-4 h-4 text-gray-600" />
                    }
                    <span className="text-sm font-semibold text-white">{env.name}</span>
                    {confidenceBadge(env.confidence)}
                  </div>
                  <p className="text-xs text-gray-400">{env.description}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {env.lighting} · {env.mood} · {env.time_of_day}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Style & Camera toggles */}
          <div className="flex gap-4 flex-wrap">
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={applyStyle}
                onChange={e => setApplyStyle(e.target.checked)}
                className="rounded"
              />
              Apply style signals to bible
            </label>
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={applyCamera}
                onChange={e => setApplyCamera(e.target.checked)}
                className="rounded"
              />
              Apply camera signals to bible
            </label>
          </div>

          {/* Bible selector + apply */}
          <div className="flex gap-3 items-center flex-wrap">
            <div className="relative flex-1 min-w-48">
              <select
                value={targetBibleId}
                onChange={e => setTargetBibleId(e.target.value)}
                className="w-full appearance-none bg-gray-800 border border-white/10 text-gray-300 text-sm rounded-xl px-3 py-2 pr-8"
              >
                <option value="">Select a bible to populate…</option>
                {bibles
                  .filter(b => b.status !== 'locked')
                  .map(b => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.characters?.length ?? 0} chars · {b.environments?.length ?? 0} envs)
                    </option>
                  ))}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>

            <button
              onClick={() => applyMutation.mutate()}
              disabled={!targetBibleId || nothingSelected || applyMutation.isPending}
              className="px-4 py-2 bg-purple-600 text-white rounded-xl text-sm font-medium hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {applyMutation.isPending ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Applying…</>
              ) : (
                <><BookOpen className="w-4 h-4" /> Apply to Bible</>
              )}
            </button>
          </div>

          {applyMutation.isError && (
            <p className="text-red-400 text-sm">{(applyMutation.error as Error).message}</p>
          )}
        </div>
      )}
    </div>
  );
}
```

---

### 1F. Wire InspirationExtractor into Research Detail

In the Research detail view, find where Single Video analysis is rendered.
Locate the component or section that shows the analysis output when
`job.source_type === 'single_video'`. Import and add the component after
the existing analysis output:

```tsx
import InspirationExtractor from '../components/InspirationExtractor';

// Inside the render where single_video analysis is shown:
{job.source_type === 'single_video' && job.source_data?.video_url && (
  <InspirationExtractor videoUrl={job.source_data.video_url} />
)}
```

The `video_url` field comes from `job.source_data.video_url` or
`job.source_data.url` — verify the exact key in the research job's
`source_data` JSONB for the Single Video source type before wiring.

---

## Phase 2 — Multi-Source Aggregation (SCAFFOLD ONLY)

Do not implement Phase 2 in full. Create stubs only.

Create `backend/app/services/inspiration_aggregator_service.py`:

```python
"""
InspirationAggregatorService — Phase 2 (NOT YET IMPLEMENTED)

Aggregates inspiration data from multiple research sources into a single
consolidated set of bible suggestions.

Future implementation will:
1. Accept a list of InspirationData dicts (one per video/source)
2. Cluster similar characters across sources by visual similarity
3. Cluster similar environments by setting type and mood
4. Detect and flag style_lock conflicts (e.g., conflicting color temperatures)
5. Return an aggregated InspirationData with provenance tracking per entry

Triggered from: POST /bible/aggregate-inspiration (to be added to bible.py)
Sources: YouTube Search top-N results, Image Board, Web Article
"""


async def aggregate_inspiration(
    inspiration_sources: list[dict],
    topic: str,
) -> dict:
    raise NotImplementedError(
        "Phase 2 — multi-source aggregation not yet implemented"
    )
```

Add a placeholder endpoint to `backend/app/api/bible.py`:

```python
@router.post("/aggregate-inspiration")
async def aggregate_inspiration_placeholder():
    """Phase 2 placeholder — multi-source inspiration aggregation."""
    raise HTTPException(
        status_code=501,
        detail="Multi-source aggregation is not yet implemented (Phase 2)"
    )
```

---

## Phase 3 — Bible → Curation Constraint (SCAFFOLD ONLY)

Do not implement Phase 3 in full. Add a stub only.

In `backend/app/services/bible_service.py`, add after the existing
`generate_bible_from_context` function:

```python
async def build_bible_constraint_block(bible_id: str) -> str:
    """
    Phase 3 (NOT YET IMPLEMENTED) — Build a prompt constraint block from a
    locked bible for injection into curation brief generation.

    Future implementation will:
    1. Load the locked PreProductionBible by ID
    2. Format characters and environments as named, persistent entities
    3. Return a structured text block for injection into the curation prompt
       in tasks/curation.py, ensuring scene assignments reference known
       characters and environments by name rather than inventing new ones

    Example output block:
        ESTABLISHED CHARACTERS:
        - The Ritual Dancer: [physical], [wardrobe]
        - The Elder: [physical], [wardrobe]

        ESTABLISHED ENVIRONMENTS:
        - The Dark Studio: [description], [lighting]
        - Neon Corridor: [description], [mood]

        STYLE LOCK: [color_grade], [visual_aesthetic]
        CAMERA: [movement_style], [lens_feel]

    Integration point: _orchestrate_curation() in tasks/curation.py
    Trigger condition: CurationJob with non-null bible_id
    """
    raise NotImplementedError(
        "Phase 3 — bible constraint injection not yet implemented"
    )
```

---

## Implementation Notes

### Dependencies

All required packages are already in `backend/requirements.txt`:
- `yt-dlp` — video download
- `ffmpeg-python` — ffmpeg binary is available (used in assembly service)
- `anthropic` — Claude API, accessed via `settings.ANTHROPIC_API_KEY`
- `Pillow` — available if image resizing is needed

The ffmpeg binary must be accessible on PATH. If the project already runs
ffmpeg-based operations, it is available.

### Model Selection

Use `settings.CLAUDE_CREATIVE_MODEL` (currently `claude-opus-4-6`) for
inspiration extraction. The vision analysis benefits from the more capable
model. Extraction takes approximately 30–90 seconds depending on video
length and frame count.

### Error Handling

- If yt-dlp fails (private video, unavailable, region-blocked): return
  `{"error": "Video unavailable: <reason>", "source_video_url": video_url}`
  — do not raise an exception from the service; the endpoint converts it to HTTP 500.
- If ffmpeg fails: log the stderr output and return an error dict. Verify
  that the ffmpeg binary is on PATH before assuming frame extraction will work.
- If Claude returns malformed JSON: log the raw response for debugging and
  return an error dict.

### Timeout Consideration

The extraction endpoint runs synchronously within FastAPI's async event loop
(yt-dlp and ffmpeg are offloaded via `asyncio.to_thread`). For videos over
10 minutes, the full operation could exceed 90 seconds. Do not add background
task queuing in Phase 1 — the frontend already handles this with a loading
state and an explicit "~60 seconds" message. Move to background tasks in a
future phase if needed.

### No New Database Migration Required

Phase 1 adds no new models. All data maps to existing JSONB fields on
`PreProductionBible` (`characters`, `environments`, `style_lock`,
`camera_specs`, `process_log`). The `source` field added to character and
environment objects is stored within the JSONB array — no schema change
needed.

### Bible Locked Guard

The `apply-suggestions` endpoint returns HTTP 409 if the bible is locked.
The frontend bible dropdown must filter to show only unlocked bibles
(`b.status !== 'locked'`).
