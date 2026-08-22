# Handover prompt — apply the Seedance runtime fix to the account-synced skills

Paste everything between the PROMPT STARTS / PROMPT ENDS markers into a Claude
session on claude.ai (or the Desktop app) that can reach your skill settings.

It is self-contained: it does not reference this repo, and it carries every block
of text that needs to go in.

Scope: the model-selection gate and the derived-duration rule only. The rest of
the Seedance 2.5 rollout is deliberately left out — see "Not covered here".

---

## PROMPT STARTS HERE

I need you to fix a factual error that runs through several of my skills, and
replace it with a rule rather than a different number.

### The problem

My `seedance2-director` skill states a flat **15-second maximum** as if it were an
engine limit. It is not. Seedance **2.0** caps at 15s; Seedance **2.5** caps at
**30s**. The skill has no way to know which model I am on, so it writes every
prompt against the lower ceiling and throws away half my runtime on 2.5.

Do **not** fix this by changing 15 to 30. That swaps one wrong absolute for
another. The real fault is that the skill picks a duration at all.

Two things must be true when you are done:

1. **The skill asks me which model I am generating on** — 2.0 or 2.5 — and carries
   that answer forward as an upper bound.
2. **The runtime of any prompt is derived from the scene**, not chosen from a
   ceiling or a default. Count the beats the scene needs, give each the screen
   time it needs to read, sum them. A two-beat reveal that plays in 7 seconds is a
   7-second prompt on either model.

### Skills to change

Start with `seedance2-director`. Then sweep these for the same hardcoded
15-second assumption, and for any routing to Seedance that presumes a duration:

- `seedance2-composition`
- `video-production-planner`
- `ai-music-video-director` — also has `references/verified-model-routing.md`,
  which needs a Seedance 2.5 entry
- `scene-motion`
- `dance-motion`
- `lip-sync-music-video`
- `storyboard-generator` — check whether its shot-length guidance assumes 15s
- `credit-calculator` — every Seedance row is 2.0; see the note at the end

For each one, before editing, search the skill body and all its reference files
for: `15s`, `15 second`, `4-15`, `max duration`, `maximum duration`, `duration`.

Report what you found in each skill **before you change anything**, so I can see
the blast radius.

### Change 1 — add a model-selection step to `seedance2-director`

Insert this as a new step **immediately before** the existing mode-detection step
(the one that branches text-to-video vs image-to-video). It must run before mode
detection, because the runtime bound shapes the shot plan.

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

### Change 2 — fix the Platform Constraints table

`seedance2-director` has a Platform Constraints table with a row reading roughly:

> **Max duration** — **15 seconds** — Seedance 2.0 supports 4-15s

Replace that row with two rows split by model version — 2.0 at 4-15s, 2.5 up to
30s — and add a sentence directly under the table saying the ceiling is an upper
bound and the actual runtime is derived per STEP 0.5.

Keep "integer seconds only". Both models honour integer-second timestamps, so
that rule matters *more* at 30s, not less.

### Change 3 — reframe the duration calibration table

The skill has a `DURATION CALIBRATION` table mapping duration to shot count,
signature effects and Smart Cuts, topping out at "15s (max standard)".

It currently reads as a menu to pick a duration from. It must read as a
calibration applied to a runtime already derived. Replace it with:

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

### Change 4 — turn every per-15s figure into a rate

Anywhere a skill expresses a budget "per 15 seconds", restate it as a per-second
rate so it survives a 30-second prompt.

The known instance is in `seedance2-director`, in the dialogue section.

Find:

> **Dialogue word budget:** ~25-30 spoken words fit into 15 seconds of Seedance video.

Replace with:

````markdown
**Dialogue word budget:** roughly **2 spoken words per second** of Seedance video —
so ~25-30 words at 15s, ~50-60 at 30s. Budget against the runtime you derived in
**STEP 0.5**, not against the model ceiling.
````

Search each skill for other per-15s figures and convert them the same way. Tell
me what you found rather than converting silently.

### Change 5 — reconcile the prompt header

`seedance2-director` has an `OUTPUT SETTINGS` section that asks for duration and
aspect ratio at the top of the prompt. Leave that behaviour, but make explicit
that the duration written there is the **derived** value from STEP 0.5, never the
model ceiling.

If you add or already have a top-loading rule for prompt ordering (shot count,
runtime, per-shot beats, style, texture, negations, then the scene body), fold it
into that same header rather than leaving two competing instructions about what
goes first.

### Change 6 — title and description

`seedance2-director` describes itself as a Seedance **2.0** skill throughout.
Update the frontmatter `description`, the title heading, and the opening
"You are a Seedance 2.0 specialist" line so the skill covers both 2.0 and 2.5.

**Keep every existing trigger phrase in the description.** Do not drop trigger
coverage while rewording.

Do the same for its reference files. A `seedance2-capabilities.md` (or
equivalent) that says "Generates up to 15 seconds at 1080p" should say the
ceiling depends on the model — 2.0 up to 15s, 2.5 up to 30s, both 1080p, both
integer seconds only — and that the ceiling is an upper bound, with the real
runtime derived per STEP 0.5.

If there is a worked-examples reference, add a note at the top saying each
example's runtime was derived from that scene's beats rather than chosen, that
the reader should match the reasoning and not the numbers, and that the examples
were written on 2.0 so none exceeds 15s.

### How I want you to work

1. **Report before editing.** For each skill, show me what the search found and
   what you propose to change. Wait for my go-ahead.
2. **Never drop trigger phrases** from a skill description while rewriting it.
3. **Do not touch anything outside the duration and model-selection concern.**
   Other parts of these skills are being revised separately and I do not want the
   changes tangled.
4. **After each skill, show me a before/after of the changed sections.**

### Verification, once applied

Confirm all of these:

- `seedance2-director` asks which model before writing any prompt.
- No skill states a flat 15-second maximum as an engine fact.
- No skill writes a duration into a prompt because it is the maximum.
- Every per-15s budget is now a per-second rate.
- The 2.5-only rows in the duration table are marked as 2.5-only.
- Every trigger phrase present before the edit is still present after it.

Then run one live test: give `seedance2-director` a short scene brief and check
that it (a) asks which model, and (b) proposes a runtime that matches the beats
in the brief rather than the ceiling.

### One thing to verify independently

The 30-second figure for Seedance 2.5 comes from creator videos transcribed from
YouTube auto-captions, **not** from BytePlus documentation. Before you commit to
it, check the current BytePlus/Seedance docs for the real 2.5 maximum duration
and tell me if it differs.

If that number is wrong, only the two ceilings need correcting — the
model-selection gate and the derivation rule hold either way.

Same caveat for `credit-calculator` if you touch it. The figures I have (~250
credits per generation, ~$0.04/credit, ~800 credits ≈ $32 for a one-minute
project) are one platform, one week, with a promotion running. Add them as a
dated snapshot, not a rate card.

## PROMPT ENDS HERE

---

## Not covered here

These are separate items from the same rollout. Do them in their own pass so the
duration fix stays reviewable on its own:

- **Extension mode** for `seedance2-director` (Mode E: input clip → frame analysis
  → continuation prompt naming preserved elements), and scoping the "zero memory
  between generations" rule to fresh generations only.
- **The anti-plastic vocabulary block.**
- **Spatial geometry lock** and "open mid-motion" for `seedance2-composition`.
- **Scene-plate-first** and the image-model split for `storyboard-generator`.
- **Reference-image moderation workaround** for `higgsfield-generate`.

Full detail for each is in `README.md` in this folder.
