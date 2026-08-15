# YTMF v4 Implementation Prompt — For Antigravity / Claude Code

> **Purpose:** This is a code-change specification. Do not rewrite anything that already works. Add new models, endpoints, services, and pages to the existing codebase. Work in phases — complete and test each phase before starting the next.

---

## Tech Stack (do not change)

- **Backend:** Python 3.11, FastAPI, SQLAlchemy (async), Neon PostgreSQL, Pydantic
- **Frontend:** React 18, TypeScript, Tailwind CSS, TanStack React Query, React Router, Lucide icons
- **AI APIs:** Anthropic (Claude Opus/Sonnet), CometAPI (Seedance 2.0 + SeeDream), Kling 3.0 direct
- **Config:** `backend/app/core/config.py` → Pydantic `Settings` from `env/.env`
- **DB session:** `backend/app/db/session.py` → `AsyncSessionLocal`, `get_db`

---

## PHASE 1: Pre-Production Bible (backend)

### 1A. New model — `PreProductionBible`

**File:** `backend/app/models/__init__.py` — add after `CurationJob`:

```python
class PreProductionBible(Base):
    __tablename__ = 'pre_production_bibles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curation_job_id = Column(UUID(as_uuid=True), ForeignKey('curation_jobs.id'), nullable=True)
    name = Column(String(200), nullable=False)
    status = Column(String(20), default='draft')  # draft | locked | archived

    # Structured bible sections (all JSONB)
    characters = Column(JSONB, default=list)       # [{name, physical, expressions, ref_sheet_url, ...}]
    environments = Column(JSONB, default=list)     # [{name, lighting, mood, ref_sheet_url, ...}]
    style_lock = Column(JSONB, default=dict)       # {color_palette, visual_rules, negative_prompt, looks, angles}
    surreal_motifs = Column(JSONB, default=list)   # [{symbol, meaning, visual_fragment}]
    camera_specs = Column(JSONB, default=dict)     # {default_lens, default_movement, lighting_setup}

    # Reference sheet image URLs (generated or uploaded)
    character_sheet_urls = Column(JSONB, default=list)
    environment_sheet_urls = Column(JSONB, default=list)

    # Director process log
    process_log = Column(JSONB, default=list)      # [{timestamp, agent, action, outcome}]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 1B. Add bible FK to existing models

**File:** `backend/app/models/__init__.py`

Add to `CurationJob`:
```python
bible_id = Column(UUID(as_uuid=True), ForeignKey('pre_production_bibles.id'), nullable=True)
```

Add to `ProductionScene`:
```python
bible_character = Column(String(200), nullable=True)   # which bible character this scene features
bible_environment = Column(String(200), nullable=True)  # which bible environment
qa_status = Column(String(20), default='pending')       # pending | passed | failed
qa_notes = Column(Text, nullable=True)
```

### 1C. New API router — `backend/app/api/bible.py`

Create new file with these endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/bible/` | Create new bible (from curation_job_id or standalone) |
| `GET` | `/bible/` | List all bibles |
| `GET` | `/bible/{id}` | Get full bible with all sections |
| `PUT` | `/bible/{id}` | Update bible sections (partial JSONB merge) |
| `PUT` | `/bible/{id}/lock` | Set status='locked' (prevents further edits) |
| `POST` | `/bible/{id}/log` | Append entry to process_log |
| `DELETE` | `/bible/{id}` | Delete bible (only if status='draft') |

Register in `backend/app/main.py`:
```python
from app.api.bible import router as bible_router
app.include_router(bible_router, prefix="/api/bible", tags=["bible"])
```

### 1D. Bible generation service — `backend/app/services/bible_service.py`

Create new file. Core function:

```python
async def generate_bible_from_context(
    research_context: dict,
    style_notes: str = "",
    animation_model: str = "doubao-seedance-2-0",
) -> dict:
```

This function should:
1. Load relevant skills via `skill_loader_service.build_prompt_block()` with contexts `["project_bible", "character_consistency"]`
2. Call Claude Sonnet (`settings.CLAUDE_FAST_MODEL`) with a system prompt that asks for structured JSON output matching the `PreProductionBible` schema
3. Return the parsed bible dict

### 1E. Alembic migration

Generate and run:
```bash
cd backend && alembic revision --autogenerate -m "add_pre_production_bible"
alembic upgrade head
```

---

## PHASE 2: Multi-Source Research Intake (backend)

### 2A. Extend `ResearchJob` model

**File:** `backend/app/models/__init__.py` — add columns to `ResearchJob`:

```python
source_type = Column(String(30), default='youtube_search')
# Values: text_brief | youtube_search | single_video | image_board | audio_track | existing_bible | web_article
source_data = Column(JSONB, default=dict)  # source-specific payload
```

### 2B. Extend research API

**File:** `backend/app/api/research.py`

Update `ResearchCreate` schema:
```python
class ResearchCreate(BaseModel):
    topic: str
    research_depth: str = "standard"
    research_brief: Optional[dict] = None
    source_type: str = "youtube_search"
    source_data: Optional[dict] = None  # {text, video_url, bible_id, article_url, ...}
```

Update `POST /start` to save `source_type` and `source_data` to the job row.

### 2C. New intake normalizer — `backend/app/services/intake_normalizer.py`

Create new file. Core function:

```python
async def normalize_to_research_context(
    source_type: str,
    source_data: dict,
    topic: str,
) -> dict:
    """
    Normalize any source type into a unified research_context dict:
    {
        "topic": str,
        "source_type": str,
        "text_content": str,        # extracted/provided text
        "image_urls": list[str],    # reference images if any
        "audio_meta": dict | None,  # BPM, duration, mood
        "bible_snapshot": dict | None,  # existing bible if provided
        "video_analysis": dict | None,  # transcript + metadata if video source
    }
    """
```

Route by `source_type`:
- `text_brief` → pass through `source_data["text"]` as `text_content`
- `youtube_search` → existing `_orchestrate_research` flow (no change)
- `single_video` → call `youtube_service.get_video_details()` + transcript extraction for one video
- `image_board` → store uploaded image URLs, pass as `image_urls`
- `audio_track` → extract metadata (BPM, duration) from uploaded file, store URL
- `existing_bible` → load `PreProductionBible` by ID, snapshot into `bible_snapshot`
- `web_article` → fetch and extract text from URL (use httpx + basic HTML parsing)

### 2D. Update research task

**File:** `backend/tasks/research.py`

Modify `_orchestrate_research()` to:
1. Check `source_type` on the job row
2. If not `youtube_search`, call `intake_normalizer.normalize_to_research_context()` instead of the YouTube pipeline
3. Store normalized `research_context` in `research_summary` (as JSON string) or a new JSONB column

---

## PHASE 3: Bible-Driven Curation (backend)

### 3A. Update curation task

**File:** `backend/tasks/curation.py`

Modify `_orchestrate_curation()`:
1. After generating the creative brief, check if a bible exists for this curation job (`CurationJob.bible_id`)
2. If no bible exists, call `bible_service.generate_bible_from_context()` using the research context + creative brief
3. Save the generated bible, set `CurationJob.bible_id`
4. When building storyboard scenes, inject bible character/environment names into each scene's metadata

### 3B. Update Claude service

**File:** `backend/app/services/claude_service.py`

Modify `generate_creative_brief()`:
- Accept new optional param `bible: Optional[dict] = None`
- If bible is provided, add a `## Pre-Production Bible` section to the system prompt containing the character list, environment list, style lock rules, and negative prompts
- Instruct Claude to reference bible characters by name and apply style_lock rules to every `visual_prompt`

---

## PHASE 4: Ripple Edit (backend)

### 4A. New endpoint

**File:** `backend/app/api/curation.py` — add:

```
POST /curation/{job_id}/ripple-edit
```

Request body:
```python
class RippleEditRequest(BaseModel):
    instruction: str          # e.g. "Change all outdoor scenes to golden hour"
    scope: str = "all"        # all | visual_only | motion_only | narration_only
    scene_ids: Optional[list[str]] = None  # if null, apply to all scenes
```

Implementation:
1. Load the current storyboard from `CurationJob.user_approved_brief` (or `creative_brief`)
2. Send to Claude Sonnet with the instruction + scope + current scenes
3. Ask Claude to return a JSON diff: `[{scene_index, field, old_value, new_value}]`
4. Return the diff to the frontend (do NOT auto-apply)

### 4B. Apply endpoint

```
POST /curation/{job_id}/ripple-apply
```

Request body: `{"changes": [{scene_index, field, new_value}]}`

Applies the selected changes to the storyboard JSON in `user_approved_brief`.

---

## PHASE 5: Frontend — New Pages & Navigation

### 5A. Update navigation

**File:** `frontend/src/App.tsx`

Update `navItems` array — insert between Curation and Production:
```typescript
{ path: '/bible', label: 'Bible', icon: BookMarked },
{ path: '/storyboard', label: 'Storyboard', icon: Film },
```

Add new routes:
```tsx
<Route path="/bible/:jobId" element={<BibleWorkspace />} />
<Route path="/storyboard/:jobId" element={<StoryboardBoards />} />
```

### 5B. New page — `frontend/src/pages/ResearchIntake.tsx`

Replace the current inline form in `Research.tsx` with a card-grid source selector:

- 7 source-type cards in a responsive grid (3 cols desktop, 2 tablet, 1 mobile)
- Cards: Text Brief, YouTube Search, Single Video URL, Image Board, Audio Track, Existing Bible, Web Article URL
- Clicking a card reveals a source-specific input form below the grid
- Each form submits to `POST /api/research/start` with `source_type` and `source_data`
- YouTube Search card keeps the existing form (topic + depth selector)

### 5C. New page — `frontend/src/pages/BibleWorkspace.tsx`

Two-column layout (40/60 split):

**Left column — Director Process Log:**
- Scrollable timestamped log entries fetched from `GET /api/bible/{id}` → `process_log`
- Color-coded by agent type (blue = Visualizer, purple = Style Director)
- Text input at bottom: "Tell the director..." → `POST /api/bible/{id}/log`

**Right column — Context Notebook (tabbed):**
- Tab 1 "Characters": Card grid from `bible.characters`. Each card shows name, thumbnail, attributes. Edit + Regenerate buttons.
- Tab 2 "Environments": Same layout from `bible.environments`
- Tab 3 "Style Lock": Color swatches from `bible.style_lock.color_palette`, rules list, negative prompt textarea
- Tab 4 "Motifs": Cards from `bible.surreal_motifs`
- Tab 5 "Reference Sheets": Image gallery from `bible.character_sheet_urls` + `bible.environment_sheet_urls`

Lock button in header → `PUT /api/bible/{id}/lock`

### 5D. New page — `frontend/src/pages/StoryboardBoards.tsx`

Four-zone layout:

**Zone 1 (top bar):** Video title + render settings (model selector dropdown, duration, aspect ratio)

**Zone 2 (controls bar):** Buttons: Generate All, Approve Brief, Ripple Edit (opens modal), Export JSON

**Zone 3 (timeline):** Horizontal filmstrip of scene thumbnails with drag-to-reorder (use `@dnd-kit/sortable`)

**Zone 4 (scene cards):** Each scene card is a horizontal row:
- Left: Still image preview (from `image_url` or placeholder)
- Center: Narration text + `motion_prompt` in monospace block, inline edit buttons
- Right: Duration, pacing badge, model badge, QA status badge (green/amber/red)
- "Regenerate Still" button per card

### 5E. Ripple Edit modal — `frontend/src/components/RippleEditModal.tsx`

Full-screen overlay triggered from Storyboard controls bar:
- Top: Textarea for change instruction + scope radio buttons (All, Visual Only, Motion Only, Narration Only)
- "Preview Changes" button → calls `POST /api/curation/{jobId}/ripple-edit` → shows diff
- Middle: Two-column before/after diff for each affected scene. Checkbox per scene to include/exclude.
- Bottom: "Apply Selected" → calls `POST /api/curation/{jobId}/ripple-apply` with checked changes. "Cancel" closes modal.

### 5F. Production page enhancements

**File:** `frontend/src/pages/Production.tsx`

Add to existing page:
- Phase progress bar at top (5 badges: Initialize → Images → Animation → Music → Assembly)
- Credit meter component in top-right (reads from a new `GET /api/production/{jobId}/credits` endpoint if available, otherwise estimate from scene count × model cost)
- Failed scene cards show red border + Recovery dropdown with 3 options: Retry Same Model, Fallback Model, Manual Upload

---

## PHASE 6: Smart Model Routing (backend)

### 6A. New service — `backend/app/services/model_router.py`

```python
def select_animation_model(scene: dict, bible: dict) -> str:
    """
    Route each scene to the best model based on content:
    - Dialogue/lip-sync scenes → Kling Pro (better face handling)
    - Surreal/abstract scenes → Seedance 2.0 (better artistic motion)
    - Default → Seedance 2.0 (user's preferred model)
    Returns model key: 'kling_video' or 'doubao-seedance-2-0'
    """
```

### 6B. Integrate into production pipeline

**File:** `backend/tasks/production.py`

In Phase 1 (scene initialization), after creating `ProductionScene` rows:
1. If a bible is linked to the curation job, load it
2. For each scene, call `model_router.select_animation_model()` to set `scene.animation_model`
3. Log the routing decision to the production job's `progress_log`

---

## Database Migration Summary

New table: `pre_production_bibles` (see Phase 1A)

Altered tables:
- `research_jobs`: add `source_type` (String), `source_data` (JSONB)
- `curation_jobs`: add `bible_id` (FK → pre_production_bibles.id)
- `production_scenes`: add `bible_character` (String), `bible_environment` (String), `qa_status` (String), `qa_notes` (Text)

---

## New Files Summary

| File | Type | Phase |
|------|------|-------|
| `backend/app/api/bible.py` | API router | 1 |
| `backend/app/services/bible_service.py` | Service | 1 |
| `backend/app/services/intake_normalizer.py` | Service | 2 |
| `backend/app/services/model_router.py` | Service | 6 |
| `frontend/src/pages/ResearchIntake.tsx` | Page | 5 |
| `frontend/src/pages/BibleWorkspace.tsx` | Page | 5 |
| `frontend/src/pages/StoryboardBoards.tsx` | Page | 5 |
| `frontend/src/components/RippleEditModal.tsx` | Component | 5 |

## Modified Files Summary

| File | Changes | Phase |
|------|---------|-------|
| `backend/app/models/__init__.py` | New model + FK columns | 1, 2 |
| `backend/app/main.py` | Register bible router | 1 |
| `backend/app/api/research.py` | Extended schema + source_type | 2 |
| `backend/app/api/curation.py` | Ripple edit endpoints | 4 |
| `backend/tasks/research.py` | Multi-source routing | 2 |
| `backend/tasks/curation.py` | Bible generation + injection | 3 |
| `backend/tasks/production.py` | Model routing integration | 6 |
| `backend/app/services/claude_service.py` | Bible injection into prompt | 3 |
| `frontend/src/App.tsx` | New nav items + routes | 5 |
| `frontend/src/pages/Research.tsx` | Swap form for ResearchIntake | 5 |
| `frontend/src/pages/Production.tsx` | Phase bar, credit meter, recovery | 5 |

---

## Implementation Order

```
Phase 1 (Bible model + API + service) → must be first, other phases depend on it
Phase 2 (Multi-source intake) → independent of Phase 3-6
Phase 3 (Bible-driven curation) → depends on Phase 1
Phase 4 (Ripple edit) → depends on Phase 3
Phase 5 (Frontend) → depends on Phase 1-4 APIs existing
Phase 6 (Model routing) → depends on Phase 1
```

Complete each phase fully (model → migration → service → API → test) before starting the next.
