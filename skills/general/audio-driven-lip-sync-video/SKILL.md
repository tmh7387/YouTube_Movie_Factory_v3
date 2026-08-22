---
name: audio-driven-lip-sync-video
description: >-
  Generates realistic lip-synced character video by feeding a video model an
  audio track alongside a face reference, using the Performance Anchor method —
  a still face muxed with a segment of audio into a silent anchor clip, passed
  as a video reference so the model reads the performance rather than guessing
  it. Use this whenever you need a character to speak, sing, or deliver dialogue
  with natural facial movement and expression — especially for music videos,
  promotional content, narrative films, or any scene requiring a talking or
  singing on-camera character. Covers phrase-aligned segmentation, anchor
  construction, the 7-section prompt structure, and phoneme-sensitive
  articulation. Trigger on: lip sync, lip-sync, character speaking, singing
  character, dialogue scene, talking head, performance anchor, music video
  vocals, sync mouth to audio.
---

# Audio-Driven Lip-Sync Character Video

Give the model the audio itself, not a description of it. A video model that
accepts an audio input animates mouth, jaw, neck and breath from the waveform,
producing a whole performance rather than a warped mouth region.

The **Performance Anchor** method makes that reliable: mux the still face
reference with the audio segment into a short clip, and pass that clip as a video
reference. The model then has the exact face and the exact performance to work
from, instead of inferring both.

## When to use
- A character needs to deliver spoken dialogue or sing in a scene
- You need realistic facial movement and expression tied to an existing audio track
- Music videos, narrative films, promotional spots, or any talking-head format
- You want to avoid the uncanny artificiality of traditional AI lip-sync overlays

## Core technique — the Performance Anchor

**1. Segment the audio on phrase boundaries, not on round numbers.**

Never cut at a clean second. Find the silence between vocal phrases and cut
there; a word chopped in half is invisible in a plan and ruins the clip.

```bash
ffmpeg -i "<audio>" -af silencedetect=noise=-30dB:d=0.1 -f null - 2>&1 | grep silence
```

Then cut, and verify:

```bash
ffmpeg -y -i "<audio>" -ss <start> -t <duration> -c:a libmp3lame -q:a 2 "segment_<NN>.mp3"
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "segment_<NN>.mp3"
```

**Segment length follows the phrase.** Whole seconds only — sub-second durations
cause sync drift.

Segments can run from about 4 seconds up to whatever the target model allows:
**Seedance 2.0 caps at 15s, Seedance 2.5 at 30s**, and some other models at 10s.
Within that range, **8-10 seconds is the usual sweet spot for coherence** — long
enough to carry a phrase and a bit of performance, short enough that the model
holds the face and the motion together. That is a rule of thumb, not a limit:
go shorter when the phrase is shorter, and longer when the phrase and the model
both support it.

Runtime available is not runtime required. A phrase that lands in 6 seconds is a
6-second segment; padding it to the ceiling costs credits and buys nothing.

**2. Build the anchor.**

```bash
ffmpeg -y -loop 1 -i "<face_image>" -i "segment_<NN>.mp3" \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -t <duration> \
  "anchor_<NN>.mp4"
```

`-loop 1` turns the still into continuous video; `-shortest` matches the audio,
with `-t` as a safety net. **Use the same face image for every anchor** — that is
what holds identity across clips.

**3. Pass the anchor as a video reference**, with the audio supplied separately
where the platform allows it. Models approximate audio from the anchor, but an
explicit audio input is cleaner.

## Two segment types

Not every shot needs an anchor.

| Type | Anchor? | Use for |
|---|---|---|
| **Performance** | Yes | The character is audibly singing or speaking on camera |
| **Narrative** | No | Mood, environment, cutaway — standard image-to-video |

Attaching an anchor to a narrative segment forces lip-sync where none belongs,
and costs credits for it.

## Prompt structure — 7 sections for performance segments

1. **Style spine + anchor** — camera, lens, aperture, palette, lighting, grain,
   frame cadence. Then the anchor and audio references. **Identical across every
   segment**, or the clips will not cut together.
2. **Setup** — character in environment, spatial position, wardrobe, props.
3. **Action** — timestamped beats whose end matches the segment duration exactly.
   Be physical: "takes two deliberate steps forward", not "walks".
4. **Camera** — shot size, angle, movement per beat, and always a clause
   preserving the face.
5. **SFX / physical detail** — only where the shot needs wind, fabric, smoke, rain.
6. **Vocal / lip-sync** — the exact lyrics or lines, an instruction to match the
   audio syllable by syllable, and anatomical description: jaw pressure, neck
   tension, breath attack. Ask for raw skin texture; name AI smoothing as the
   thing to avoid.
7. **Constraints** — at most three imperatives. More and none of them carry.

Narrative segments use sections 1, 2, 3, 4 and 7 only.

## Phoneme-sensitive articulation

Scan the lines for sounds the model reliably gets wrong, and write the mouth
shape explicitly.

| Sound | Words | Instruction |
|---|---|---|
| Bilabial P/B/M | up, bump, map, boom | full bilabial closure — lips press completely shut, visible contact, then release |
| OO vowel | choose, move, groove | lips round forward on OO |
| EE vowel | peace, free, dream | sustained EE, wide lateral lip stretch |
| TH fricative | the, this, that | tongue tip visible between teeth |

Write each one **once** for the project and reuse the same wording everywhere it
appears. Discovering wrong mouth shapes after ten clips are generated is the
expensive version of this problem.

## Two failure modes worth naming

**Conflicting instructions.** "Still and silent" plus "lip-sync to the audio"
cannot both be satisfied. Singing always wins — write the body as "nearly still"
while the face performs.

**Assumed continuity.** Every *fresh* generation is self-contained: re-describe
character, wardrobe and environment in each prompt, and repeat the physical
anchor words. The exception is extension on models that support it — there the
model reads the input clip, so name what must *not* change rather than
re-establishing the world.

## Pro tip

The reference image is the single biggest lever. Sharp, evenly lit, front-facing
or three-quarter, neutral-to-slight expression. A reference already mid-expression
or at an extreme angle gives the model less to work from, and it shows in the
mouth.

Keep failed generations. A rejected take usually shows what the prompt actually
said, which is the fastest route to fixing it.

## Workflow

1. Collect the song or dialogue audio, a clean face reference, and a character card.
2. Segment the audio on phrase boundaries; record start, end, duration, type and
   lyrics per segment.
3. Build an anchor MP4 for every performance segment, same face throughout.
4. Write one prompt per segment using the structure above.
5. Generate one segment at a time and review before continuing.
6. Assemble in an editor and **lay the original master audio underneath** —
   never ship the model's regenerated audio.

## Tool compatibility

Any video model accepting simultaneous image + audio, or a video reference.
Verified with Seedance 2.0 and 2.5. Audio from Suno or a DAW render; ffmpeg for
segmentation and anchor construction; frame interpolation afterwards if playback
looks jittery.

For the full production pipeline built on this technique — reference sheets,
lyric timing manifests, project structure — see the music-video skills rather
than this note, which is the technique alone.
