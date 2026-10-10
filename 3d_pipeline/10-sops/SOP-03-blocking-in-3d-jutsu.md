# SOP-03 — Blocking in 3D Jutsu (server-side route)

**Stage:** S3–S5, browser variant · **Cost:** credits **per agent message** · **Prerequisite:** SOP-01
**Output:** an exported previz MP4 and/or GLB, plus the scene kept under **My Scenes**

---

## 0. When to use this route instead of Blender

| Use 3D Jutsu when | Use Blender (SOP-02) when |
|---|---|
| you are **exploring** an idea and speed matters more than repeatability | the shot will be **delivered** and must be reproducible |
| the set is complex or organic and conversational iteration is faster | the camera move is geometrically specific |
| you want a **client-facing** previz without local setup | the blockout will be restyled or reused as an asset |
| you need a scene built from a **reference image** or from **existing footage** | you need exact coordinates, focal lengths and frame numbers |
| you have no machine capable of local 3D work | you want the blockout to be version-controlled and diffable |

**Costing note that changes behaviour:** 3D Jutsu is billed **per agent message**, and the
model selector sets the price. `Auto` is free; **GPT 6 Astra is roughly 17 credits per turn**
— over 40× the cheapest paid model. Use a cheap model for iteration and the strong model for
the turns that matter.

---

## 1. Set the parameters before prompting

| Parameter | Values | Note |
|---|---|---|
| Model | `Auto` (free), DeepSeek V4 Flash, Seed 2.1 Turbo, Gemini 3.5 Flash, Gemini 3.1 Pro, GPT 5.6 Sol, Claude Opus 5, Claude Fable 5.1, **GPT 6 Astra**, GLM-5.3 Flash | switchable per chat; the price is per message |
| Duration | **1–60 s** (default 15) | scene time, not render time |
| Aspect | 16:9, 9:16, 1:1, 4:3, 3:4, 21:9 | set at creation; changing later means a new scene |
| Behaviour mode | *generate without asking* / *ask before generating* / *ask* (answers only) | **use "ask before generating" for anything expensive** — the agent asks before each generation, which is the cheapest possible guard rail |

---

## 2. Write the blockout prompt

Full template: [`PROMPT_TEMPLATES.md` T1](../30-library/prompt-vault/PROMPT_TEMPLATES.md).
The published house style is unusually explicit, and every element of it exists to close a
specific ambiguity. Extract these moves rather than writing free prose:

| Move | Why |
|---|---|
| **Duration + aspect as literal tokens** (`8 seconds, 16:9.`) | not prose — the agent reads them as parameters |
| **Hard negatives in caps, with a rationale** (`NO arms and NO hands: none rendered, nothing at the shoulders`) | a bare prohibition invites the model to resolve the ambiguity by adding the thing |
| **Explicit framing with its exclusions** (`no legs, no waist`) | stops the agent widening the shot to "help" |
| **A camera target placed separately from the subject** | the highest-leverage instruction in the whole grammar; framing then survives the move |
| **A named rig** (`CAMERA = robo-arm`) | imports a movement grammar in two words |
| **Bidirectional collision rules** | catches both occlusion failures in one line |
| **A continuous performance state**, not a pose | the subject is active throughout, not frozen |
| **A negative style tail** | stops the agent decorating with grain, flare, vignette, neons |

---

## 3. Iterate the scene

Everything the agent generates lands as **editable scene data**, so refinement is on real
objects rather than a full regeneration. Tools available in the workspace:

- **Add object** — primitives (sphere, cube, pyramid), lights (sun, point, spot), cameras.
- **Asset library** — curated GLB assets and **Mixamo characters** drop into the active scene.
- **Scene properties** — background colour, resolution, light intensity; full object hierarchy.
- **Animation** — a timeline with a playhead; motion from camera trajectory, an animated
  character, or a GLB imported with its animation.
- **Camera work** — presets and **trajectory editing**; `Esc` returns from camera view.
- **Revision history** — every editing session saves as a revision; preview a checkpoint or
  restore it as a new head.

**Two conventions worth adopting verbatim from the official workflow:**
1. **Colour-code the roles** so occupancy is readable at a glance — the tutorial used black
   for one character, white for another, yellow for a third worker group. This pipeline's
   standard is lead red / support blue / crowd grey, matching the Blender route so blockouts
   read the same whichever tool built them.
2. **Tier the cast treatment** — hero characters get reference sheets; background characters
   are *described in the prompt only*. Do not spend reference slots on extras.

**Position in the blockout, choreography in the prompt.** A blockout that animates a dance
produces a dance that looks like a blockout. Give the agent occupancy and orientation; direct
the movement quality in the L3 prompt (pattern P-03).

---

## 4. A route only 3D Jutsu offers: deconstruction

A **reference video can be supplied** and the workspace extracts the blocking and camera move
from the footage. That makes 3D Jutsu usable as a *deconstructor* as well as a builder —
useful for matching an existing shot's movement without hand-authoring the path.

Treat this as an acceleration of Stage S3, not a replacement for it: extracted paths still
need the four review checks in [`SOP-02`](SOP-02-blocking-in-blender.md) §3.

---

## 5. Export

Three export forms: **animated MP4**, **static frame**, or **GLB** — with dimensions and file
size set before the render. **No published price exists for any of these**, so measure the
first one and log it in `MODEL_NOTES.md`.

Export rules that matter downstream:

- **The clean previz is the model-facing artefact.** If you annotate for a human review,
  export a second, unannotated version for generation. Feed the annotated one and the burn-in
  leaks into the render.
- **Match the aspect to the delivery aspect.** Genjutsu has no aspect parameter — output
  inherits the driver's.
- **The GLB is the portable asset.** It carries geometry (and animation, if exported) into
  other tools, which is how a 3D Jutsu scene becomes a reusable library environment.

---

## 6. Hand off to generation

**Do this in the same conversation.** The official workflow puts the previz render, the
character reference and the location reference **in one chat** and asks the agent in a single
message to combine them. Splitting them across sessions loses the binding between reference
and role.

Ask for the **two-render variant** in one request — the native 3D render *and* a model
generated version from the exact same camera. It costs one round trip and gives a genuine A/B
between "3D render" and "AI realisation", which is the cleanest quality comparison available.

Then continue at [`SOP-04`](SOP-04-generation-and-delivery.md).

---

## 7. Cost discipline for this route

| Lever | Effect |
|---|---|
| Use `Auto` or a cheap model for iteration; switch up for the final turns | the model selector is the single largest cost lever here |
| Set **"ask before generating"** | prevents an autonomous agent spending without a decision |
| Reuse scenes | scenes persist under **My Scenes**; a scene reused is a scene not rebuilt |
| Export a GLB for anything reusable | moves the work into the free local route for subsequent shots |
| Do not iterate in the browser what you could iterate in Blender for free | local code-driven iteration is ~free |

**Rule of thumb:** if a scene will serve more than two shots, build it in Blender (free,
deterministic, versioned) and treat 3D Jutsu as the exploration tool. If it is a one-off
concept board, 3D Jutsu is faster and the credit cost is the price of that speed.
