# Video Model Selection

How the platform decides which model animates a scene, and how a user overrides
that decision.

---

## The registry is the source of truth

`backend/app/services/video_models.py` describes every model the platform can
route to. Before this existed, the same facts were duplicated in three places —
`model_router.MODEL_PROFILES`, a `model_mode_map` dict inside
`tasks/production.py`, and substring sniffing in `media_gen_service.animate_image`
— and they had already drifted apart.

Each entry carries three separable things:

| | |
|---|---|
| **capability** | durations, generation modes, reference budgets, resolutions, ratios, native audio |
| **routing** | strengths / weaknesses the ModelRouter scores scenes against |
| **transport** | which API actually runs it, and under which remote model name |

Adding a model is one registry entry, plus one adapter in `media_gen_service`
if it speaks an API nothing else uses.

### Status values

| Status | Meaning | Selectable? |
|---|---|---|
| `available` | wired end to end, exercised in production | yes |
| `preview` | adapter exists, needs credentials and a verification run | yes, badged |
| `planned` | documented target, no working call path | no — shown greyed out |

`configured` is computed separately: it asks whether *this deployment* holds the
credentials that model's transport needs. A `preview` model with no API key is
listed but not launchable.

### Current entries

| Registry id | Model | Transport | Status | Max duration |
|---|---|---|---|---|
| `doubao-seedance-2-0` | Seedance 2.0 | CometAPI | available | 15s |
| `dreamina-seedance-2-5` | Seedance 2.5 | BytePlus ModelArk | preview | 30s |
| `kling-v2-master` | Kling v2 Master | CometAPI | available | 10s |
| `kling-v1-6` | Kling v1.6 | CometAPI | available | 10s |
| `wan-pro` | Wan Pro | CometAPI | available | 5s |
| `minimax-h3` | MiniMax H3 | MiniMax API | preview | 15s |
| `minimax-h3-local` | MiniMax H3 (ComfyUI) | ComfyUI | planned | 15s |

---

## Prompt dialects

Models don't share a prompt grammar, so each entry declares a `dialect`:

| Dialect | Grammar | Director skill |
|---|---|---|
| `seedance-2.0` | `SHOT N`, `@image1` bindings, no clock times | `seedance2-director` |
| `seedance-2.5` | integer-second timestamps, upload-order asset bindings, role tags | `seedance2-director` (Step 0.5 routes) |
| `minimax-h3` | `integrated_multimodal_description` + soundscape fields, `<d>` speech tags | `minimax-h3-director` |
| `kling` | single motion sentence plus a std/pro quality knob | `music-video-producer` |
| `generic` | plain cinematic motion description | — |

`skill_loader_service.DIALECT_SKILL_MAP` maps dialect → skills injected into the
Claude prompt. A new model picks up the right director skill by declaring its
dialect, not by having its name pattern-matched.

Writing a prompt in the wrong dialect fails quietly rather than loudly: a 2.0
prompt with timestamps just loses its timing, and an H3 prompt without the audio
fields gets arbitrary sound design.

---

## Selection precedence

For any scene, the model is decided in this order:

1. **The production run's `video_model`** — what the user picked in the Launcher.
2. **The curation job's `video_model`** — what was chosen when the brief was
   written, so the brief's prompt dialect and the render agree.
3. **Auto-route** — `model_router.recommend_model` scores the scene's visual and
   motion prompts against each configured model's strengths and weaknesses.

When (1) or (2) supply a model, routing is **locked**: `recommend_model` is
called with `lock_preferred=True` and returns the chosen model unconditionally.
A user's explicit pick is never overridden by keyword scoring.

With no selection, each scene routes independently, so one job can mix models —
close-ups to Kling, action to Seedance, and so on.

### Auto-routing signals

`SCENE_SIGNALS` maps keywords to scene characteristics (`character_closeup`,
`fast_action`, `dance`, `dialogue`, `long_form`, …). Each model scores +2×weight
per matched strength and −1.5×weight per matched weakness. Highest score wins;
a `preferred_model` within 70% of the winner is honoured anyway.

No signals at all → the configured default (`DEFAULT_ANIMATION_MODEL`).

---

## API surface

```
GET  /api/models/video?include_planned=true   catalogue + default id
GET  /api/models/video/{model_id}             one model
POST /api/models/video/recommend              {visual_prompt, motion_prompt, preferred_model?}
```

`POST /api/production/start` accepts `video_model`. It is validated up front —
unknown id, non-selectable status, or missing credentials all return 400 rather
than failing halfway through a render.

`POST /api/curation/start` accepts `video_model` too, which becomes the default
for the production run that follows.

---

## UI

The Production Launcher shows an **Auto** tile plus one tile per selectable
model, each with its duration ceiling, native-audio and timestamp support,
reference budget, and cost tier. `preview` models carry a badge; models that are
planned or missing credentials are listed underneath as unavailable, with the
reason.

The Kling std/pro toggle only appears when a Kling model is selected — it is a
Kling-specific quality knob, not a general engine switch. It previously doubled
as the model chooser ("std = Seedance 2.0, pro = Kling Pro"), which is why it
looked like one.

---

## Configuration

```bash
DEFAULT_ANIMATION_MODEL=doubao-seedance-2-0   # registry id used when nothing is picked

COMETAPI_API_KEY=...                          # Seedance 2.0, Kling, Wan
ARK_API_KEY=...                               # Seedance 2.5
ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
MINIMAX_API_KEY=...                           # MiniMax H3
MINIMAX_BASE_URL=https://api.minimax.io       # CN: https://api.minimaxi.com
COMFYUI_BASE_URL=                             # planned: local MiniMax H3
```

`DEFAULT_VIDEO_MODEL` and `SEEDANCE_VIDEO_MODEL` remain, but they are
*transport-level* names passed to CometAPI, not user-facing choices. Don't
confuse them with registry ids.

---

## Legacy ids

Old rows carry ids that predate the registry. `LEGACY_ALIASES` maps them
forward, and `resolve()` falls back to the default rather than raising, so a
stale `animation_model` on a year-old scene row can't take down a rerun:

`kling-v3` · `kling_video` → `kling-v2-master`
`seedance` · `seedance-2-0` → `doubao-seedance-2-0`
`seedance-2-5` · `doubao-seedance-2-5` · `dreamina-seedance-2-5-260628` → `dreamina-seedance-2-5`
`minimax-h3-api` → `minimax-h3`
`wan_pro` → `wan-pro`

Use `is_known()` when you need to reject an unknown id (API validation);
use `resolve()` when you need a model no matter what (render paths).

---

## Adding a model

1. Add a `VideoModel` entry to `MODEL_REGISTRY` with `status="planned"`.
2. If it needs a new transport, add the constant, a credentials check in
   `is_configured()`, and config keys.
3. Write the adapter in `media_gen_service` plus its poller, and dispatch it
   from `animate_image`.
4. If the prompt grammar is new, add a dialect constant, a director skill, and a
   `DIALECT_SKILL_MAP` entry.
5. Verify a real generation, then move the status to `preview`, then
   `available` once it has run in production.
