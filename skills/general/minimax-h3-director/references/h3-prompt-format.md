# MiniMax H3 — Exact Prompt Format

Field names, tag syntax and vocabulary. Everything here is literal — H3's
preprocessing was trained on these exact forms, so paraphrasing a field name or
a fixed phrase degrades adherence.

Condensed from the two official guides in the MiniMax H3 model repository on
Hugging Face (`docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md` and
`docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`).

---

## 1. Opening instruction lines (base modes)

The instruction is the **first line** of the prompt, followed by one blank line,
then the core fields. `N` is the index of the shot the picture belongs to;
`S.SS` is the effective duration to exactly two decimal places.

**T2VA** — no instruction line. Begin at `integrated_multimodal_description:`.

**I2VA**
```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
```

**FL2VA**
```
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.
```

**L2VA**
```
How the reference pictures align with the target video — <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.
```

---

## 2. Core fields (base modes)

```
integrated_multimodal_description: [Shot 1] …

overall_soundscape: …

non_diegetic_music: …
```

### Per-mode body strategy

| Mode | Structure to follow |
|---|---|
| I2VA | first-frame anchor → action onset → continuous development → result/reaction |
| FL2VA | first-frame state → observable intermediate changes → narrowing differences → last-frame state |
| L2VA | plausible preceding state → explicit transition path → convergence → landing on the image |

FL2VA favours a **single shot** so the model can interpolate continuously; only
use multiple shots when explicitly asked, and the last frame must be reached at
the end of the final shot.

For L2VA, remember `<Picture 1>` belongs to the *last* shot, not Shot 1.

### Style keywords for the `[Shot 1]` opener
`Cinematic` · `live-action` · `2D-animated` · `3D CG` · `claymation` ·
`watercolor` · `vintage film`

For keyframe modes, derive the style from the reference image. For T2VA, take it
from the user's brief.

---

## 3. Shots and cuts

- `[Shot 1]` — no timestamp, ever.
- `[Shot 2] At 00:03.500, …` — `MM:SS.mmm`, strictly increasing, inside the
  clip duration.
- Ordinary cut verbs: `the camera cuts to` · `the shot cuts to` ·
  `the shot transitions to` · `the shot changes to` · `the shot switches to`.
- Cross-dissolve, fade and wipe only when the user asks for them.
- A cut must introduce new information. Distance or a small angle change is a
  camera move, not a cut.

---

## 4. Camera vocabulary

**Motion type**

| Term | Meaning |
|---|---|
| `Zoom In` / `Zoom Out` | focal length changes, body stationary |
| `Push In` / `Pull Out` | camera body moves forward / back |
| `Pan Left` / `Pan Right` | pivots horizontally in place |
| `Truck Left` / `Truck Right` | translates horizontally |
| `Tilt Up` / `Tilt Down` | pivots vertically in place |
| `Pedestal Up` / `Pedestal Down` | whole camera rises / lowers |
| `Arc Shot` | arcs around the subject |
| `Tracking Shot` | follows a moving subject |
| `Static Shot` | position and lens both still |
| `Shake Slightly` / `Shake Strongly` | camera shake |
| `POV` | subject's point of view |
| `Roll Clockwise` / `Roll Counterclockwise` | rolls around the lens axis |

**Amplitude** — `with small amplitude` · `with large amplitude`
**Speed** — `at slow speed` · `at fast speed`

Medium amplitude and normal speed are the defaults; omit them. Write the whole
expression as a natural clause inside the shot, e.g. *"The camera trucks right
with small amplitude at slow speed as she lifts her gaze."*

---

## 5. Speech tags

```
<d>[Language] exact words here.</d>
```

- Only the language tag and the verbatim line go inside `<d>`. Speaker id,
  action and delivery stay outside it.
- Preserve original wording and punctuation. Never translate or paraphrase.
- Unintelligible spans in reused audio: write `[unclear]`, don't guess.
- Standardise punctuation to `,` `.` `?` `!`; strip tildes, emoji and decorative
  repeats. Close statements, questions and exclamations properly before `</d>`.

**Speaker ids** — `(S1)`, `(S2)`, … assigned in order of first vocal event.
Unison: `(S1,S2)`. Never renumber. Never write ids in `retention_analysis`.

**Voiceover** — use the exact phrase `says in an off-screen voiceover`, then
immediately state the on-screen character's lips remain closed.

**Across a cut** — `<scenetrans>` at both connection points, plus one of:
`continues seamlessly across the cut` · `continues uninterrupted into the next
shot` · `carries over from the previous shot` · `remains audible across the
transition`.

**Truncated by the end of the clip** — `<cutoff>`.

**On-screen text** — in double quotes, verbatim, untranslated:
`A red neon sign reading "OPEN" glows above the doorway.`

---

## 6. Full-reference mode (Ref2VA)

Six sections, in this order:

| Section | Contains |
|---|---|
| `subject_definitions` | one line per tracked reference, defining its label, role and key features |
| `summary` | one paragraph, opening with a bracketed task type |
| `retention_analysis` | one line per label with a fixed relationship marker |
| `detailed_description` | the body, in playback order, with labels inserted where they apply |
| `overall_soundscape` | ambience and physical sound |
| `non_diegetic_music` | audience-only score |

### Labels

| Label | Use for |
|---|---|
| `<Subject N>` | reusable visible content — people, animals, objects, scenes, clothing, props, VFX, styles, actions, poses |
| `<Picture N>` | an image acting as a first/last/key frame, edited keyframe, composition anchor, or storyboard plan |
| `<Video N>` | whole-video relationships — the edit source, continuation source, or structural/rhythm reference |
| `<Audio N>` | a standalone audio asset or an enabled sync track from a reference video |

One subject may draw on several assets; one asset may supply several subjects.
An image used only to define a character, scene, costume or style is cited
*inside* that subject's line, not given its own `<Picture N>` entry. `<Video N>`
and `<Audio N>` are numbered independently — matching indices imply nothing
about a shared source, and a reference video does not automatically produce an
`<Audio N>` just because it has sound.

When an audio asset maps to a target speaker, reuse that speaker's global id:
`<Audio 1> is the voice-timbre reference for <Subject 1> (S1).`

### Task types for the `summary` prefix

| Type | When |
|---|---|
| `keyframe completion` | an image is a concrete frame anchor |
| `reference generation` | an asset guides a character, scene, style, action, camera or storyboard without being a concrete frame or edit source |
| `video editing` | an existing source video is directly modified |
| `video continuation` | new content continues or extends an existing video |
| `audio reuse` | the same audio signal is reused, in whole or part |
| `audio reference` | only style, timbre, content, texture, beat or continuity is referenced |

Combine with ` + `, no repeats. Video-editing summaries begin (after the prefix)
with `The target video is an edited version of <Video 1>.`

### Relationship markers

Visual — `fully_preserved` · `partially_preserved` · `attribute_transfer` ·
`weak_reference`
Audio — `fully_copy` · `partially_copy` · `reference` · `weak_reference`

Format:
```
<Subject 1> (appears in [Shot 1], [Shot 3]): fully_preserved - …
<Picture 2> ([Shot 1] first frame): fully_preserved - …
<Video 1> (cut and pacing structure): weak_reference - …
<Audio 1>: fully_copy - …
```

Choose a marker only within the role already defined for that label. New actions
or backgrounds added to the target video are not losses of fidelity.

### Frame-anchor phrasing inside shots
`the shot begins from <Picture 1>` · `the shot's keyframe corresponds to
<Picture 2>` · `the shot ends on <Picture 3>`

### Style placement
Full-reference mode states style in one or two sentences **before** `[Shot 1]`,
unlike base mode which states it inside `[Shot 1]`.

---

## 7. Length guidance

`detailed_description` for generation tasks: **350–500 English words**.
Dialogue-dense pieces should fit the complete spoken timeline instead of hitting
a target length. Editing descriptions scale with the source video's complexity.
A single-shot clip does not automatically warrant a short description — spread
detail according to each shot's information load.

---

## 8. Worked skeleton (I2VA)

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, the mechanic shown in <Picture 1> stays crouched beside the open engine bay, preserving her coveralls, the wrench in her right hand, and the workshop layout. The camera pushes in with small amplitude at slow speed as she straightens up and wipes her forehead with her sleeve. The middle-aged mechanic with a low, even voice (S1) says: <d>[English] That's not the alternator.</d> She sets the wrench down on the wing. [Shot 2] At 00:05.000, the camera cuts to a close-up of the corroded terminal as her final word carries over from the previous shot.

overall_soundscape: A low compressor hum runs under the workshop throughout, with occasional metallic tings as tools settle. Fabric scrapes as she straightens, and the wrench lands with a dull clunk on painted metal.

non_diegetic_music: N/A
```
