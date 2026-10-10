# 3D Scene & Production Video Domain — Phase 1 Knowledge Base

**Owner:** YouTube Movie Factory v3 · **Domain:** Astra → Higgsfield → Blender / Genjutsu 3D pipeline
**Doctrine:** Process · Precision · Profession
**Status:** Phase 1 active

---

## Purpose

This directory is the **executable knowledge base** for building 3D scenes and production
videos with an AI-driven pipeline. It exists so that a project is *repeatable* rather than
*remembered*: any operator (human or agent) should be able to open this folder, follow a SOP,
and produce the same class of result without re-deriving the method.

Phase 2 wires this into the YouTube Movie Factory research and production pipeline. This
directory is deliberately **plain files** — markdown, JSON, Python, shell — so that Phase 2 can
read it as data, not prose.

---

## The one rule that pays for everything else

> **Block in 3D before you spend a single generation credit.**

Every source reviewed reaches the same conclusion independently. Text-only prompting makes the
video model *guess* at spatial logic, so the camera drifts, characters swap seats, the 180-degree
line breaks, and the reveal lands late. When the same shot is blocked as 3D geometry first and
handed over as a reference, the model stops guessing: it has a camera path, a timeline, and
occupancy to follow.

The saving is not only credits — it is **revision cost**. A blockout is an editable timeline, so
a client note becomes a recut, not a rebuild.

---

## Entry points — read in this order

| # | Document | Read it when |
|---|---|---|
| 1 | [`00-overview/STACK_MAP.md`](00-overview/STACK_MAP.md) | You need to know which tool does what, and the tenancy rules |
| 2 | [`00-overview/PIPELINE_ARCHITECTURE.md`](00-overview/PIPELINE_ARCHITECTURE.md) | You need the stage model, gates and cost curve |
| 3 | [`10-sops/SOP-02-blocking-in-blender.md`](10-sops/SOP-02-blocking-in-blender.md) | You are about to build a blockout |
| 4 | [`10-sops/SOP-03-blocking-in-3d-jutsu.md`](10-sops/SOP-03-blocking-in-3d-jutsu.md) | You are working in the browser |
| 5 | [`10-sops/SOP-04-generation-and-delivery.md`](10-sops/SOP-04-generation-and-delivery.md) | The blockout is approved and you are spending credits |
| 6 | [`30-library/prompt-vault/PROMPT_TEMPLATES.md`](30-library/prompt-vault/PROMPT_TEMPLATES.md) | You need a prompt and want the proven shape |
| 7 | [`40-memory/LESSONS.md`](40-memory/LESSONS.md) | Before any generation spend, and at project wrap |

Setup is done once per machine:
[`10-sops/SOP-01-pipeline-setup.md`](10-sops/SOP-01-pipeline-setup.md).

---

## Directory map

```
3d_pipeline/
├── README.md                        ← you are here
├── 00-overview/
│   ├── STACK_MAP.md                 tool inventory, tenancy rules, capability matrix
│   └── PIPELINE_ARCHITECTURE.md     stages, gates, data contracts, cost curve
├── 10-sops/
│   ├── SOP-01-pipeline-setup.md     env vars, Blender, MCP, preflight
│   ├── SOP-02-blocking-in-blender.md
│   ├── SOP-03-blocking-in-3d-jutsu.md
│   └── SOP-04-generation-and-delivery.md
├── 20-reference/
│   └── SOURCES.md                   every ingested source, what it proved, confidence
├── 30-library/
│   ├── prompt-vault/                templates and prompt grammar
│   │   ├── PROMPT_TEMPLATES.md
│   │   └── RECOVERED-PROMPTS.md     prompts recovered verbatim from sources
│   └── shot-grammar/                camera-move and shot vocabulary
│       └── CAMERA_MOVE_CATALOGUE.md
├── 40-memory/                       the feedback loop — see below
│   ├── LESSONS.md
│   ├── MODEL_NOTES.md
│   ├── PATTERNS.md
│   ├── PREFERENCE_PROFILE.md
│   └── PROJECT_LOG/
├── 50-toolkit/                      code that does the work
└── research/                        raw source material (transcripts, scrapes)
```

---

## The feedback loop (how this directory gets smarter)

This mirrors the established `music-video-director` memory pattern in `.agent/`, extended to 3D.

```
Project runs
    │
    ├─► 40-memory/PROJECT_LOG/<slug>.md     episodic: what happened, per project
    │            │
    │            ▼  distill
    ├─► 40-memory/LESSONS.md                one entry per lesson, newest first
    │            │
    │            ▼  promote when proven across 2+ projects
    ├─► 40-memory/PATTERNS.md               reusable, proven method
    │            │
    │            ▼  bake into templates
    ├─► 30-library/                         templates, prompts, camera catalogue
    │            │
    │            ▼  ship inside the SOP
    └─► 10-sops/                            the SOP is the product
```

**`MODEL_NOTES.md` overrides every routing table in these documents.** When observed platform
behaviour contradicts a documented default, the observation wins and it is logged immediately.
Documentation here is a cache; `MODEL_NOTES.md` is the evidence.

---

## Non-negotiables

1. **No generation spend without an approved blockout.** Enforced by the Stage Gate in
   `PIPELINE_ARCHITECTURE.md`.
2. **Nothing is recalled that was not measured.** Every platform limit, cost, and capability claim
   carries a source or a `[VERIFIED]` / `[UNVERIFIED]` tag. Unknown is written as unknown.
3. **Every project writes its wrap-up before it is called complete.** A project that does not
   update memory produced no institutional value.
4. **Blockout files are assets, not scratch work.** The structural layer of a blockout is
   style-agnostic and is retained in the library for reuse in later projects.
5. **Costs are logged per project.** Credit spend is a first-class production metric.

---

## Current asset inventory

| Asset | Location | State |
|---|---|---|
| **Blockout toolkit** | `50-toolkit/` | **built and verified** — spec → blockout → previz → prompt |
| **Contract tests** | `50-toolkit/tests/test_blockout.py` | **10 passed, 0 failed** |
| **Worked example** | `examples/demo-infinite-loop/` | **complete through Gate 3**, loop seam pixel-identical |
| Blender 5.2.1 LTS (portable) | `tools/blender-5.2.1-windows-x64/` | installed, headless-verified |
| Blender 4.5.9 LTS (portable) | `tools/blender-4.5.9-windows-x64/` | installed, for add-on compatibility |
| Higgsfield MCP | session transport | connected, `ultra` plan |
| Source transcript library | `research/phase1_sources/raw/` | 3 videos ingested |
| Community research report | `research/phase1_sources/community/higgsfield-3d-research.md` | 1,160 lines, 337 cited links |
| Prompt vault | `30-library/prompt-vault/` | 12 recovered prompts + 9 templates |
| Camera catalogue | `30-library/shot-grammar/CAMERA_MOVE_CATALOGUE.md` | 9 rig classes, 15 moves, 4 signature shots |
| Reference library | `library/` | **not yet populated** — first real project seeds it |

See [`20-reference/SOURCES.md`](20-reference/SOURCES.md) for the source ledger with confidence
ratings.

---

## Verified: the first key deliverable

**`examples/demo-infinite-loop/`** contains two shots. See its
[`DELIVERABLES.md`](examples/demo-infinite-loop/DELIVERABLES.md) for the full inventory.

| Shot | What it is | Status |
|---|---|---|
| **SH020** | 15 s locked-off take; camera still, performance-only, seamless loop | **delivered** |
| SH010 | 15 s seamless loop with a nested-miniature reveal, camera moving | calibration — the shot that produced the routing data |

```powershell
$env:BLENDER_EXE = '<path to blender.exe>'
python 50-toolkit\build_blockout.py --spec <shot.json> --out <dir> --render
python 50-toolkit\make_prompt.py --spec <shot.json> --references <references.json> --out prompt.txt
```

Its measured results: 360 frames at the exact spec duration · all expected cast colours present in
the render · **loop seam pixel-identical (0.00% of pixels differ)** · 10/10 contract tests passing.

### What running it for real changed

Building the blockout found and fixed **six silent failure modes**, every one of which had produced a
build that reported success — see
[`50-toolkit/README.md`](50-toolkit/README.md#hard-won-platform-findings). Then spending credits
found three more things that no amount of free verification could have revealed:

1. **A blockout locks motion and timing but NOT composition.** Genjutsu applied the camera arc
   smoothly and lost the framing at the mid-shot beat, ignoring the blockout's camera target. A
   frame-matched loop did not survive realisation.
2. **Seedance 2.5 rejects a blockout video as `nsfw`, and no prompt wording changes that.** A bare
   video reference fails even with a prompt that explicitly disclaims people and text. Genjutsu
   accepts the identical file. Full isolation matrix in
   [`40-memory/MODEL_NOTES.md`](40-memory/MODEL_NOTES.md).
3. **Seedance obeys a composition described in text.** That is why the delivered shot is designed the
   way it is — a locked-off camera is text-describable, so the shot needs no video reference at all
   and sidesteps the moderation block by design rather than by workaround.

**Cost of all of this: ~140 credits of a 2,214.87 balance.** The free half of the pipeline — spec,
blockout, previz, prompt generation, verification, three rounds of iteration — cost **zero**. L3 is
93% of a shot's spend and the only place a mistake is expensive.

**Correction to an earlier assumption in this file:** the 4.5.9 LTS Blender build is *not* needed for
add-on compatibility, because this pipeline drives Blender headlessly and never requires the add-on.
It is a fallback, not a dependency.
