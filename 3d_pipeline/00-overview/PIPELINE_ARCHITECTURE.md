# PIPELINE ARCHITECTURE — Stages, Gates, Data Contracts & Cost Curve

**Version:** 1.0 · Companion to [`STACK_MAP.md`](STACK_MAP.md)

---

## 1. Why the pipeline is shaped this way

The economics are asymmetric. Getting a *camera move* wrong costs one regeneration of the most
expensive asset in the stack; getting it right in 3D costs nothing. Every architectural decision
below exists to move uncertainty into the cheap layer.

| Layer | Rough cost of one iteration | Iterations typically needed |
|---|---|---|
| Idea / script | ~0 | 3–10 |
| Local 3D blockout (code) | ~0 | 10–40 |
| Server 3D scene (3D Jutsu) | 50–100 cr | 2–6 |
| Reference images (Soul/Nano Banana) | image-grade | 3–10 |
| Final video generation | **the expensive tier** | target **≤ 2** per shot |

**Design target: at most two final generations per shot** (a variant pair to choose between).
Everything upstream exists to make that number true. If a project is running five or more final
generations per shot, the Stage Gate was skipped and the failure belongs in `LESSONS.md`.

---

## 2. Stage model

Ten stages. Stages 0–2 cost nothing and are where the quality is actually decided.

```
S0  BRIEF ──────────► S1  RESEARCH ────────► S2  CONCEPT LOCK
                                                      │
                                            ╔═════════▼═════════╗
                                            ║  GATE 1 — BRIEF   ║  approved concept,
                                            ╚═════════╤═════════╝  duration, aspect, deliverable
                                                      │
S3  SHOT SPEC ──────► S4  BLOCKOUT ────────► S5  PREVIZ RENDER
                                                      │
                                            ╔═════════▼═════════╗
                                            ║ GATE 2 — BLOCKING ║  camera + timing approved
                                            ╚═════════╤═════════╝  NO CREDITS SPENT YET
                                                      │
S6  ASSET BUILD ────► S7  REFERENCE PACK
                                                      │
                                            ╔═════════▼═════════╗
                                            ║  GATE 3 — ASSETS  ║  identity & look locked
                                            ╚═════════╤═════════╝
                                                      │
S8  GENERATION ────► S9  SELECTION ────────► S10 DELIVERY
                                                      │
                                            ╔═════════▼═════════╗
                                            ║  GATE 4 — PICTURE ║  take locked
                                            ╚═════════╤═════════╝
                                                      │
                                              WRAP-UP (mandatory)
```

---

## 3. Stage detail

### S0 — Brief
**Input:** anything — a sentence, a reference, a client note, a song.
**Output:** `brief.md`
**Minimum contents:** the *one thing* the shot must communicate · intended platform and aspect ·
target duration · audio posture (silent / SFX / dialogue / music) · any non-negotiable brand or
continuity constraint.
**Failure mode:** briefs that describe *style* but not *intent*. Style is L2's job; intent is yours.

### S1 — Research
**Input:** `brief.md`
**Output:** `research.md` — references, comparable shots, absorbed sources.
Research is *AI-driven and mandatory*: search for visual references, prior art, technique notes,
and any existing asset in the library that already solves part of this. Check
`../../3d_pipeline/40-memory/PROJECT_LOG/` for a project that already did something close.
**Reuse rule:** before generating any asset, search the library. A character or location used
before should be re-used, not regenerated.

### S2 — Concept lock
**Output:** `concept.md` + a chosen visual direction.
**Gate 1** — does the concept name a *camera move* and a *duration*? If not, it is not locked.

### S3 — Shot spec
**The central data contract of the pipeline.** A shot spec is a machine-readable JSON file that
fully describes the shot in 3D terms. It is the input to the blockout builder and the source of
truth for every downstream prompt.

See §4 for the schema. It is worth restating here why it matters: **a prompt is prose and a spec is
data.** Prose drifts; data does not. The spec is what makes the pipeline a factory instead of a
conversation.

### S4 — Blockout (3D)
**Input:** `shot.json`
**Two routes:**

| Route | Use when | Tool |
|---|---|---|
| **Code-driven** | repeatability matters, shot is one of many, blockout will be re-rendered in multiple styles, the move is geometrically specific | `50-toolkit/build_blockout.py` |
| **Conversational** | exploring an idea, the scene is complex/organic, speed matters, one-off concept boards | Blender add-on + agent, or 3D Jutsu |

**Output:** `.blend` file + `.glb` export + the spec it was built from, all archived as a
versioned **Blockout Kit**.

### S5 — Previz render
**Output:** an MP4 whose only job is to be *read* — by a human for approval, and by an L3 model as
a motion driver.

Two export forms, both required:
1. **Clean previz MP4** — full frame, no annotations. This is the Genjutsu / Seedance video reference.
2. **Annotated previz MP4** (optional, human-facing) — frame counter, shot label, focal length burn-in.
   Useful for director review; **never** feed the annotated version to a model.

**Gate 2 — the most important gate.** Before this gate: no credits spent. After it: the camera is
locked and downstream cost is bounded.

### S6 — Asset build (L2)
**Output:** character sheets, location plates, product references.
**Rule:** each asset carries exactly one job. Name assets with a stable convention
(`char-<slug>-<variant>.png`, `loc-<slug>-<variant>.png`) so prompts can reference them by name.

### S7 — Reference pack
Assemble the blockout MP4 plus every L2 asset into one **Reference Pack** — a directory plus a
`references.json` manifest that records the *slot order* each asset occupies in the final prompt.

**Slot order is not cosmetic.** L3 models bind `<<<image_1>>>` / `<<<image_2>>>` / `<<<video_1>>>`
to their positions in the pack. Assigning slot numbers in the manifest means a prompt can be
regenerated without re-deriving the mapping.

**Gate 3** — identity and look locked.

### S8 — Generation (L3)
**Input:** shot spec + reference pack + generated prompt.
**Output:** candidate takes.
Generate a **variant pair** — two takes, same prompt, different seed. Select, do not converge
blindly. Cost is logged against the shot.

### S9 — Selection
Score each take against the spec, not against taste alone:
camera fidelity · timing/beats · identity hold · spatial continuity · artifact count ·
audio correctness. Record scores. A rejected take with a *reason* is a `LESSONS.md` candidate.

### S10 — Delivery
Upscale if required, grade, conform, and hand to the assembly stage.
**Gate 4** — picture locked.

### Wrap-up (mandatory, non-optional)
Write `40-memory/PROJECT_LOG/<slug>.md`, then distil into `LESSONS.md`. Update `MODEL_NOTES.md`
with anything the platform did that contradicted documentation. A project without a wrap-up is
not complete.

---

## 4. Data contracts

### 4.1 `shot.json` — the shot spec

```jsonc
{
  "shot_id": "SH010",
  "project": "demo-infinite-loop",
  "version": 1,

  // --- time ---
  "duration_s": 15.0,
  "fps": 24,
  "aspect": "16:9",
  "resolution": [1920, 1080],

  // --- intent (drives every downstream prompt) ---
  "intent": "one continuous take that starts and ends on an identical frame",
  "format_mode": "ONE SINGLE UNBROKEN SHOT",   // or a cut list
  "audio": { "mode": "music", "notes": "rising sub, no dialogue" },

  // --- optic ---
  "optic": {
    "fov_diagonal_deg": 47,
    "character": "standard normal lens, natural proportions, no distortion",
    "dof": "shallow-but-honest, focus rides the subject"
  },

  // --- camera ---
  "camera": {
    "rig": "handheld",              // handheld | locked | dolly | crane | robo-arm | drone | orbit
    "handheld_drift_m": 0.015,      // amplitude, 0 = none
    "height_m": 1.55,
    "path": [
      { "t": 0.0,  "pos": [0.0, -3.2, 1.55], "target": [0,0,1.5], "note": "opening frame — loop key" },
      { "t": 7.5,  "pos": [0.0,  0.0, 1.55], "target": [0,0,1.5], "note": "mid" },
      { "t": 15.0, "pos": [0.0, -3.2, 1.55], "target": [0,0,1.5], "note": "closing frame — must MATCH t=0" }
    ],
    "constraints": [
      "camera passes through nothing: no wall, floor, ceiling or prop",
      "nothing passes through the camera",
      "constant unhurried speed; never stops, never reverses, never zooms"
    ]
  },

  // --- set ---
  "set": {
    "description": "interior study, nested miniature conceit",
    "volumes": [
      { "id": "room_inner", "min": [-4, -4, 0], "max": [4, 4, 3], "role": "primary" },
      { "id": "room_outer", "min": [-8, -8, -1], "max": [8, 8, 5], "role": "reveal" }
    ]
  },

  // --- cast ---
  "cast": [
    { "id": "lead", "proxy": "capsule", "role": "human", "color": [0.9,0.2,0.2,1],
      "start": [0,-1,0], "end": [0,1.6,0],
      "motion": "walks toward the wardrobe, unhurried" }
  ],

  // --- beats ---
  "beats": [
    { "t": 0.0,  "label": "open on identical frame", "action": "lead seated, still" },
    { "t": 4.0,  "label": "hook",  "action": "lead turns, notices the wardrobe" },
    { "t": 8.0,  "label": "rise",  "action": "lead crosses to the wardrobe" },
    { "t": 12.0, "label": "reveal","action": "camera pulls back, inner room becomes a miniature" },
    { "t": 15.0, "label": "close", "action": "frame matches t=0 exactly" }
  ],

  // --- what the previz must NOT export ---
  "exclude_from_realisation": [
    "grey proxy materials",
    "proxy geometry proportions beyond the camera-path intent",
    "previz lighting"
  ]
}
```

**Why `exclude_from_realisation` exists:** the official reference-slot grammar includes an explicit
instruction not to inherit the previz's grey materials, proxy geometry or lighting. Without it,
models try to preserve the blockout's look. Making it a spec field means it is never forgotten.

### 4.2 `references.json` — the reference pack manifest

```jsonc
{
  "shot_id": "SH010",
  "slots": {
    "image_1": { "file": "char-lead-v3.png",     "role": "THE CHARACTER", "job": "identity + wardrobe" },
    "image_2": { "file": "loc-study-v1.png",     "role": "THE LOCATION",  "job": "set + light" },
    "video_1": { "file": "previz_SH010.mp4",     "role": "CAMERA PATH AND FIGURE BEHAVIOUR",
                 "controls": ["camera move", "figure behaviour"],
                 "does_not_control": ["materials", "lighting", "proxy geometry"] }
  }
}
```

### 4.3 Project layout

```
projects/<project-slug>/
├── brief.md
├── research.md
├── concept.md
├── shots/
│   └── SH010/
│       ├── shot.json               ← spec (source of truth)
│       ├── shot.v1.blend           ← blockout, versioned
│       ├── shot.v1.glb             ← portable geometry
│       ├── previz_SH010.mp4        ← clean, model-facing
│       ├── previz_SH010_annot.mp4  ← annotated, human-facing
│       ├── references.json
│       ├── prompt.txt              ← the generated L3 prompt
│       ├── takes/                  ← generated candidates
│       ├── select.md               ← scoring + decision
│       └── cost.log                ← credits, what for, when
└── wrapup.md                       ← feeds PROJECT_LOG
```

---

## 5. The prompt-generation loop (blockout → prompt)

This is the highest-leverage trick in the pipeline and it deserves its own stage description.

**A vision-capable model reads the previz MP4 frame by frame and writes the L3 prompt
second by second, matching the camera motion in the clip.** The askNK workflow does exactly this:
Claude ingests the viewport playblast plus object references, and writes a 30-second
"Seedance prompt" broken down second by second to match the camera motion.

Why this works: the previz is a *measurement* of the shot. A second-by-second breakdown derived
from a measurement is far more accurate than prose written from imagination, and it is
mechanically checkable against the spec.

```
shot.json ──► build_blockout.py ──► .blend/.glb ──► render_previz.py ──► previz.mp4
                                                                            │
                                                                            ▼
                                              (vision pass: read frame by frame)
                                                                            │
                                                                            ▼
                                            timestamped prompt + slot grammar
                                                                            │
                                                            + references.json
                                                                            ▼
                                                                     L3 generation
```

The toolkit in `50-toolkit/` automates the mechanical half of this: the spec already contains the
beat table and camera keyframes, so a **second-by-second prompt scaffold is generated directly from
`shot.json`** and the vision pass is used to *refine and verify* it rather than to invent it. That
halves the cost of the loop and makes it auditable.

---

## 6. Cost curve and the budget law

**Budget law:** `cost(shot) ≈ cost(L1) + cost(L2) + n × cost(L3)`, and the whole point of the
pipeline is to drive `n` toward 2.

Worked example from the sources: one creator produced 17 finished 3D videos for roughly **3,000
credits** (~200 s of video), but that included generating an **entirely new environment for every
scene** — and reported that reusing one environment is far cheaper, yielding **six to eight clips
from a single environment** ([Zane Hoyer](https://www.youtube.com/watch?v=pJLPpB_zueg)). The
lesson is architectural, not budgetary: **environments are capital, shots are consumables.**

Therefore:
- Build environments once, as library assets, and reuse them across shots and projects.
- Group a project's shots by location so one environment serves several.
- Log cost *per shot*, so reuse savings become visible and measurable.

---

## 7. Anti-patterns (each one observed in the sources as the thing that goes wrong)

| Anti-pattern | Symptom | Correction |
|---|---|---|
| **Prompt-first** | camera drifts, seats swap, 180° line breaks | block first, prompt second |
| **Choreography in the blockout** | stiff, mechanical dancer movement | put *position* in the blockout, *choreography* in the prompt |
| **One reference doing two jobs** | identity drifts, wardrobe changes between shots | one asset, one job |
| **Feeding the annotated previz to a model** | burn-in text leaks into the render | clean previz to models, annotated to humans only |
| **Regenerating the environment per shot** | cost explosion with no quality gain | environments are capital; reuse and version them |
| **Unbounded variant generation** | 5–10 takes per shot, none reviewed against the spec | variant pair (2), then decide |
| **Style described in the brief** | brief churn, style drift across shots | intent in the brief, style in L2 assets |
| **No wrap-up** | the same mistake recurs next project | mandatory wrap-up commit |
