# CAMERA_MOVE CATALOGUE — Shot Grammar for Blockouts and Prompts

**Purpose:** a shared vocabulary. When the blockout, the spec and the prompt all use the *same name*
for a camera move, precision survives the handoff. This file is the reference for that naming.

**How to use it**
- In a `shot.json`, name the rig (`camera.rig`).
- In a blockout prompt, write `CAMERA = <rig name>` — a named rig imports a whole movement grammar
  in two words.
- In the final prompt, expand the rig into a per-second breakdown.

---

## 1. Rig classes

Pick the rig first; it constrains everything downstream.

| Rig | Character | Use when | Blockout note |
|---|---|---|---|
| **locked** | tripod, zero movement | dialogue coverage, product hero, deliberate stillness | freeze the camera object; no drift |
| **handheld** | human operator, living frame | intimacy, documentary, urgency, realism | add drift amplitude in metres — **0.010–0.020 m reads as human; 0.000 m reads as CG** |
| **dolly** | rail, perfectly linear | reveals, tension, corridors | constrain to a straight line; layer the target separately |
| **crane / jib** | vertical arc | scale reveals, endings | vertical component dominant |
| **robo-arm** | mechanically perfect, arbitrary path | orbits, impossible continuous moves, product spin | zero shake; constant speed; never stops or reverses |
| **orbit** | circular around a subject | character focus, 360° turns | constant radius unless deliberately closing |
| **drone** | free 3D flight | establishing, terrain, scale | watch the ground plane; no impossible accelerations |
| **steadicam** | gliding follow | walking-and-talking, journeys | smooth but human; slight lateral sway |
| **whip / snap** | very fast transition | energy, beat drops, match cuts | reads as a blur — plan the post-blur framing |

---

## 2. Move vocabulary

| Move | Definition | Reads as |
|---|---|---|
| **push in** | camera translates toward subject | intensification, narrowing attention |
| **pull back / pull out** | camera translates away | reveal, isolation, context |
| **dolly zoom** | translate while counter-zooming to hold subject size | disorientation, dread |
| **truck / track** | lateral translation | parallel observation |
| **pan** | horizontal rotation, camera fixed | surveying |
| **tilt** | vertical rotation, camera fixed | scale, ascent/descent |
| **roll / dutch** | rotation about the lens axis | unease, stylisation — use sparingly |
| **crane up / down** | vertical translation | reveal, arrival, departure |
| **arc** | translation along a curve around subject | deepening relationship with subject |
| **tracking shot** | follow a moving subject | participation |
| **reveal** | any move whose endpoint changes what is visible | narrative turn |
| **rack focus** | focal plane shift without camera movement | attention transfer |
| **crash zoom** | extremely fast zoom | shock, comedy, emphasis |
| **fly-through** | continuous translation through geometry | journey, immersion |
| **impossible shot** | a move physics forbids, built as geometry | spectacle — see §4 |

---

## 3. Composition constants

Set these once per project and hold them. Drifting composition between shots is the most common
continuity failure in generated video.

| Parameter | Pipeline default | Why |
|---|---|---|
| **Camera height** | **1.55 m** (eye level) for adults; scale per subject | human-eye default; deviating is a statement |
| **Diagonal FOV** | **47°** = standard normal lens | the official grammar uses 47° and calls it "standard normal lens character" |
| **Subject distance** | state it in metres and state how it changes | distance is the real shot-size control |
| **Headroom** | state as a percentage of frame height | prevents the model from reframing |
| **Lead room** | state which side, and how much | preserves eyeline convention |
| **Frame maps** | **x%/y% occupancy per beat** | the official grammar's method for text-based spatial precision |

**Wide / medium / close as numbers (16:9, 47° FOV, adult subject):**

| Shot size | Subject frames | Camera distance | x% occupancy |
|---|---|---|---|
| Wide / establishing | full body + environment | 8–15 m | 8–18% height |
| Full shot | full body, head near top | 5–7 m | 60–75% height |
| Medium | waist up | 2.5–3.5 m | 40–55% height |
| Medium close-up | chest up | 1.8–2.4 m | ~60% height |
| Close-up | head and shoulders | 1.2–1.6 m | 70–80% height |
| Extreme close-up | feature | 0.3–0.6 m | fills frame |

*(These are working values for blockout geometry, not lens tables. Calibrate once against a real
previz render and record the correction here.)*

---

## 4. Signature shots — how to build them

Four moves recur in the sources because they are disproportionately impressive and disproportionately
hard to prompt. Each has a **geometric** solution, which is why they belong to the blockout layer.

### 4.1 The seamless loop
**Problem:** make a video that replays without a visible seam.
**Geometric solution:** clone the set so the closing move lands on the opening frame. Nesting a copy
of the room inside a larger copy of itself lets a pull-back arrive back at the start.
**Critical detail from the source:** *"the first and last frames match perfectly, even though the
camera is in totally different spots compared to the beginning."* **Match frames, not positions.**
**Spec fields used:** `beats[0]` and `beats[-1]` marked as loop keys; camera path start and end
annotated `opening frame — loop key` / `closing frame — must MATCH t=0`.

#### What we proved building one (2026-09-13)

A loop is a *claim*, and building one exposed three failure modes that are each invisible in any
single frame. All three are now checked automatically.

| Failure | Why it is invisible | Guard |
|---|---|---|
| **A cast member travels and never returns.** A performer who walks 2 m in 15 s cannot be in the same place at the closing frame. | Every individual frame looks correct; the loop only breaks on replay. | Spec validator rejects travelling cast in a loop; move the performer by *camera* motion and describe their walk in the prompt (P-03). |
| **Bezier ease at the path endpoints.** `AUTO_CLAMPED` handles ease into the first key and out of the last — which stalls the camera exactly where the seam is. | The path looks smooth and correct in the graph editor. | Flat `VECTOR` handles on the first and last keys of the camera, target and drift rig. |
| **Handheld drift not zero on the seam frames.** Drift that happens not to reproduce its opening value at `frame_end` displaces the closing frame. | The two frames look near-identical to the eye. | Harmonic frequencies chosen to complete whole cycles across the shot, plus the drift forced to exactly zero on both seam frames. |

**Verification is the deliverable, not the render.** The builder measures the mean absolute
pixel difference between frame 1 and the final frame and classifies the seam as `seamless`
(mean ≤ 1%, ≤ 2% of pixels differing), `minor seam`, or `VISIBLE SEAM`. The verified example
in [`../../examples/demo-infinite-loop/`](../../examples/demo-infinite-loop/) reports a mean
difference of **0.0 with 0.00% of pixels differing** — pixel-identical ends.

**Design consequence worth stating plainly:** in a loop, *the camera is the only thing allowed
to travel.* The performer's movement has to be performed in place, or the loop is broken by
construction. That is a story decision as much as a technical one — and it is much cheaper to
make it in the spec than to discover it in a rejected generation.

### 4.2 The impossible mirror shot
**Problem:** a continuous take in which the camera passes through a mirror.
**Geometric solution:** build a **mirrored copy of the room with both characters moving in sync**, and
make the mirror surface an **opening, not an object**. It reads as a reflection; the camera passes
through it.
**Why it works:** the illusion is *constructed*, not *faked*. Models hallucinate reflections; geometry
does not.

### 4.3 The multi-location continuous take
**Problem:** a 30 s single take that travels street → stairs → corridor → kitchen → casino.
**Geometric solution:** build the whole journey as one connected set with a single camera path; give
**the camera and each character separate paths** so each is independently adjustable; colour-code
roles.
**Why it works:** the transitions are spatial, and the model is no longer asked to invent them.

### 4.4 The scale / macro reveal
**Problem:** a 10 cm hero, or a product reveal at the end of a chase.
**Geometric solution:** scale is a **framing** problem. Frame tiny subjects against large ones and at
macro distances; plan the final pull-back so the product is revealed *by the camera path*, not by an
edit.
**Spec fields used:** `optic.fov_diagonal_deg` changed mid-take (the source's *"shifting camera sizes
and focal lenses on the fly"*), and `beats` naming the reveal.

---

## 5. Cut grammar (when the shot is not a single take)

| Cut | Rule | Failure it prevents |
|---|---|---|
| **180-degree rule** | keep all cameras on one side of the action axis | characters swapping screen sides — the single most-reported AI video failure |
| **30-degree rule** | change camera angle by ≥30° between adjacent shots of the same subject | jump-cut feel |
| **Eyeline match** | a character looking off-screen must look toward the thing they see in the next shot | spatial incoherence |
| **Match on action** | cut mid-movement, not at rest | visible seam |
| **Cut on beat** | place cuts on musical beats when audio drives the edit | arbitrary-feeling rhythm |
| **Coverage** | for a dialogue scene, build the blockout with **specific rails, targets and cuts** — brief the agent like a camera operator, not with "make it cinematic" | characters swapping seats between cuts |

---

## 6. The blockout's obligation for a crowd scene

From the concert scene in the official tutorial — write this into any scene with more than ~4 moving
bodies:

> **The blockout's job is occupancy and orientation.** Where each body stands, and which way it
> faces. Nothing more.

- Proxies: **boxes for crowd**, a **distinctly different shape for the lead**, so roles are
  unambiguous at a glance.
- Record ring/slot counts explicitly (`10 inner / 20 middle / 36 outer`).
- **Choreography goes in the prompt**, not in the proxy animation — otherwise the model copies the
  stiff blocking and the movement dies.
- Group rather than individually rigging: the model needs *formations*, not 66 unique rigs.
