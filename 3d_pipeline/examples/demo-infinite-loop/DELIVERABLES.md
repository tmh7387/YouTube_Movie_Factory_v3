# demo-infinite-loop — Project Deliverables

Two shots. One is a **calibration** project whose value is the measurements it produced; the other
is the **delivered** shot those measurements made possible.

| Shot | Spec | What it is | Status |
|---|---|---|---|
| **SH010** | `shots/SH010/shot.json` | 15 s seamless loop with a nested-miniature reveal, camera moving | calibration — measurements taken, shot not delivered |
| **SH020** | `shots/SH020/shot.json` | 15 s locked-off take, camera still, performance-only | **delivered** |

---

## The delivered shot — SH020

**Why this shot exists.** SH010 proved that a blockout transfers motion but not composition, and
that Seedance rejects the blockout video outright. It also proved that **Seedance obeys a
composition described in text**. SH020 is designed around exactly that: a shot whose entire value
survives without a video reference.

**Design logic.**

- **A locked-off camera is a text-describable camera.** A move with zero displacement cannot be
  misread. The blockout confirms it — measured camera path length **0.00 m**.
- **Therefore the shot needs no video reference**, which sidesteps the Seedance moderation block
  entirely rather than working around it.
- **All movement is inside the frame.** One performance beat — a man lifts his head, looks off,
  settles — carrying the whole fifteen seconds.
- **The loop is a performance loop, not a camera loop.** He returns to his opening pose, so the
  closing frame matches the opening one without the camera having to travel anywhere.
- **It is honest about its own budget.** 15 s at 720p for ~97 credits, with no gamble on a reveal
  the model cannot stage.

That last point is the real design decision. SH010's miniature reveal is a beautiful idea that
**two different models failed to produce**. SH020 is the shot the pipeline can actually deliver
today, and choosing it deliberately is worth more than another failed attempt at the ambitious one.

**Deliverable:** `takes/SH020_seedance25_720p_takeA.mp4`

---

## Artefacts

### SH020 — delivered

| File | What it is |
|---|---|
| `shots/SH020/shot.json` | **source of truth** — everything else derives from it |
| `shots/SH020/shot.v1.blend` · `.glb` | the blockout, editable and portable |
| `shots/SH020/previz_SH020.mp4` | clean previz (not used as a model reference — see below) |
| `shots/SH020/previz_SH020_annot.mp4` | annotated previz, human review only |
| `shots/SH020/prompt.txt` | generated final prompt |
| `shots/SH020/blockout_report.json` | measured verification record |
| `takes/SH020_seedance25_720p_takeA.mp4` | **the delivered shot** |

### SH010 — calibration

| File | What it is |
|---|---|
| `shots/SH010/shot.json` | the loop shot spec |
| `shots/SH010/previz_SH010.mp4` | the blockout video that Genjutsu accepted |
| `takes/SH010_genjutsu_720p_takeA.mp4` | Genjutsu take — good image, **framing lost** |
| `takes/SH010_seedance25_480p_takeA.mp4` | Seedance 480p take — **framing held**, no reveal |

### Reusable assets

| File | What it is |
|---|---|
| `assets/char-lead-C.png` | selected character plate, 2048×1152 |
| `assets/loc-study-C.png` | selected study plate, 2048×1152, relit for legibility |
| `assets/char-lead-A/B`, `loc-study-A/B/D` | rejected variants, kept for comparison |

**Eight L2 image variants cost roughly 8 credits in total** — about 2 credits each. Image iteration
is effectively free next to video, which is why L2 selection should never be skipped to save time.

---

## Verification results

### SH020 blockout

| Check | Result | Verdict |
|---|---|---|
| Frames / duration | 360 frames, measured 15.00 s | matches spec exactly |
| Readability | mean luminance 0.51 | readable |
| Colour map | lead present (79.4% of frame), set 20.5% | all expected cast colours present |
| **Loop seam** | frames 1 vs 360: **mean difference 0.0, 0.00% of pixels differ** | **seamless — pixel-identical** |
| Camera path length | **0.00 m** over 15 s | confirms genuinely locked off |
| Contract tests | 10 passed, 0 failed | toolkit trustworthy |

### SH010 blockout

Same checks; 0.00% loop seam, camera path 8.88 m over 15 s.

---

## Reproduce

```powershell
$env:BLENDER_EXE = '<path to blender.exe>'
cd 3d_pipeline

# validate
python 50-toolkit\build_blockout.py --spec examples\demo-infinite-loop\shots\SH020\shot.json `
       --out examples\demo-infinite-loop\shots\SH020 --dry-run

# build + previz
python 50-toolkit\build_blockout.py --spec examples\demo-infinite-loop\shots\SH020\shot.json `
       --out examples\demo-infinite-loop\shots\SH020 --render

# generate the prompt
python 50-toolkit\make_prompt.py --spec examples\demo-infinite-loop\shots\SH020\shot.json `
       --out examples\demo-infinite-loop\shots\SH020\prompt.txt

# contract tests
& $env:BLENDER_EXE --background --factory-startup --python 50-toolkit\tests\test_blockout.py
```

---

## What was learned here — see the memory files

This project's real output is knowledge. Read, in order:

1. [`../../40-memory/MODEL_NOTES.md`](../../40-memory/MODEL_NOTES.md) — the **Seedance moderation
   isolation matrix** and the Genjutsu composition limitation, both measured.
2. [`../../40-memory/LESSONS.md`](../../40-memory/LESSONS.md) — six rules extracted.
3. [`../../40-memory/PROJECT_LOG/demo-infinite-loop.md`](../../40-memory/PROJECT_LOG/demo-infinite-loop.md)
   — the full cost and failure accounting.
4. [`../../10-sops/SOP-04-generation-and-delivery.md`](../../10-sops/SOP-04-generation-and-delivery.md)
   — the routing table, rewritten around what was measured.

### The one-sentence version

**A blockout locks motion and timing; it does not lock composition, and it is not accepted by every
model — so calibrate the paid route with a 480p take before designing a project around it.**
