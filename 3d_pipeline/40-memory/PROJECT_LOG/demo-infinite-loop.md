# demo-infinite-loop — Production Log

**Dates:** 2026-09-13 (single session)
**Platform:** Higgsfield · **Plan:** ultra · **Credits at start:** 2,214.87 · **Credits at end:** *in progress*
**Total spend (to date):** 98.46 credits on realisation + ~8 credits of L2 assets
**Deliverable:** 15 s seamless-loop shot, 1280×720 (previz) / 16:9 · **not yet delivered — Gate 3**

> **Status: this is a calibration project, not a delivery.** Its purpose was to prove the
> L1→L2→L3 handoff exists and to measure what each route actually does. It succeeded at both and
> failed at neither — but it did **not** produce a deliverable shot, and that distinction is the
> most important thing in this log.

---

## 1. Brief

Build one shot that ends on a frame identical to its first, so the clip can replay without a seam,
using a nested-miniature reveal to solve the loop geometrically rather than by matching camera
positions. Deliberately chosen because it is the shot type where every silent blockout failure
becomes visible at once.

## 2. Shot list

| Shot | Duration | Location | Aspect | Notes |
|---|---|---|---|---|
| SH010 | 15 s | mansion study | 16:9 | one continuous take, 360 frames @ 24 fps |

## 3. Environments — the reuse ratio

| Environment | Built how | Shots served | Regenerated? |
|---|---|---|---|
| study (nested miniature) | Blender, code-driven from `shot.json` volumes | SH010 | no |

**Reuse ratio:** 1.0 — no reuse yet, which is expected for a single-shot calibration project and
would be a red flag in a production. The environment is reusable; it has simply not been reused.

## 4. Blockout approach

| Shot | Route | Why | Iterations | Previz exported |
|---|---|---|---|---|
| SH010 | code (`shot.json` → `build_blockout.py`) | must be reproducible and restylable | 3 spec revisions + 1 defect fix | `previz_SH010.mp4` (clean) + annotated |

Three spec revisions: the initial build, a loop-integrity fix (travelling cast), and the
environment-defect fixes found by the checks. **Cost of all iterations: 0 credits.**

## 5. Reference packs

| Slot | Asset | Source | Status |
|---|---|---|---|
| `image_1` | `char-lead-v1` / v2 | Soul Cinematic, 4 variants generated | **selected v2 (buttoned)** |
| `image_2` | `loc-study-v1` | Soul Cinematic, 4 variants generated | **selected v3 (C, re-lit)** |
| `video_1` | `previz_SH010.mp4` | `build_blockout.py` | clean, 15.00 s verified |

**4 character variants and 4 location variants were generated to select one of each.** At ~2 credits
per image this cost roughly **8 credits total** — image iteration is effectively free next to video,
which is why L2 selection should never be skipped to save time.

**Slots are not interchangeable — verified the hard way.** With two character images in the pack,
Genjutsu used the **first-uploaded** one and produced a man in the wrong wardrobe.

## 6. Generation

| Shot | Model | Duration | Res | Takes | Credits | Result |
|---|---|---|---|---|---|---|
| SH010 | **Genjutsu** Motion Transfer | 15 s | 720p | 1 | **98.46** | delivered, quality good, **framing wrong** |
| SH010 | Seedance 2.5 `omni_reference` | 15 s | 720p | 2 attempts | 0 (rejected) | **moderation-blocked** |
| SH010 | Seedance 2.5 `omni_reference` | 15 s | 480p | 1 | ~40 | *in progress at time of writing* |

**Takes per shot: 1 successful.** The pipeline target is 2; the calibration nature of the project
means one take plus a scored evaluation was the correct spend.

## 7. Cost accounting

| Stage | Credits | % of total |
|---|---|---|
| L1 structure (local Blender) | **0** | 0% |
| L2 identity & look (8 image variants) | ~8 | 7% |
| L3 realisation (Genjutsu 720p) | **98.46** | 93% |
| Upscale / finishing | 0 | 0% |
| **Total** | **~106** | 100% |

**Cost per finished second:** ~6.6 cr/s
**Cost per shot:** ~106 cr

**The headline number: the entire free half of the pipeline — spec, blockout, previz, prompt
generation, verification, and three rounds of iteration — cost zero credits and produced the shot's
entire structure.** L3 is 93% of spend and is the *only* stage where a mistake is expensive.

## 8. What shipped

Nothing. **Deliberately.** This project stopped at Gate 3 for the calibration, then spent on one
take specifically to *measure* the paid layer rather than to deliver. See §9.

## 9. Failures and root causes — the substance of this project

| Count | What failed | Root cause | Fixable by |
|---|---|---|---|
| 1/1 | **Framing lost at mid-shot.** At the beat where the blockout is a medium close-up of the subject, the generated shot was on the wardrobe wall with the subject half out of frame. | **Genjutsu transfers motion and timing, not composition.** It re-frames to its own judgement and ignores the blockout's camera target. | route selection — use a model that honours framing for narrative coverage |
| 1/1 | **Loop seam lost.** Closing frame did not reproduce the opening frame. | same root cause: framing is not carried over | as above |
| 2/2 | **Seedance rejected as `nsfw`.** | moderation triggered by the reference set; a bare chest was visible in the first character plate, and rejection recurred with a corrected plate, so the trigger is not fully isolated | dress reference plates conservatively; isolate the trigger before repeating |
| 1/1 | **Wrong wardrobe used.** | two character plates in the pack; the first-uploaded won | one character plate per pack, or deliberate slot ordering |

**Zero blockout defects in the final build.** The blockout itself was verified to 0.00% loop seam
error and passed 10/10 contract tests. **Every failure in this project happened above the free
layer, in the paid layer, and none of them were detectable from the blockout.** That is the central
finding.

## 10. Library additions

| Asset | Type | Where it lives | Reusable for |
|---|---|---|---|
| study environment | `.blend` + `.glb` + `shot.json` | `examples/demo-infinite-loop/` | any interior study scene |
| infinite-loop shot pattern | spec + verified technique | `CAMERA_MOVE_CATALOGUE.md` §4.1 | any loop shot |
| blockout toolkit | code | `50-toolkit/` | every future shot |
| character plate (buttoned, 2k) | image | `examples/.../assets/char-lead-C.png` | any shot needing this actor |
| study location plate (2k, legible) | image | `examples/.../assets/loc-study-C.png` | any shot in this room |
| **Genjutsu framing limitation** | measurement | `MODEL_NOTES.md` | routing for every future shot |
| **Seedance `mode` parameter gotcha** | measurement | `MODEL_NOTES.md` | every future Seedance call |

## 11. Lessons produced

- → `LESSONS.md`: *demo-infinite-loop (L3 realisation, first paid run)* — five rules
- → `MODEL_NOTES.md`: Genjutsu framing limitation (measured), Genjutsu cost verified at 98.46 cr,
  reference-slot-order behaviour, Seedance `mode` default rejecting references, Seedance `nsfw`
  moderation cause, preset-suggestion behaviour
- → `PREFERENCE_PROFILE.md`: routing is now *fidelity-first*, not price-first
- → `SOURCES.md` / `RECOVERED-PROMPTS.md`: the frame-map-percentage TODO is now a known gap

## 12. Next time

**Calibrate the paid layer before committing a shot's design to it.** This project verified its
blockout to pixel-perfect loop closure and still lost both the framing and the loop in realisation —
because verification of the free layer says nothing about the paid layer.

Concretely: **spend one 480p take per candidate model on the first shot of a project**, score it
against the spec, and only then design the remaining shots around whichever model actually holds
composition. At ~40 credits a 480p calibration take, that is the cheapest insurance in the pipeline.
