# Handover prompt — apply the full Seedance 2.5 rollout to the account-synced skills

Paste everything between the PROMPT STARTS / PROMPT ENDS markers into a Claude
session on claude.ai (or the Desktop app) that can reach your skill settings.

It is self-contained. It does not reference this repo, and it carries the full
text of every block that needs to go in — including the whole practitioner
findings reference, so the online session can create that file without seeing it.

This covers the **complete** rollout: all six priorities from `README.md` in this
folder, not just the duration fix.

It is long on purpose. Work through it in the order given — the ordering matters,
because Priority 1 creates the reference file every later priority points at.

---

## PROMPT STARTS HERE

I need you to roll a set of field findings into several of my skills. The
findings come from two creator breakdowns of Seedance 2.5 that I ingested into my
knowledge base. My skills were all written for Seedance 2.0 and are now wrong in
places that cost me real credits.

There are six priorities below. Do them in order. Priority 1 creates a shared
reference file that Priorities 2-6 depend on.

### How I want you to work

1. **Report before editing.** For each skill: search it, show me what you found
   and what you propose to change, then wait for my go-ahead. Do not batch all
   six priorities into one edit.
2. **Never drop trigger phrases** from a skill's `description` frontmatter while
   rewording it. Losing a trigger means the skill stops firing. If you rewrite a
   description, list the trigger phrases before and after so I can compare.
3. **Show me a before/after** of each changed section.
4. **Do not invent capability claims.** Everything factual in this rollout comes
   from the reference file in Priority 1. If you think something is wrong, say so
   rather than smoothing it over — see "What is not verified" at the end.
5. **If a skill does not contain what I describe**, say so and stop on that skill.
   Do not approximate. My description of each skill's internals may be stale.

---

## PRIORITY 0 — Inventory before you touch anything

**Read this first. It governs every change below.**

I do not know which build of these skills is in my account. The section names and
reference filenames I use below come from copies on my workstation, and I have at
least three builds here that disagree with each other — one has a
`DURATION CALIBRATION` table and no storyboard mode, another has storyboard mode
and four reference files but no duration table at all.

So treat every name I give you as a **hint, not a guarantee**.

For `seedance2-director`, report the following and then stop:

1. **Structure.** Does the skill have reference files, or is it a single
   `SKILL.md`? List every reference file by name.
2. **Headings.** List every top-level and second-level heading in `SKILL.md`.
3. **Search hits.** Search the skill body and every reference file for each of the
   following, and quote what you find along with the heading it sits under:
   - `15s`, `15 second`, `4-15`
   - `max duration`, `maximum duration`, `duration limit`
   - `zero memory`, `no memory`, `between generations`
   - `OUTPUT SETTINGS`
   - `DURATION CALIBRATION`
   - `Platform Constraint`
   - `Seedance 2.0`

Show me that inventory. I will tell you which of the changes below map onto what
you actually found before you edit anything.

### Three rules that apply to every change below

- **Where I name a section or file that does not exist, do not approximate.** Do
  not create a near-match silently and do not rename an existing section to fit my
  description. Tell me it is missing and propose where the content should go.
- **Where the skill has no `references/` folder**, the reference content in 1.1
  goes inline into `SKILL.md` as its own section rather than being dropped.
- **Where a section exists under a different name** but carries the content I
  describe, use the one that is actually there and tell me what it is called.

---

## PRIORITY 1 — `seedance2-director`

This is the skill with the actual errors. Everything else is addition.

### 1.1 — Create the shared reference file

**If the skill has a `references/` folder**, add a new file to it at
`references/seedance-2-5-practitioner-findings.md`, and point at it from the skill
body wherever the skill lists its reference files — there is usually a "read these
first" step near the top. Add it to that list with a one-line description matching
the style of the entries already there.

**If the skill has no reference files**, put the content inline in `SKILL.md` as
its own top-level section instead, placed after the skill's opening material and
before its first procedural step. Do not drop it, and do not create a
`references/` folder if the skill is not built that way.

Either way the content is the same. The complete text follows — use it verbatim.

````markdown
# Seedance 2.5 — capabilities and practitioner findings

Sourced from two field breakdowns:

- JOEY (CTRL / noisygroup), *The Cheat Codes to Prompting for True Realism with
  Seedance 2.5* — https://www.youtube.com/watch?v=5dWgZDka3Ww
- GenAI with Keera, *How I Made a 1-Minute AI Film With Only 2 Prompts* —
  https://www.youtube.com/watch?v=OFD9blyx204

Model id `dreamina-seedance-2-5-260628`, served through BytePlus ModelArk and
resold via Higgsfield and CometAPI.

## What changed from 2.0

| | 2.0 | 2.5 |
|---|---|---|
| Timestamps | ignored — shot numbers only | integer-second timestamps honoured |
| Max duration | ~15s | **30s** |
| Reference assets | a handful | up to 50 (≤30 images, ≤10 videos, ≤10 audio) |
| Aspect ratios | six fixed | any ratio in [0.4, 2.5] |
| Multi-view subject refs | discouraged | supported |
| Editing / extension | — | instruction editing, forward/backward extension |
| Output | up to 4K | 1080p as observed in both sources |

BytePlus positions this as a production-workflow upgrade rather than a
generational leap — the 2.0→2.5 step is smaller than 1.5→2.0.

Beyond straight generation: 3D clay-model reference (grey-box animatic rendered
into finished style), multi-panel storyboard reference, strict keyframe
reference, instruction-based video editing, forward/backward extension, seamless
transition between two clips, and one-click assembly from a set of stills.

**Locked-parameter rules.** Editing pins both ratio and duration; first-frame and
extension tasks pin ratio. Violating these rejects the request outright.

## Prompt ordering — top-load what must be honoured

What sits at the head of the prompt is held to most reliably, in both image and
video models. Anything you cannot afford to lose belongs at the top, not buried
after three paragraphs of scene description.

Order:

1. Shot count
2. Total runtime, and seconds per shot
3. What happens in each shot — one line each
4. Style — photorealism, organic film grain, halation, high dynamic range, shot
   on large format film
5. Texture — matte non-reflective surfaces, lived-in worn materials
6. Explicit negations of the wrong register — not a 3D render, not a game engine,
   not a game-cutscene aesthetic

Then the scene body underneath.

**If a constraint is being ignored, move it up before rewording it.** Reported
case: background music bleeding into generations unasked; the suggested fix is
positional — put `NO MUSIC WHATSOEVER` / `NO BGM (Background Music)` on the first
line rather than the last. Offered untested by the creator, but consistent with
official 2.5 guidance that negative control is reliable specifically for
subtitles and audio.

## Killing the plastic look

"Plastic" is the tell that a clip was generated rather than photographed:
surfaces too clean, light too even, motion that reads as an image being animated
rather than a scene being filmed.

**Causes.** Pinning a literal first frame; a sanitised scene plate; opening on a
held pose; no texture vocabulary, which defaults surfaces to glossy.

**Counters:**

- **Ask for optical imperfection.** Organic film grain, halation around hot light
  sources, high dynamic range, large-format film. Overexposure in the source
  plate is a feature — it carries through into the generation.
- **Ask for material honesty.** Matte non-reflective surfaces, lived-in worn
  materials. Say what things are made of and how used they are.
- **Negate the wrong register explicitly.** Naming the right look is not enough;
  name the wrong one — not a 3D render, not a game engine, not a game cutscene.
- **Never open or close on stasis.** Start the shot with the character already
  mid-action; don't end on them coming to rest.
- **Name costumes as costumes.** If a character is in a suit or creature costume,
  say so, or the model may render the creature as real — and the physics and skin
  response go with it.

## Scene plate first

Build the environment as a still **before** generating any video and before
building characters into it. Ask the image model for the empty set: the room, the
angle, the practical light sources, the signage, the state of the props. No hero
character in it.

That still is the visual bible for everything downstream — lighting, palette and
lens character are all inherited, so errors here compound.

Specify explicitly: interior/exterior, time of day, camera angle, the state of
individual props, and which direction signage faces relative to camera.

Counter-intuitively, a technically *flawed* plate often produces better video. An
overexposed plate with visible halation reads as photographed; a clean,
evenly-lit one reads as CG.

**Split image models by job.** Seedream 5.0 Pro for scene plates — better
cinematic image character. Nano Banana Pro for faces and wardrobe — face fidelity
is what Seedream doesn't hold.

## Spatial geometry lock — do not pin a first frame

**The problem.** Three clips of a character leaning on a washing machine gives
three different washing machines, in three different parts of the room, with
three different neighbouring props. Each clip is individually fine; cut together
they don't read as one location.

**The instinctive fix backfires.** Feeding a fixed start frame to every
generation does lock position — but it produces the plastic look, because the
motion inherits a still's stiffness.

**Lock the space in description instead:**

1. Establish the room once as a scene plate.
2. Carry the same spatial anchors into every prompt — which wall, which machine,
   what's to camera-left, what's visible through the window, where the practical
   lights are.
3. State where in the frame the subject sits and which direction they face.
4. Let the shot open mid-motion rather than from a held pose.

The distinction that matters: a reference image used as a *description of the
space* behaves differently from the same image used as a *literal first frame*.

## Extension as a continuity tool

2.5 grows an existing clip out to 30 seconds in either direction — sequel or
prequel. The model reads the whole input clip, so it already knows where subjects
are placed and what they look like. You are describing what happens next, not
re-establishing the world.

**The step that makes it work:** don't write the continuation prompt from memory.
Put the clip into Claude and ask it to analyse each frame — what's happening,
where everything sits — then write the continuation from that reading.

> "He looks down, takes the chocolate bar out of his pocket, starts eating, looks
> up at the mirror — his hand stays where it is on the side of the washing
> machine."

The hand note is the point. Without frame analysis you don't know the hand was
there to preserve. **Name the things that must not change, not only the new
action.** Reported as visually seamless at the join.

## Storyboard gate before video spend

Once the video prompt exists, render **one image from it** and look at that before
spending video credits. If the direction is wrong, fix the prompt — an image
costs a fraction of a video generation.

It is not a prediction of the final frame; image and video models are different
models and won't agree on detail. It is a cheap read on direction: is the
character where you thought, is the environment the one you described, does the
framing carry the idea.

Treat it as a gate, not an optional extra.

## Reference-image moderation

2.5 applies strict copyright moderation to reference images and can reject an
original design that merely resembles a known character, even when deliberately
changed. Observed: an original superhero outfit — hoodie and skirt rather than a
bodysuit — rejected as a reference image.

**Workaround:** move the design from the image channel to the text channel.
Describe the outfit in the prompt, supply a body reference in plain clothing, and
let the model layer the described outfit onto the referenced body. What tripped
the filter was the reference image, not the concept.

This is a route around an over-eager similarity filter on genuinely original
work, not a way to launder someone else's character design. If the design isn't
yours, describing it in text instead of showing it changes nothing about whether
you should be generating it.

## Observed pricing

Via Higgsfield: ~250 credits per generation at ~$0.04/credit. A one-minute
project ran to roughly 800 credits ≈ $32. An unlimited-but-serialised promo was
available at the time of the source videos — treat the credit figures as a
snapshot, not a rate card.
````

### 1.2 — Replace the duration constraint with a model gate and a derivation rule

This is the error that costs the most.

Somewhere the skill states a flat 15-second maximum as if it were an engine
limit. In the build I have seen it sits in a **Platform Constraints** table, as a
row reading roughly:

> **Max duration** — **15 seconds** — Seedance 2.0 supports 4-15s

Your build may carry it elsewhere, under another name, or only implicitly — your
Priority 0 search for `15s` / `max duration` / `4-15` will have found where. Work
from what you found, not from my description. If no such statement exists
anywhere, say so: part (a) below still applies, parts (b) and (c) may not.

It states a flat 15-second maximum as if it were an engine limit. It is not. 2.0
caps at 15s; 2.5 caps at 30s. The skill has no way to know which model I am on,
so it writes every prompt against the lower ceiling.

**Do not fix this by changing 15 to 30.** That swaps one wrong absolute for
another. The real fault is that the skill picks a duration at all.

**(a) Add a model-selection step.** Insert this immediately **before** the
existing mode-detection step (the one branching text-to-video vs image-to-video).
It has to run before mode detection, because the runtime bound shapes the shot
plan.

````markdown
## STEP 0.5 — MODEL SELECTION (Ask Before Anything Else)

Seedance 2.0 and 2.5 have different runtime ceilings. Writing a prompt without
knowing which one the user is generating on either wastes half the available
runtime or produces a prompt the engine will truncate.

**Ask, every time, unless the user has already said:**

> "Which model are you generating on — Seedance 2.0 or 2.5?"

| Model | Runtime ceiling | Notes |
|---|---|---|
| **Seedance 2.0** | up to 15s | Integer seconds only. Established camera syntax. |
| **Seedance 2.5** | up to 30s | Integer seconds only. Also supports extension of an existing clip. |

Record the answer as `MODEL_CEILING` and carry it through every later step.

**If the user does not know or does not answer**, do not guess a model and do not
guess a number. State the assumption you are making and say it is changeable —
for example: "Writing this for 2.0, so the ceiling is 15s. Tell me if you're on
2.5 and I'll re-cut the beats."

### Duration is derived, never assumed

`MODEL_CEILING` is an upper bound, not a target and not a default.

The runtime of any prompt comes from the **scene**: count the beats the scene
actually needs, give each one the screen time it needs to read, and add them up.
A two-beat reveal that plays in 7 seconds is a 7-second prompt on either model.
Padding it to the ceiling buys nothing and costs credits.

**Rules:**
- Never write a fixed duration into a prompt because it is the maximum. Write the
  duration the scene earns.
- If the derived runtime exceeds `MODEL_CEILING`, do not silently trim. Say so, and
  offer the two real options: cut beats to fit, or split across generations (on 2.5,
  extension is the cleaner split).
- If the user names a runtime, that wins over your derivation — but flag it if the
  beat count does not fit comfortably inside it.
- Round to integer seconds. Both models honour integer-second timestamps only.
````

**(b) Split whatever states the ceiling** into two, by model version — 2.0 at
4-15s, 2.5 up to 30s — and add a line immediately after it saying the ceiling is
an upper bound with the actual runtime derived per STEP 0.5. If it is a table row,
make it two rows; if it is prose, make it two sentences.

Keep "integer seconds only". Both models honour integer-second timestamps, so
that rule matters *more* at 30s, not less.

**(c) Reframe the duration calibration table — if the skill has one.** In my
build it is called `DURATION CALIBRATION` and maps duration to shot count,
signature effects and Smart Cuts, topping out at "15s (max standard)". It reads as
a menu to pick a duration from, which is the problem.

If your build has no such table, **add this as a new section** rather than skipping
it — the calibration is what stops a derived runtime from producing an unworkable
shot count. Either way, the content is:

````markdown
## DURATION CALIBRATION

Derive the runtime from the scene first (see **STEP 0.5**), then read the row it
lands in. This table calibrates shot density against a runtime you have already
worked out — it is not a menu to pick a duration from.

| Derived runtime | Shots | Signature Effects | Smart Cuts |
|---|---|---|---|
| 3-5s | 2-4 | 1 | OFF |
| 5-10s | 4-7 | 1-2 | Optional |
| 10-15s | 7-12 | 2-3 | ON recommended |
| 15-22s (2.5 only) | 12-18 | 3-4 | ON |
| 22-30s (2.5 only) | 16-24 | 4+ | ON |

Rows above 15s require Seedance 2.5. On 2.0 the ceiling is 15s — if the scene
derives longer than that, cut beats or split the generation rather than
compressing every beat below the time it needs to read.

**Shot density is a consequence of runtime, not a quota.** A 30s prompt does not
have to carry 24 shots; a held 30s single take is a legitimate choice when the
scene is built on duration rather than cutting.
````

**(d) Turn every per-15s figure into a rate.** The known instance is the dialogue
word budget.

Find:

> **Dialogue word budget:** ~25-30 spoken words fit into 15 seconds of Seedance video.

Replace with:

````markdown
**Dialogue word budget:** roughly **2 spoken words per second** of Seedance video —
so ~25-30 words at 15s, ~50-60 at 30s. Budget against the runtime you derived in
**STEP 0.5**, not against the model ceiling.
````

Search the whole skill for other per-15s figures and convert them the same way.
Tell me what you found rather than converting silently.

### 1.3 — Scope the "zero memory" rule to fresh generations

**If your Priority 0 search for `zero memory` / `between generations` found
nothing, skip this item and tell me** — my build may carry a rule yours does not.

Where it exists, the skill has a Prompt Discipline rule reading roughly:

> AI video generators have **zero memory between generations**... Never reference
> other segments... Re-describe the character, wardrobe, environment in EVERY
> prompt.

That is true for fresh generations and **false for extension**. In extension the
model reads the whole input clip, so re-describing the world is wasted prompt
budget, and the correct move is naming what must *not* change.

Rewrite the rule so it:

- applies explicitly to every **fresh** generation — each one self-contained
- carves out extension as a named exception, pointing at the new Mode E (1.6)
- states the extension move: analyse the input clip's frames first, then name
  preserved elements alongside the new action

### 1.4 — Add the prompt top-loading order

Add a rule for prompt ordering, taken from the reference file's "Prompt ordering"
section: shot count, total runtime and seconds per shot, per-shot beats, style,
texture, explicit negations — then the scene body underneath.

The runtime in that header is the **derived** value from 1.2, never the ceiling.

**If the skill has an `OUTPUT SETTINGS` section** — or anything else that already
dictates what goes at the top of a prompt, such as a rule asking for duration and
aspect ratio first — this partly conflicts with it. **Reconcile them into one
ordered header** rather than leaving two competing instructions about what goes
first, and tell me which section you merged into which.

If there is no such section, just add the ordering rule.

Include the positional-fix principle: if a constraint is being ignored, move it up
before rewording it — with the `NO MUSIC WHATSOEVER` / `NO BGM` first-line case as
the worked example, flagged as offered untested.

### 1.5 — Add the anti-plastic vocabulary as a named block

Add a named section covering the five counters from the reference file's "Killing
the plastic look":

1. Optical imperfection — organic film grain, halation, high dynamic range, large
   format film
2. Material honesty — matte non-reflective surfaces, lived-in worn materials
3. Explicit negation of the wrong register — not a 3D render, not a game engine,
   not a game cutscene
4. Never open or close on stasis
5. Name costumes as costumes

Include the causes list too, so the skill can diagnose rather than only prescribe.

### 1.6 — Add an extension mode

The skill currently has modes A/B/C. Add **Mode E — Extension**:

- **Input:** an existing clip the user wants more of, forward or backward
- **Step 1:** analyse the input clip frame by frame — what is happening, where
  everything sits, what each subject's hands and body are doing
- **Step 2:** write the continuation prompt from that reading, naming the elements
  that must not change alongside the new action
- **Constraint:** extension pins the aspect ratio

Mode detection in Step 1 needs a new branch for "user has an existing clip and
wants more of it." Add it to the decision tree, not just the prose.

### 1.7 — Title, description, and locked parameters

The skill calls itself a Seedance **2.0** skill throughout. Update the frontmatter
`description`, the title heading, and the opening "You are a Seedance 2.0
specialist" line to cover both versions.

**Keep every existing trigger phrase in the description.**

Add the locked-parameter rules as a constraint block: editing pins both ratio and
duration; first-frame and extension tasks pin ratio; violating these rejects the
request outright.

**Then update the reference files your Priority 0 inventory actually found.** Do
not go looking for files by the names I use here — I am describing them by content,
and my names come from a build that may not be yours.

- **A capabilities or model-facts reference** — whatever file describes what the
  engine can do. In my build it is `seedance2-capabilities.md` and contains the
  line "Generates up to 15 seconds at 1080p". Wherever that claim lives, it should
  say the ceiling depends on the model — 2.0 up to 15s, 2.5 up to 30s, both 1080p,
  both integer seconds only — and that the ceiling is an upper bound with the real
  runtime derived per STEP 0.5.

- **A worked-examples reference** — whatever file holds example prompts you are
  told to calibrate output against. In my build it is `prompt-examples.md`. Add a
  note at the top saying each example's runtime was derived from that scene's beats
  rather than chosen, that the reader should match the reasoning and not the
  numbers, and that the examples were written on 2.0 so none exceeds 15s.

- **Any other reference file** that states a duration, a Seedance version, or a
  capability that 2.5 changed. My build also has a camera reference and a
  storyboard-bridge reference; yours may have neither, or others. Check each one
  you found and report what needs changing before you change it.

**If either of those two references does not exist in your build, say so and stop
on that item.** Do not create a new reference file to hold the note, and do not
attach the note to an unrelated file. Tell me what you found and I will decide
where it goes.

---

## PRIORITY 2 — `seedance2-composition`

Do this together with Priority 1. The director loads this skill on every prompt,
so they have to agree.

This skill is currently silent on first-frame pinning, so this is addition rather
than correction.

### 2.1 — Add a spatial geometry lock section

Lock the space **by description, not by pinning a start frame**. Carry the same
spatial anchors into every prompt of a sequence: which wall, which machine, what
is to camera-left, what is visible through the window, where the practical lights
are. State where in frame the subject sits and which direction they face.

Use the reference file's "Spatial geometry lock" section as the source — including
the problem it solves (three clips of the same room that do not cut together).

### 2.2 — Add the anti-pattern explicitly

A pinned literal first frame trades character teleportation for the plastic look.
It does lock position, but the motion inherits a still's stiffness.

State the distinction that matters: a reference image used as a **description of
the space** behaves differently from the same image used as a **literal first
frame**.

### 2.3 — Add "open mid-motion" to the blocking rules

Never open or close on a held pose. Start the shot with the subject already
mid-action.

---

## PRIORITY 3 — `storyboard-generator`

The storyboard-as-cost-gate is already this skill's stated purpose, so most of
this is confirmation rather than news. Three additions:

### 3.1 — Scene plate first

Generate the empty environment **before** any character panels. Specify
interior/exterior, time of day, camera angle, the state of individual props, and
which direction signage faces relative to camera.

Include the counter-intuitive part: do not sanitise the plate. Overexposure and
halation carry through and read as photographed; a clean evenly-lit plate reads as
CG.

### 3.2 — Split image models by job

Seedream 5.0 Pro for scene plates; Nano Banana Pro for faces and wardrobe.

**Check what the skill currently routes to first** — I believe it is written around
GPT Image 2. Tell me what you find before changing the routing, because that may
be deliberate.

### 3.3 — Judge direction, not detail

Add this to the gate language. Image and video models are different models and
will not agree on specifics. Treating the storyboard as a prediction of the final
frame causes pointless re-rolls. It is a cheap read on direction: is the character
where you thought, is the environment the one you described, does the framing
carry the idea.

---

## PRIORITY 4 — `credit-calculator`

Every Seedance row in this skill is 2.0. Add 2.5 alongside, with the observed
figures: ~250 credits per generation at ~$0.04/credit, roughly 800 credits ≈ $32
for a one-minute project.

**Flag these as a dated snapshot, not a rate card.** An unlimited-but-serialised
promo was running when the source videos were made, which distorts any per-clip
average. Put that caveat in the skill, next to the numbers.

---

## PRIORITY 5 — `higgsfield-generate`

Add the reference-image moderation workaround from the reference file: describe
the wardrobe in the prompt, supply a body reference in plain clothing, and let the
model layer one onto the other.

**Include the caveat verbatim in spirit:** this routes around an over-eager
similarity filter on genuinely original work. It is not a way to launder someone
else's character design. If the design is not the user's, describing it in text
instead of showing it changes nothing about whether they should be generating it.

Do not add the workaround without that caveat attached.

---

## PRIORITY 6 — Sweep the chain consumers

These skills all reference Seedance 2.0 durations or route to `seedance2-director`.
This is a sweep, not a rewrite — do it after Priority 1 lands, so there is a single
source of truth to point at.

- `video-production-planner`
- `ai-music-video-director` — also has `references/verified-model-routing.md`,
  which needs a Seedance 2.5 entry
- `scene-motion`
- `dance-motion`
- `lip-sync-music-video`

For each: search the skill body and all reference files for `15s`, `15 second`,
`4-15`, `max duration`, `maximum duration`, `Seedance 2.0`, `duration`.

Report what you find in each before changing anything. Then remove hardcoded
15-second assumptions and point at the director skill's STEP 0.5 rather than
restating the ceilings locally — one source of truth, not six copies.

---

## Verification, once all six are applied

Confirm all of these and show me the evidence:

- `seedance2-director` asks which model before writing any prompt.
- No skill states a flat 15-second maximum as an engine fact.
- No skill writes a duration into a prompt because it is the maximum.
- Every per-15s budget is now a per-second rate.
- The 2.5-only rows in the duration table are marked as 2.5-only.
- `references/seedance-2-5-practitioner-findings.md` exists and is referenced from
  the director skill body.
- The "zero memory" rule is scoped to fresh generations and names extension as the
  exception.
- Mode E exists and appears in the mode-detection decision tree, not only in prose.
- `seedance2-composition` says lock the space by description, and names the pinned
  first frame as an anti-pattern.
- `higgsfield-generate` carries the moderation workaround **with** its caveat.
- `credit-calculator` marks the 2.5 figures as a dated snapshot.
- Every trigger phrase present before the edit is still present after it.

Then run two live tests:

1. Give `seedance2-director` a short scene brief. Check it asks which model, and
   proposes a runtime matching the beats in the brief rather than the ceiling.
2. Tell it you have an existing 10-second clip and want 10 more seconds. Check it
   routes to Mode E and asks to analyse the clip rather than re-describing the
   world from scratch.

---

## What is not verified

Be sceptical of these and tell me if you find better sources. All of it comes from
two creator videos transcribed from YouTube auto-captions, with proper nouns
normalised by hand — not from vendor documentation.

- **The 30-second ceiling, the 50-reference limit and the [0.4, 2.5] ratio range.**
  Check the current BytePlus / Seedance documentation before you commit to these
  numbers, and tell me if they differ. If the 30s figure is wrong, only the two
  ceilings need correcting — the model-selection gate and the derivation rule hold
  either way.
- **The background-music positional fix** was offered untested by the creator. Mark
  it as untested in the skill.
- **The credit figures** are one platform, one week, with a promo running.

If any of this conflicts with what you know or can look up, stop and tell me
rather than writing it in.

## PROMPT ENDS HERE
