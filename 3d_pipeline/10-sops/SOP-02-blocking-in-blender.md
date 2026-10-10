# SOP-02 — Blocking a Shot in Blender

**Stage:** S3–S5 · **Cost:** ~0 (local) · **Prerequisite:** [`SOP-01`](SOP-01-pipeline-setup.md)
**Output:** a versioned **Blockout Kit** — `.blend`, `.glb`, clean previz MP4, and the `shot.json` it
was built from.

> **This SOP is the load-bearing wall of the pipeline.** Everything downstream inherits its
> precision or its sloppiness. Budget your attention accordingly: most of the quality is decided here,
> where it is free.

---

## 0. Why code-driven rather than conversational

The conversational route (agent + add-on) is excellent for *exploration* and *one-off concept boards*.
It is a poor fit for a production pipeline because **it is non-deterministic**: the same request
produces a different blockout each time, so a blockout cannot be re-derived, diffed, reviewed, or
regenerated in a new style with confidence.

The code route is deterministic. Same spec in, same blockout out — on any machine, forever. That is
what makes the blockout *capital* (see [`PATTERNS.md` P-02](../40-memory/PATTERNS.md)).

| | Code-driven | Conversational |
|---|---|---|
| Determinism | exact | none |
| Cost | ~0 | ~0 local / 50–100 cr in 3D Jutsu |
| Speed to first look | slower | faster |
| Restyling later | free — re-render the same spec | re-derive by hand |
| Complex organic sets | laborious | strong |
| Best for | production shots, sequences, library assets | exploration, concept boards, one-offs |

**Decision rule:** if the shot will be *delivered*, or *restyled*, or *reused*, build it from code.
If you are *thinking*, converse.

---

## 1. Write the shot spec first

Do not open Blender until `shot.json` is written. The spec is where the cinematography happens; the
script only executes it.

Schema: [`../00-overview/PIPELINE_ARCHITECTURE.md`](../00-overview/PIPELINE_ARCHITECTURE.md) §4.1.

**Minimum viable spec — a shot is not specified until all six exist:**

1. **duration + fps + aspect** — the frame budget
2. **intent** — the one thing the shot must communicate, in one sentence
3. **format_mode** — one unbroken take, or a named cut list
4. **optic** — FOV and lens character
5. **camera.path** — at least a start and an end keyframe with positions *and* targets
6. **beats** — the timeline, with a label and an action at each beat

**Two spec disciplines that prevent most downstream failures:**

- **Constraint list.** Encode the negatives *in the spec*, not in your head:
  `"camera passes through nothing"`, `"nothing passes through the camera"`,
  `"constant speed; never stops, never reverses, never zooms"`.
- **`exclude_from_realisation`.** Always include the blockout's grey materials, proxy geometry and
  previz lighting. Downstream prompts inherit this verbatim, and its absence is why models try to
  preserve the blockout's look.

### Loop shots

If the shot is a loop, mark `beats[0]` and `beats[-1]` as loop keys and annotate the camera path with
`opening frame — loop key` / `closing frame — must MATCH t=0`.

**Critical:** a frame-matched loop does **not** require position-matched cameras. The official
infinite-loop build ends with the camera in a *totally different position* from the start and still
matches frames, because the set was built so the move arrives back at the opening composition. Solve
the loop **geometrically** (see [`CAMERA_MOVE_CATALOGUE.md`](../30-library/shot-grammar/CAMERA_MOVE_CATALOGUE.md)
§4.1), not by trying to return the camera home.

---

## 2. Build the blockout

```
python 50-toolkit/build_blockout.py \
    --spec projects/<slug>/shots/SH010/shot.json \
    --out  projects/<slug>/shots/SH010/ \
    --blender <path-to-blender.exe>
```

The builder produces:

| Output | Purpose |
|---|---|
| `shot.v1.blend` | editable blockout, versioned |
| `shot.v1.glb` | portable geometry for 3D Jutsu / other tools |
| `previz_SH010.mp4` | **clean** previz — the model-facing motion reference |
| `previz_SH010_annot.mp4` | annotated previz — human review only |
| `blockout_report.json` | machine-checkable: measured duration, keyframe count, collisions detected |

What the builder guarantees, so you do not have to check it by eye:

- **Colour-coded cast proxies** per the pipeline standard (lead red, support blue, crowd grey).
- **Camera is target-constrained** — an empty target is parented and the camera holds a
  `TRACK_TO` constraint, so framing survives path edits. *This is the single most transferable trick
  in the whole method.*
- **Frame-count arithmetic is checked against duration × fps** and mismatches fail loudly.
- **Explicit frame-range export**, so the previz always matches the spec's duration exactly.

---

## 3. Review the blockout — the four checks

Never approve a blockout by watching it once. Run these four checks in order; each catches a
different class of failure.

| # | Check | How | What it catches |
|---|---|---|---|
| 1 | **Geometry** | measure the actual bounding boxes against the spec's volumes | scale errors that only become visible after generation |
| 2 | **Camera** | step to every beat's frame number and compare the composition to the intent | drift, unintended framing changes, missed reveals |
| 3 | **Collision** | walk the path frame by frame, or read `blockout_report.json` | camera clipping geometry — the failure that ruins an otherwise good take |
| 4 | **Loop/time** | for loops, diff first vs last frame; for sequences, verify every beat lands at its frame number | seams and timing slips |

**Review discipline:** review against the **spec**, not against your impression. "It looks good" is
not an approval. "Beat at 8.0 s lands at frame 192 and the reveal is legible" is.

---

## 4. Export the previz correctly

Two exports, always both:

| Export | Settings | Fed to |
|---|---|---|
| **clean** | MPEG-4 / H.264, spec resolution, spec fps, no overlays, no annotations | Genjutsu / Seedance as `video_references` |
| **annotated** | same, plus frame counter, shot ID and focal length burn-in | humans only |

> **Never feed the annotated previz to a model.** Burn-in text leaks into the render. This is a real
> and avoidable failure — the annotation is on the frame, and the model reads frames.

Encoding settings that matter for a reference clip (the model is reading motion, not admiring the
image):

- **Constant frame rate**, matching the spec's fps. Variable frame rate breaks frame-by-frame reading.
- **H.264, high quality** — compression artifacts look like motion to a vision model.
- **No motion blur, no film grain** in the render. Blur is the one thing that genuinely confuses
  motion extraction.
- **Full spec resolution**, not a preview resolution.

---

## 5. Archive the Blockout Kit

A blockout is not scratch work. Commit:

```
projects/<slug>/shots/SH010/
├── shot.json                  ← the spec (source of truth)
├── shot.v1.blend
├── shot.v1.glb
├── previz_SH010.mp4
├── previz_SH010_annot.mp4
├── blockout_report.json
└── references.json
```

And if the environment is reusable — it usually is:

```
library/environments/<env-slug>/
├── env.v1.blend
├── env.v1.glb
├── spec.json                  ← volumes, materials, camera-height conventions
└── used_by.md                 ← every shot that has used it
```

**The `used_by.md` file is what turns a folder into capital.** It is how you find out, before
generating anything, that this environment already served six shots.

---

## 6. Gate 2 — the approval that bounds the budget

Before passing Gate 2, confirm all of the following. If any is false, do not proceed — the cost of
fixing it here is zero and the cost of fixing it after generation is a full regeneration.

- [ ] Camera move is exactly what the intent requires, verified at every beat frame
- [ ] Every beat lands on its spec frame number
- [ ] No camera/geometry collisions anywhere on the path
- [ ] Loop shots: first and last frames match
- [ ] Cast occupancy and orientation are unambiguous (colour-coded, single lead shape)
- [ ] `shot.json` `constraints` and `exclude_from_realisation` are populated
- [ ] Clean previz exported at spec resolution and constant fps
- [ ] Blockout Kit archived; environment registered in the library with a `used_by.md`

**Gate 2 is the last point at which a mistake is free.** Everything after it costs credits.

---

## 7. Troubleshooting

| Symptom in the previz | Cause | Fix |
|---|---|---|
| Camera clips through geometry | path keyframes too sparse | add intermediate keyframes; check collisions per frame |
| Framing drifts mid-move | camera driving its own rotation instead of tracking a target | ensure the target empty is parented and the `TRACK_TO` constraint is present |
| Previz duration ≠ spec duration | frame range not set explicitly, or fps mismatch | set `frame_start`/`frame_end` from `duration × fps`; verify fps |
| Loop seam visible | closing composition does not match opening | fix geometrically — extend or nest the set so the move arrives back at the opening frame |
| Movement looks mechanical in the final render | choreography was animated in the blockout | **remove proxy animation; put choreography in the prompt** (P-03) |
| Model reproduces grey materials | `exclude_from_realisation` missing from the prompt | add it; it is a required field |
| Export is huge / slow to hand over | rendering at delivery resolution | reference clips only need enough to read motion — but keep fps and frame count exact |

---

## 8. What "done" looks like

A blockout is done when **a camera operator could shoot from it without asking a question**.

If they would have to ask where the camera starts, what it does, what it frames at any moment, or who
is where — the spec is not finished, no matter how good the previz looks.
