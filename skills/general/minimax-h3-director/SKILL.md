---
name: minimax-h3-director
description: >-
  Write MiniMax H3 video prompts in the model's native Context-IR grammar —
  integrated_multimodal_description / overall_soundscape / non_diegetic_music for
  text and keyframe modes, and the six-section subject_definitions / summary /
  retention_analysis / detailed_description form for full-reference (Ref2VA) mode.
  H3 generates video *and* native stereo audio together, so dialogue, sound design
  and score are part of the prompt, not a post step. Use this skill whenever the
  target model is MiniMax H3 or Hailuo, or when the brief needs synchronized
  dialogue, lip-sync, an authored soundscape, or a scored clip out of a single
  generation. Trigger on: MiniMax, MiniMax H3, H3, Hailuo, T2VA, I2VA, FL2VA,
  L2VA, Ref2VA, Context-IR, "native audio video", "generate video with dialogue",
  "video with sound design", or any request routed to the minimax-h3 /
  minimax-h3-local model in the video model registry.
---

# MiniMax H3 Director — Native Audio-Video Prompt System

H3 is an omni-modal model: one generation produces picture *and* 32 kHz stereo
audio. That single fact drives everything below — a prompt that describes only
what the camera sees is a half-written prompt.

Source guides (fetched, condensed):
- Base modes — `docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md` on
  https://huggingface.co/MiniMaxAI/MiniMax-H3
- Full-reference mode — `docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`, same repo
- System overview and deployment — https://github.com/MiniMax-AI/MiniMax-H3

Read `references/h3-prompt-format.md` before writing anything. It carries the
exact field names, tag syntax and camera vocabulary.

---

## STEP 1 — Pick the mode

H3 has five modes. The mode decides the prompt's first line.

| Mode | Inputs | When |
|---|---|---|
| **T2VA** | text only | No reference material. |
| **I2VA** | text + first frame | The usual pipeline case — animate a generated still. |
| **FL2VA** | text + first and last frame | The shot must land on a known end state. |
| **L2VA** | text + last frame only | You know the destination, not the opening. |
| **Ref2VA** | text + up to 9 images / 3 videos / 3 audio | Character locking, voice matching, motion transfer, editing. |

**Keyframe roles and reference roles cannot be mixed in one request.** If you
need a first frame *and* character references, the first frame has to be
supplied as a reference image and described as such in the prompt — the API
rejects the combination outright.

## STEP 2 — Write the instruction line

T2VA has none: start straight at the fields. Every other base mode opens with a
single alignment sentence stating which picture maps to which second of the
target video, then a blank line. `references/h3-prompt-format.md` has the exact
wording for each — use it verbatim, the phrasing is load-bearing.

## STEP 3 — Write the three core fields (base modes)

```
integrated_multimodal_description: [Shot 1] …

overall_soundscape: …

non_diegetic_music: …
```

**integrated_multimodal_description** is the body. Every clause must correspond
to something a viewer would see or hear. Open `[Shot 1]` with the style and
initial composition (`Live-action, cinematic, a medium-wide shot frames…`).
Later shots carry a strictly increasing cut time: `[Shot 2] At 00:03.500, the
camera cuts to…`. Shot 1 never gets a timestamp.

**overall_soundscape** is 1–4 sentences of ambience, physical action sound and
non-verbal human sound across the whole clip — wind, footsteps, fabric, impacts,
breathing. Dialogue and singing do not belong here; they live in the body.
`N/A` only for deliberate silence.

**non_diegetic_music** is 1–3 sentences of score the characters cannot hear.
Describe instrumentation, tempo, rhythm and dynamics. Do **not** write mood
words or explain what the music is doing emotionally. Music a character can hear
— a radio, a busker, a phone — is diegetic and belongs in the body. `N/A` when
there is no score.

## STEP 4 — Full-reference mode (Ref2VA) uses six sections instead

`subject_definitions` → `summary` → `retention_analysis` → `detailed_description`
→ `overall_soundscape` → `non_diegetic_music`.

Label everything you reference once, then reuse the label consistently across
all six sections: `<Subject N>` for reusable visible content, `<Picture N>` for
an image acting as a concrete frame anchor, `<Video N>` for whole-video
structure, `<Audio N>` for a copied or referenced audio signal. An image used
only to define a character does **not** get its own `<Picture N>` line — cite it
inside that subject's definition.

`summary` opens with a bracketed task-type prefix, joined with ` + ` when
several apply: `[video editing + audio reuse]`, `[reference generation]`,
`[video continuation + keyframe completion]`.

`retention_analysis` gives one line per label with a fixed relationship marker —
`fully_preserved` / `partially_preserved` / `attribute_transfer` /
`weak_reference` for visuals, `fully_copy` / `partially_copy` / `reference` /
`weak_reference` for audio.

`detailed_description` replaces `integrated_multimodal_description` and states
the style in a sentence *before* `[Shot 1]` rather than inside it. Aim 350–500
words for generation tasks; dialogue-heavy pieces prioritise fitting the whole
spoken timeline over hitting a word count.

## STEP 5 — Speakers, dialogue and lip-sync

This is where H3 earns its keep, and where prompts most often go wrong.

- Give every vocal source a stable id — `(S1)`, `(S2)`, `(S1,S2)` for unison.
  Characters who never vocalise get no id. Ids are assigned in order of the
  first actual vocal event and never renumbered.
- Establish identity at first appearance: age, gender, on/off screen, pitch,
  timbre, rate, accent.
- Everything descriptive sits **outside** `<d>`; inside `<d>` goes only a
  language tag and the exact words, punctuation preserved, never translated.

```
The young woman with a quiet, breathy voice (S1) says: <d>[English] I get off at the next station.</d>
```

- Voiceover uses the exact phrase `says in an off-screen voiceover`, and must be
  followed by a statement that the on-screen character's lips stay closed —
  otherwise H3 will animate a mouth that shouldn't move.
- A line crossing a cut gets `<scenetrans>` at both connection points plus an
  explicit continuity phrase. Speech cut off by the end of the clip gets
  `<cutoff>`.
- On-screen text — signs, banners, subtitles — goes in double quotes, verbatim,
  untranslated.

## STEP 6 — Camera

Write camera motion as natural English inside the shot, never as labels bolted
onto the end. The full expression is **type + amplitude + speed**, and amplitude
and speed are omitted when they're unremarkable:

> The camera pushes in with small amplitude at slow speed toward the folded
> letter in her hands.

Motion types: Zoom In/Out · Push In / Pull Out · Pan Left/Right · Truck
Left/Right · Tilt Up/Down · Pedestal Up/Down · Arc Shot · Tracking Shot ·
Static Shot · Shake Slightly/Strongly · POV · Roll Clockwise/Counterclockwise.

Cut only when the shot introduces new information — new subject, space, state,
viewpoint or time. If all that changes is distance or a slight angle, move the
camera instead of cutting.

---

## Hard limits (check before promising the user anything)

| | |
|---|---|
| Duration | 4–15 seconds |
| Frame rate | 24 fps |
| Audio | 32 kHz stereo, native |
| Resolution | 768P, or 2K via H3-Regenerate-2K |
| Ratios | adaptive, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 |
| Dialogue languages | 11 with stable support: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish |
| Ref2VA inputs | ≤ 9 images, ≤ 3 videos, ≤ 3 audio, ≤ 12 files total; each clip 2–15s, ≤ 15s per type |

T2VA must name a concrete ratio — `adaptive` is rejected. I2VA always resolves
to `adaptive` regardless of what you send. Ref2VA takes either.

## Where H3 fits against the other models

Pick H3 when the clip needs **synchronized dialogue, lip-sync, or an authored
soundscape out of one generation**, or when voice timbre must be matched from a
reference. It is the strongest option in the registry for performance and audio.

Pick Seedance 2.5 instead when the piece runs past 15 seconds, needs more than a
handful of references, or involves editing/extending existing footage. Pick
Kling for pure facial-performance close-ups without audio requirements.

---

## Chaining

- **Upstream** — `storyboard-generator` locks composition; `project-bible`
  supplies character and environment anchors to repeat verbatim across shots.
- **Sibling** — `seedance2-director` for Seedance targets. The grammars are not
  interchangeable; route by the model chosen in the registry, and say which
  model each prompt is for at the top of your output.
- **Downstream** — the backend adapter is
  `media_gen_service.animate_image_minimax_h3`; the model entries are
  `minimax-h3` (API) and `minimax-h3-local` (planned ComfyUI) in
  `backend/app/services/video_models.py`.

## The Context-IR caveat

MiniMax runs a hosted preprocessing system, **H3-Context-IR**, that rewrites raw
user input into exactly the grammar above before H3-Base ever sees it. It is not
open source. Calling the MiniMax API gets it for free. Running H3-Base locally
does **not** — so a local deployment either calls the hosted Context-IR endpoint
or relies on this skill to produce the rewrite. That is precisely what this
skill is for: it *is* the local Context-IR substitute.

See `docs/MINIMAX_H3_INTEGRATION_PLAN.md` for how that decision plays out in the
platform.
