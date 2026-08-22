# Seedance 2.5 rollout across the account-synced skills

What to change, in which skill, and why. Sourced from the 2026-08-19 ingest of
two Seedance 2.5 field breakdowns — see
`seedance-2-5-practitioner-findings.md` in this folder, which is the shared
reference the changes below point at.

These skills are **account-synced** (`~/.claude/skills/synced/`, each with a
`skillId` in `manifest.json`). A container or cloud session gets a read-only
copy, so none of this could be applied from the session that drafted it. Apply
via Customize in the Desktop app or claude.ai skill settings, whichever holds the
authoritative copy.

## The headline problem

`seedance2-director` and `seedance2-composition` contain **zero** mentions of 2.5.
They are written entirely for 2.0. Two of their hard rules are now factually
wrong, and both cost real credits:

| Skill | Line | Says | Reality in 2.5 |
|---|---|---|---|
| seedance2-director | Platform Constraints table | "**Max duration** — **15 seconds** — Seedance 2.0 supports 4-15s" | 2.5 supports **30s**. The skill caps every prompt at half the available runtime — and states a flat maximum where it should be asking which model is in use and deriving the runtime from the scene. |
| seedance2-director | Prompt Discipline Rule 1 | "AI video generators have **zero memory between generations**... Never reference other segments... Re-describe the character, wardrobe, environment in EVERY prompt" | True for fresh generations, **false for extension**. In extension the model reads the whole input clip; re-describing the world is wasted prompt budget, and the correct move is naming what must *not* change. |

Rule 1 is the subtler of the two. It isn't wrong so much as unscoped — it needs
to say "every *fresh* generation is self-contained" and carve out extension.

## Priority 1 — seedance2-director

1. **Add `references/seedance-2-5-practitioner-findings.md`** (the file in this
   folder) and reference it from the skill body the way the skill already
   references `seedance2-composition`.
2. **Replace the duration constraint with a model gate plus a derivation rule.**
   Splitting the constraint row by version is necessary but not sufficient — it
   still leaves the skill picking a number. Two changes, together:

   **(a) Add a model-selection step before mode detection.** The skill must ask
   which model the user is generating on — Seedance 2.0 (ceiling 15s) or 2.5
   (ceiling 30s) — and carry that answer as `MODEL_CEILING` through every later
   step. It must not infer the model from the scene or default silently. Where the
   user does not answer, it states the assumption it is working under and says it
   is changeable, rather than picking one quietly.

   **(b) Make runtime derived, never assumed.** `MODEL_CEILING` is an upper bound,
   not a target and not a default. The prompt must carry no absolute duration
   chosen because it is the maximum. The skill counts the beats the scene actually
   needs, gives each the screen time it needs to read, and sums them — a two-beat
   reveal that plays in 7 seconds is a 7-second prompt on either model. Where the
   derived runtime exceeds `MODEL_CEILING`, it says so and offers the real choice
   (cut beats, or split — on 2.5, extension is the cleaner split) instead of
   silently trimming. A user-named runtime overrides the derivation, but a beat
   count that does not fit it gets flagged.

   Keep "integer seconds only" — 2.5 honours integer-second timestamps, so that
   rule gets *more* important, not less.

   The `DURATION CALIBRATION` table needs the same reframing: it calibrates shot
   density against a runtime already derived, and is not a menu to pick a duration
   from. Add the 15-22s and 22-30s rows as 2.5-only, and state that shot density is
   a consequence of runtime rather than a quota — a held 30s single take is
   legitimate where the scene is built on duration rather than cutting.

   Any per-15s figure elsewhere in the skill becomes a rate. The dialogue word
   budget ("~25-30 spoken words fit into 15 seconds") is the known instance:
   restate it as ~2 spoken words per second, budgeted against the derived runtime.
3. **Scope Rule 1 to fresh generations** and add extension as an explicit
   exception, with the frame-analysis step.
4. **Add a prompt-ordering rule** for top-loading: shot count, runtime, per-shot
   beats, style, texture, negations — then the scene body. The runtime in that
   header is the derived value from item 2, never the model ceiling. This partly
   conflicts with the existing `OUTPUT SETTINGS` section, which already asks for
   duration and aspect ratio at the top; reconcile them into one ordered header
   rather than leaving two competing instructions about what goes first.
5. **Add the anti-plastic vocabulary** as a named block — optical imperfection,
   material honesty, explicit negation of the wrong register, never open or close
   on stasis, name costumes as costumes.
6. **Add a new mode for extension** (call it Mode E) alongside the existing A/B/C
   modes: input clip → frame analysis → continuation prompt naming preserved
   elements. Mode detection in Step 1 needs a branch for "user has an existing
   clip and wants more of it."
7. **Update the title, description and body** from "Seedance 2.0 Director" to
   cover both versions, and add the locked-parameter rules (editing pins ratio +
   duration; first-frame and extension pin ratio).

## Priority 2 — seedance2-composition

Currently silent on first-frame pinning, so this is an addition rather than a
correction.

1. **Add a "spatial geometry lock" section**: lock the space by description, not
   by pinning a start frame. Carry the same spatial anchors — which wall, what's
   to camera-left, what's through the window, where the practicals are — into
   every prompt of a sequence.
2. **Add the anti-pattern explicitly**: a pinned literal first frame trades
   character teleportation for the plastic look. Note the distinction between a
   reference image used as a description of the space and the same image used as
   a literal first frame.
3. **Add "open mid-motion"** to the blocking rules — never open or close on a
   held pose.

## Priority 3 — storyboard-generator

The storyboard-as-cost-gate is already this skill's stated purpose, so most of
the finding is confirmation rather than news. Two additions:

1. **Scene plate first** — generate the empty environment before any character
   panels. Specify interior/exterior, time of day, camera angle, prop states, and
   signage direction relative to camera. Don't sanitise it: overexposure and
   halation carry through and read as photographed.
2. **Split image models by job** — Seedream 5.0 Pro for plates, Nano Banana Pro
   for faces and wardrobe. Worth checking against what the skill currently routes
   to, since it is written around GPT Image 2.
3. Add "judge direction, not detail" to the gate language — image and video
   models won't agree on specifics, and treating the storyboard as a prediction
   of the final frame causes pointless re-rolls.

## Priority 4 — credit-calculator

Every Seedance row is 2.0. Add 2.5 alongside, with the observed Higgsfield
figures: ~250 credits per generation at ~$0.04/credit, roughly 800 credits ≈ $32
for a one-minute project.

Flag these as a dated snapshot, not a rate card — an unlimited-but-serialised
promo was running at the time, which distorts any per-clip average.

## Priority 5 — higgsfield-generate

Add the reference-image moderation workaround: describe wardrobe in the prompt,
supply a body reference in plain clothing, let the model layer one onto the
other. Include the caveat that this routes around an over-eager similarity filter
on original work and is not a way to launder someone else's design.

## Priority 6 — chain consumers

`video-production-planner`, `ai-music-video-director`, `scene-motion`,
`dance-motion` and `lip-sync-music-video` all reference Seedance 2.0 durations or
route to `seedance2-director`. Once Priority 1 lands, sweep them for hardcoded
15-second assumptions. `ai-music-video-director` also has
`references/verified-model-routing.md`, which needs the 2.5 entry.

## Suggested sequencing

Priorities 1 and 2 are the ones that change output today — do them together,
since the composition skill is loaded by the director on every prompt. The rest
can follow. Priority 6 is a sweep, not a rewrite, and is best done after 1 lands
so there's a single source of truth to point at.

## Not yet verified

The findings come from two creator videos, transcribed from YouTube auto-captions
rather than a Whisper pass, with proper nouns normalised by hand. Before treating
any of it as settled:

- The background-music fix was offered untested by the creator.
- Credit figures are one platform, one week, with a promo running.
- The 30s / 50-reference / ratio-range numbers come from the videos, not from
  BytePlus documentation read directly. Worth confirming against the vendor docs
  before the duration constraint in `seedance2-director` is rewritten around them.
