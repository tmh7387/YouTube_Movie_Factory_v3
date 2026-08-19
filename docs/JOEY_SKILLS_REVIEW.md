# Review — Joey's Skill Files (081626 build)

Reviewed 2026-08-19.

Four Claude skills published free by JOEY (CTRL / noisygroup), linked from the
channel's video descriptions and distributed as a public Dropbox folder. The
author's stated position is that they are free permanently, no course or upsell,
and explicitly meant to be adapted: his encode how *he* shoots, yours should
encode how you shoot.

| Skill | Size | What it is |
|---|---|---|
| `cinema-director-v3` | 48 KB | Seedance 2.0/2.5 + Higgsfield video prompt grammar, built on a 16-slot spine |
| `banana-pro-director-30` | 128 KB | Image asset builder for Nano Banana Pro — face lock, character sheets, scene plates |
| `character-builder` | 55 KB | Photoreal character and outfit grammar, five modes |
| `story-bible-builder` | 15 KB + 3 refs | Narrative canon construction, with an explicit handoff into a prompt director skill |

Source: https://tinyurl.com/cinema-director-skills
Context: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]] in the Content Intelligence
staging folder.

---

## What each one does

### cinema-director-v3
The headline skill, rewritten for Seedance 2.5. Opens with a **target version
check** — it refuses to guess between 2.0 and 2.5 because the reference ceiling
(9 vs 50) and runtime ceiling (15s vs 30s) change the prompt's architecture, not
just its length.

The core is a **locked 16-slot spine**: header, style prefix, no-on-screen-text,
critical blocks, assets, geometry map, first frame, optics (lens as a field of
view in degrees), camera, light and colour, atmosphere, timecoded action, physics,
acting, audio, locks. Every fact lives in exactly one slot.

Its governing idea is that **the model is a physics engine, not a mood board** —
if a phrase produces no pixel and no sound, cut it. Emotion is written as muscle,
contact as deformation, scale as measurements.

It also carries a lipsync closure protocol, strobe grammar (quarantining stepped
lighting so the model doesn't return genuinely broken footage), a NO BGM audio
convention, and a story-bible handoff.

### banana-pro-director-30
The largest of the four. Six modes covering face lock, single-image outfit,
character sheets (3-panel primary, 6-panel legacy), cinematic scene plates,
a detail-face mode, and outfit replacement. Notable pieces: a locked 18% gray
seamless plate as the default for all character work, a "cinema stack" appended
to most prompts, universal render rules aimed squarely at fighting the AI
aesthetic, a night-cinema register, a mental X/Y coordinate system for
composition, and a five-paragraph cinema-prose register that replaced an earlier
tag-based grammar.

### character-builder
Narrower and cleaner than banana-pro-director, focused on faces and wardrobe.
Its most transferable ideas: separating identity from presentation as two
independent axes, a "flattering-realism ceiling" applied to every face in every
mode, an identity firewall when adding to an existing character, a re-lock rule,
and the observation that **lean prompts hold faces better** than dense ones.

### story-bible-builder
The smallest, and the one that maps most directly onto something we already
have. Builds a twelve-section canon through a staged interview, and distinguishes
two uses: a standalone reference a human reads, versus a context source that
feeds a prompt director skill. It ships three reference files (character
interview, character section format, example excerpts).

---

## What we adopted

**The shot spine** → `skills/general/seedance2-director-v2/references/shot-spine.md`

The slot architecture, the write-the-visible discipline, one-fact-one-slot,
length discipline, the per-version reference strategy, and the anti-drift rules
for long 2.5 takes. Reconciled against the official BytePlus guidance in
`seedance2-5-capabilities.md`, and mapped onto our registry: API parameters
(ratio, duration, output format) stay out of the prompt body because the adapter
sets them from `video_models.py`.

**The narrative canon layer and the handoff contract** →
`skills/general/project-bible/SKILL.md`

Our project-bible was purely visual — characters, environments, palette, rules.
It now also carries an optional `canon` layer (premise, thesis, timeline,
factions, world rules, relationships, structural engines, production rules) with
a build order, plus an explicit **Mode 1 / Mode 2** split. Mode 2 is the one that
matters operationally: what gets injected per shot is *only* the characters in
that shot, that shot's environment, the invariants, and any world rule the shot
could violate — not the whole bible. That contract is what `bible_service` and
the `project_bible` / `character_consistency` skill contexts already implement
in the backend; it just wasn't written down.

**Realism techniques** → appended to
`skills/general/seedance2-director-v2/references/seedance2-5-capabilities.md`
in the same pass as the Content Intelligence ingest: scene-plate-first, locking
space by description rather than by pinning a first frame, the anti-plastic
vocabulary, prompt top-loading, LLM frame analysis before an extension prompt.

---

## What we deliberately did not do

**We did not vendor the four skills into this repo.** They are ~264 KB of
someone else's authored work, and copying them wholesale into a private
production repo is a different act from adapting their architecture — even
under a permissive "make them yours" framing. What we took is structure and
technique, credited here and at each integration point.

If you want the originals live in Claude alongside our skills — which is the
intended use, and how the author demonstrates them — install them the normal
way from the files you already have locally. The three image/character skills in
particular (`banana-pro-director-30`, `character-builder`) have no equivalent in
this repo and are worth running as-is rather than reimplementing.

**We did not merge banana-pro-director or character-builder into anything.**
Both are image-side skills, and our image path currently runs through
`storyboard-generator`, the Higgsfield skills and
`reference_documents/core-gpt-image-2-prompt-guide-library.md`. Folding a
128 KB skill into that would be a rewrite of our image pipeline, not an
integration — and it should be a deliberate decision, not a side effect of this
task. See "worth considering" below.

---

## Worth considering next

1. **The 18% gray plate default.** Our character-sheet path has no equivalent
   standing default. If face consistency is a recurring problem, this is a cheap
   experiment.
2. **Lean prompts hold faces better.** This cuts against how our prompt builders
   currently work — they accumulate detail. Worth measuring before adopting.
3. **The strobe quarantine.** A narrow fix, but the failure it prevents (the
   model returning genuinely broken footage when asked for flashing light) is one
   we would otherwise diagnose as a model bug.
4. **Lens as field-of-view in degrees** rather than as a focal length. More
   portable across models than "shot on a 35mm", and something our camera bible
   could adopt directly.
5. **Named-DP shorthand** as a compression device in the style prefix — one name
   carrying a whole capture register. Cheap to try, easy to over-apply.
