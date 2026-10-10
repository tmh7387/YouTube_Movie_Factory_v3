# PATTERNS.md — Promoted Reusable Patterns

**Lives at:** `3d_pipeline/40-memory/PATTERNS.md`

A pattern earns a place here when it has proved out across **2+ projects**. Each entry records the
pattern, when to apply it, why it works, and the first project that surfaced it.

This file is the distilled layer. When it accumulates 5+ stable patterns, they get baked into
[`../30-library/`](../30-library/) templates and the SOPs, and the cycle repeats.

**Promotion rule:** a `LESSONS.md` entry becomes a `PATTERNS.md` entry only when it has held on a
second, independent project. Single-project successes are anecdotes; the whole point of this file is
to separate method from luck.

---

## P-01 — Blockout-first sequencing

**Status:** seeded from source evidence (3 independent sources), **awaiting our own 2-project proof**
**When to apply:** every shot, without exception, where a camera move or spatial continuity matters.
**What it is:** solve space, camera and time in 3D before any generation spend. The blockout becomes
the motion reference handed to the realisation layer. Gate 2 in the pipeline architecture enforces it.
**Why it works:** text prompts make a video model *guess* at spatial logic, so the camera drifts, the
180° line breaks and characters swap seats. Given a blockout, the model stops guessing — it has a
camera path, a timeline and occupancy to follow.
**Evidence:** official Higgsfield tutorial (5 scenes), askNK (connector demo + playblast handoff),
Gachoki (dialogue scenes: "six characters, zero seat swaps"). Independently converged.
**First project:** *pending* — this pipeline's first production shot.

---

## P-02 — Structure/style separation (the blockout as capital)

**Status:** seeded from source evidence, **awaiting our own proof**
**When to apply:** any project where more than one visual direction is needed, or where a client is
choosing a look.
**What it is:** a blockout has two layers — **structural** (cuts, camera moves, timing) and **style**
(what the world looks like). Hold the structural layer fixed and swap the style layer's assets. The
same sequence regenerates photoreal, 2D-ink, or stylised-toy with **frame-for-frame matching cuts and
camera drift**.
**Why it works:** the expensive, judgement-heavy part of the work is the structure. Style is
reference assets — cheap to replace, expensive to re-derive.
**Consequence:** archive every blockout as a versioned asset, in a library, with its spec.
**Evidence:** Gachoki (19-shot sequence, three styles, frame-for-frame match); official tutorial (same
blocking, different assets per scene).
**First project:** *pending.*

---

## P-03 — Position in the blockout, choreography in the prompt

**Status:** seeded from source evidence, **awaiting our own proof**
**When to apply:** every scene with human movement, and especially crowd scenes.
**What it is:** the blockout supplies *occupancy and orientation* — where each body stands, which way
it faces. The *quality* of movement is directed in the prompt.
**Why it works:** a blockout that animates a dance produces a dance that looks like a blockout. The
model will faithfully copy stiff proxy motion, because that is what it was given. Giving it
positions and asking it for performance gets fluid movement in the right places.
**Evidence:** official tutorial, concert scene: *"I'm going to handle the actual choreography in the
prompt so the model keeps their movement fluid instead of copying the stiff blocking."*
**First project:** *pending.*

---

## P-04 — Environments as capital, shots as consumables

**Status:** seeded from source evidence, **awaiting our own proof**
**When to apply:** all multi-shot projects. This is a *pre-production grouping decision*.
**What it is:** build and version an environment once. Reuse it across shots, scenes and projects,
swapping only objects and camera. Group a project's shot list **by location** before generating
anything.
**Why it works:** one creator reported **6–8 clips from a single environment**, and that generating a
new environment per scene was the reason a 17-video project consumed ~3,000 credits. The savings are
architectural, not incremental.
**Evidence:** Zane Hoyer (2026-09-12), stated and demonstrated.
**First project:** *pending.*

---

## P-05 — Variant pair, then decide

**Status:** seeded from source evidence, **awaiting our own proof**
**When to apply:** every final generation.
**What it is:** generate exactly **two** takes of the same prompt with different seeds, score both
against the spec, select one. Never generate a fifth take before scoring the first two.
**Why it works:** take selection is a real cost lever only when the search is bounded. Unbounded
variant generation is the most common way a project burns credits without improving output. Two
takes also give a genuine A/B, which trains judgement.
**Evidence:** official tutorial states it as standing practice (*"I'm going to generate two versions
so I can choose the best one"*); the two-render request pattern from Zane Hoyer is the same idea.
**First project:** *pending.*

---

## P-06 — The previz clip is the prompt's source of truth

**Status:** seeded from source evidence, **partially implemented** in `50-toolkit/make_prompt.py`
**When to apply:** every shot with a blockout.
**What it is:** derive the final prompt's camera and timing language from the *previz clip* (or from
the `shot.json` it was rendered from), not from imagination. Where a vision pass is used, it reads
the clip frame by frame and writes the prompt second by second.
**Why it works:** the previz is a *measurement* of the shot; a prompt written from imagination is a
*guess*. A second-by-second prompt derived from measurement is mechanically checkable against the
spec — which makes it auditable rather than merely plausible.
**Evidence:** askNK: *"read the input video and write out the prompt second by second to match the
camera motion in the clip."*
**First project:** *pending.*

---

## P-07 — Front-load detail; name what must be good

**Status:** seeded from source evidence, **awaiting our own proof**
**When to apply:** every 3D scene generation prompt, and every image-generation brief.
**What it is:** put all the detail in the **first** prompt — including the phrase *"spend lots of
time on details"* — and name the two or three specific things that must be good, rather than
applying a generic quality adjective.
**Why it works:** *"if you just tell it to generate you a 3D scene, it's usually pretty basic."*
Front-loading avoids a re-prompt cycle; naming specifics gives the model something to allocate
capacity to.
**Evidence:** Zane Hoyer, stated as explicit practice.
**First project:** *pending.*

---

## P-08 — One asset, one job

**Status:** seeded from source evidence, **awaiting our own proof**
**When to apply:** every reference pack.
**What it is:** each reference carries exactly one responsibility. A character sheet carries identity
*and* wardrobe. A location plate carries set *and* light. A product reference carries form *and*
finish. Reference **roles are tiered**: hero characters get reference sheets; background characters
are *described in the prompt only*.
**Why it works:** asking one reference to carry two jobs is where drift enters — the model
compromises between them, and identity or wardrobe changes between shots. Spend reference slots only
where identity must survive across cuts.
**Evidence:** official tutorial — four detective sheets for the hero, zero for the casino's cooks,
staff and guests, who are *"described in the prompt."*
**First project:** *pending.*

---

<!-- Entry template:

## P-NN — <pattern name>
**Status:** promoted YYYY-MM-DD · proven across <project A>, <project B>
**When to apply:** <trigger condition>
**What it is:** <the method, in the imperative>
**Why it works:** <mechanism, not opinion>
**Evidence:** <projects + sources>
**First project:** <slug>
-->
