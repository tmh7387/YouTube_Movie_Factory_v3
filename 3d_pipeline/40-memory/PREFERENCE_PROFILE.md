# PREFERENCE_PROFILE.md — Taste Signature

**Lives at:** `3d_pipeline/40-memory/PREFERENCE_PROFILE.md`

**Population rule:** only from **explicit** statements or signals that have **clearly repeated across
projects**. Never from a single data point. An empty section is correct until there is evidence.

This file exists so that judgement calls which recur get made once. It is the difference between a
director with a point of view and a prompt operator.

---

## Stated doctrine (explicit)

- **Process · Precision · Profession** — the three named priorities. Practical reading: a repeatable
  method beats a lucky result; accuracy beats speed; delivered work is client-grade.
- **"AI driven from A to Z"** — research, deconstruction, asset generation and assembly are all
  in-scope for AI. The pipeline should be executable end-to-end by an agent, not merely assisted by
  one.
- **Every project must feed the library.** A completed project that adds nothing reusable to the
  library is a process failure.
- **Reuse before regenerate.** Confirmed in the sibling music-video profile (*"budget options
  acceptable only with no loss in overall output quality"*) and restated as a pipeline rule here:
  cost is not the optimisation target, **quality per credit is**.

## Visual style

- *Not yet established for 3D work.* To be populated from delivered projects.
- Signals to watch for: palette temperature, contrast ratio, whether the look is clean-digital or
  filmic, tolerance for grain and flare. Note the pipeline's blockout template **defaults to
  negatives** on grain, vignette, flare and colour cast — that default is a placeholder, not a
  preference, and should be overridden per project.

## Pacing / edit rhythm

- *Not yet established for 3D work.*
- From the sources' influence: continuous single takes and beat-matched cuts are both in play.
  Whether the house style favours long unbroken moves or rhythmic cutting is an open question —
  **worth asking directly.**

## Camera language

- *Not yet established for 3D work.*
- Relevant existing evidence from the sibling domain: handheld intimacy vs locked-off composure is
  unresolved. The blockout template defaults to **handheld drift 0.015 m**, on the sources' stated
  reasoning that perfect smoothness reads as artificial.

## Recurring dislikes (avoid by default)

- **Over-stylisation** — music-video profile records this as a recurring dislike; carries forward as
  a working assumption for 3D.
- **Stiff, blockout-looking movement** — explicit in the sources and elevated to pattern P-03.
- **Wasted generations** — the entire pipeline is organised against it.

## Platform / cost preferences

- **Primary platform: Higgsfield.**
- **Primary realisation model: Seedance 2.x** for video, with **Genjutsu** now added for motion
  transfer and object swap.
- **Budget options acceptable only with no loss in overall output quality.** `seedance_2_0_mini` is
  preferred over Hailuo for anything with identity or audio continuity.
- **Local execution is preferred where it is free and deterministic** — i.e. code-driven Blender
  blockouts rather than server-side 3D generation, for anything that must be reproducible.
- **CONFIRMED 2026-09-13 — 3D Jutsu model routing.** Iterate with a cheap model (`Auto`, free, or
  Gemini Flash ~2 cr/turn) and switch to **GPT 6 Astra (~17 cr/turn)** only for the turns that set
  the final camera and shot. Rationale: 3D Jutsu bills **per agent message**, so exploratory
  iteration on Astra costs ~40× the cheapest paid model. This is a standing rule, not a
  per-project choice — apply it unless a project has a specific reason to override.
- **CONFIRMED 2026-09-13 — Phase 1 boundary.** Phase 1 ends at a documented interface plus **one
  fully proven production shot** end-to-end. YMF integration is Phase 2, scoped separately, and
  should begin from working code at the integration point rather than from a specification alone.
- **CONFIRMED 2026-09-13 — proof budget.** A one-time spend of ~1,000–1,400 credits is authorised
  to prove the L1→L3 handoff: one L2 character + location pair, then the same blockout run through
  **both** Genjutsu Motion Transfer and Seedance 2.5 to settle the routing question by measurement
  rather than by third-party claim.

---

## Open questions to resolve with the user

These are taste decisions the pipeline cannot infer, and each materially changes routing:

1. **Single continuous takes vs cut sequences** as the house default?
2. **Look target** — clean modern digital, or filmic with grain/halation? This decides whether the
   blockout template's "no grain, no vignette, no flare" default is right.
3. **Camera energy** — locked-off composure or handheld life, as the default?
4. **Delivery resolution** — is 720p from Seedance 2.5 acceptable after upscale, or is 1080p+ a hard
   requirement? This decides the L3 model tier.
5. **Music/audio** — generated with the video in the same request, or composed separately and
   conformed in post? The sources support native audio generation; a separate music pipeline may
   already be the house standard.
