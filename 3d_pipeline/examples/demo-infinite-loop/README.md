# Worked Example — demo-infinite-loop / SH010

A complete, verified pass through the pipeline: a 15-second seamless loop, from spec to
generated final prompt. This exists so the method can be **inspected and re-run**, not just
described.

Everything here was produced by the toolkit in [`../../50-toolkit/`](../../50-toolkit/).
Nothing was hand-authored after the spec.

---

## What the shot is

An old mansion study, built as a **nested miniature**: the room we are in is itself a model
of the same room, sitting on a table inside a larger copy of itself. The conceit is only
legible on the final pull-back.

It is deliberately a *hard* first test, because a seamless loop is the shot type where every
silent failure in a blockout becomes visible at once.

| Property | Value |
|---|---|
| Duration | 15.0 s @ 24 fps = 360 frames |
| Aspect | 16:9 (1280×720 previz) |
| Rig | handheld, 1.5 cm drift |
| Optic | 47° diagonal — the house default |
| Format | one single unbroken shot |
| Cast | lead (red capsule), wardrobe + desk (green boxes) |
| Set | inner room 7×7×3 m, outer reveal volume 14×14×6.8 m |

---

## Artefacts

| File | What it is |
|---|---|
| `shot.json` | **the source of truth** — every other artefact is derived from it |
| `references.json` | the reference-pack manifest; binds assets to prompt slots |
| `shot.v1.blend` | the editable blockout |
| `shot.v1.glb` | portable geometry, for other tools |
| `previz_SH010.mp4` | **clean previz** — the model-facing motion reference |
| `previz_SH010_annot.mp4` | annotated previz — human review only, never fed to a model |
| `prompt.txt` | the generated final-generation prompt |
| `blockout_report.json` | machine-checkable record of what was built and measured |
| `review/*.png` | beat frames pulled for visual review |

---

## Reproduce it

```powershell
$env:BLENDER_EXE = 'D:\App development\YouTube_Movie_Factory_v3\tools\blender-5.2.1-windows-x64\blender.exe'
cd 3d_pipeline

# validate the spec, no build
python 50-toolkit\build_blockout.py --spec examples\demo-infinite-loop\shots\SH010\shot.json `
       --out examples\demo-infinite-loop\shots\SH010 --dry-run

# fast look: the beat frames only
python 50-toolkit\build_blockout.py --spec examples\demo-infinite-loop\shots\SH010\shot.json `
       --out examples\demo-infinite-loop\shots\SH010 --render --frames beats

# full previz
python 50-toolkit\build_blockout.py --spec examples\demo-infinite-loop\shots\SH010\shot.json `
       --out examples\demo-infinite-loop\shots\SH010 --render

# the final prompt
python 50-toolkit\make_prompt.py --spec examples\demo-infinite-loop\shots\SH010\shot.json `
       --references examples\demo-infinite-loop\shots\SH010\references.json `
       --out examples\demo-infinite-loop\shots\SH010\prompt.txt
```

---

## Verification results

The build reports these measurements itself. The point of listing them is that none of them
are self-evident from watching the previz.

| Check | Result | Verdict |
|---|---|---|
| Frames rendered | 360 of 360, measured duration 15.0 s | matches spec exactly |
| Readability | mean luminance 0.52 over 12 sampled frames | readable |
| Colour map | lead and prop both present; lead 33.9%, prop 6.4%, set 59.6% of frame | all expected cast colours present |
| **Loop seam** | frames 1 vs 360: **mean difference 0.0, 0.00% of pixels differ** | **seamless — pixel-identical** |
| Contract tests | 10 passed, 0 failed | toolkit trustworthy |

---

## The three defects this example exposed

This is the most valuable part of the example. Building it broke the pipeline three times,
and each break was **invisible in any single frame**.

### 1. A loop cannot contain a travelling performer

The first spec had the lead walk 2.3 m across the room. Every frame looked correct. The loop
seam measured a mean pixel difference of **0.049 with 10.3% of pixels differing** — a seam a
viewer would see on every replay.

The fix is conceptual, not technical: **in a loop, the camera is the only thing allowed to
travel.** The lead now stays at the desk and the walk is described in the prompt for the model
to perform. The spec validator now refuses to build a loop containing cast who travel and do
not return.

### 2. Bezier ease stalls the camera exactly at the seam

`AUTO_CLAMPED` handles ease into the first key and out of the last, which is right along a
path and wrong at its ends. Path endpoints are now set to flat `VECTOR` handles.

### 3. Drift has to be zero on both seam frames

Handheld drift that does not reproduce its opening value at `frame_end` displaces the closing
frame. The drift harmonics now complete whole cycles across the shot, and the drift is forced
to exactly zero on frames 1 and 360.

**Result: from a 10.3% pixel difference to 0.00%.**

---

## What this example does NOT contain

Stated plainly, because a worked example that looks complete while omitting half the pipeline
is misleading:

- **No L2 assets.** The character sheet and location plate are declared in `references.json`
  but have not been generated. The prompt's slot bindings are real; the files are not.
- **No L3 generation.** No credits have been spent. This is the entire point of Gate 2 — the
  shot is fully specified and reviewed *before* the expensive stage.
- **5 `TODO` markers remain in `prompt.txt`.** They are the sections that require a human
  judgement the spec cannot supply: physics, lighting, per-beat x/y frame-map percentages and
  fine performance detail. `make_prompt.py --strict` will refuse to pass them.

So this is a complete pass through **stages S3–S7** and a verified stop at Gate 3. That is
the correct place for a pipeline's first deliverable to stop: everything downstream costs
money, and nothing downstream should run until the free half is proven.

---

## Reusing this environment

The study set is a reusable asset. To use it for another shot, copy `shot.json`, change the
camera path, the beats and the cast, and rebuild — the environment geometry is derived from
the spec's volumes, so it comes along for free. Register it in
[`../../library/environments/`](../../library/environments/) with a `used_by.md` so the next
project can find it instead of rebuilding it.
