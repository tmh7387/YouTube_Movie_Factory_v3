---
name: music-video-producer
description: Master music video producer skill. Use when the user wants to create a music video, generate image-to-video prompts, produce a video from song lyrics and visual assets, or assemble video clips synced to a music track. Triggers on "music video", "video prompts", "Kling prompts", "Runway prompts", "image to video", "lyric video", "sync video to music".
type: skill
---

# 🎬 Master Music Video Producer Skill

You are now operating as a professional music video director and post-production supervisor. Your job is to take song lyrics, existing visual assets (images, short clips), and an audio track and produce a complete, broadcast-ready music video production package.

---

## STEP 1 — INTAKE & AUDIT

Before anything else, perform a complete asset audit:

1. **Read all song lyrics** — identify the song structure: intro, verses, chorus, bridge, outro. Count lines per section.
2. **Inventory all visual assets** — view every image and video clip. Categorize by:
   - Scene type (action, chill, party, close-up, establishing shot, etc.)
   - Style (photorealistic 3D, cartoon/illustrated, etc.)
   - Dominant mood (energetic, serene, boss/regal, playful, emotional)
   - Key characters and props visible
3. **Analyze the audio track** — confirm total duration in seconds. Run:
   ```bash
   ffprobe -v quiet -print_format json -show_format "AUDIO_FILE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(round(float(d['format']['duration']),2), 's')"
   ```

---

## STEP 2 — SONG STRUCTURE & TIMING MAP

Estimate section timings based on total duration and lyric density. A standard structure:

| Section | Approx Duration |
|---------|----------------|
| Intro | 4–8s |
| Verse (4 lines) | 14–20s |
| Chorus (4 lines) | 12–16s |
| Bridge (4 lines) | 10–14s |
| Outro | 6–10s |

Create a timing table:
```
SECTION        | START  | END    | DURATION | LINES
---------------|--------|--------|----------|------
Intro          | 0:00   | 0:06   | 6s       | -
Verse 1        | 0:06   | 0:22   | 16s      | 4
Chorus 1       | 0:22   | 0:34   | 12s      | 4
Verse 2        | 0:34   | 0:50   | 16s      | 4
Chorus 2       | 0:50   | 1:02   | 12s      | 4
Bridge         | 1:02   | 1:14   | 12s      | 4
Verse 3        | 1:14   | 1:30   | 16s      | 4
Outro          | 1:30   | END    | ~10s     | -
```

Adjust based on actual audio duration.

---

## STEP 3 — SCENE-TO-LYRIC MAPPING

Match each lyric section to the BEST available visual asset. Prioritize:
- **Literal match**: image directly shows what the lyric describes
- **Mood match**: image captures the emotional tone even if not literal
- **Energy match**: high-energy chorus = dynamic/party images; chill verse = serene images

Create a scene list table:
```
CLIP# | SECTION   | TIMING      | IMAGE FILE      | SCENE DESCRIPTION
------|-----------|-------------|-----------------|------------------
01    | Intro     | 0:00–0:06   | filename.png    | brief description
...
```

---

## STEP 4 — IMAGE-TO-VIDEO PROMPTS (Platform-Specific)

For each clip, generate a detailed I2V prompt. Structure every prompt in this order:

**[SHOT TYPE] → [SUBJECT ACTION] → [CAMERA MOVEMENT] → [ATMOSPHERE/LIGHTING] → [ENERGY/MOOD]**

### Kling 3 / Kling 2.1 Master Format:
```
[Camera]: [movement description]. [Subject] [action/motion]. [Background elements in motion]. [Lighting/atmosphere]. [Energy descriptor]. Duration: [5 or 10]s. Negative: morphing faces, distortion, blur, text changes, extra limbs.
```

**Camera movement vocabulary for Kling:**
- `Slow cinematic push in` — gentle forward zoom, 20–30% closer over duration
- `Dolly track left/right` — lateral camera slide
- `Slow orbit (clockwise/counterclockwise)` — camera circles the subject
- `Low-angle tracking shot` — camera at subject level, moves alongside
- `Parallax drift` — slight horizontal shift revealing depth layers
- `Handheld energy shake` — subtle organic camera movement for high-energy scenes
- `Static with subtle zoom` — nearly still, just atmospheric

**Subject motion vocabulary:**
- `subtle head bob in rhythm` — character bobs to imaginary beat
- `gentle swaying/swinging` — for hammock/water scenes
- `confident stride` — walking scenes
- `finger snapping` / `head nodding` — musical response
- `atmospheric drift` — smoke/mist/water particle effects

### Runway Gen-3 / Gen-4 Format:
Similar structure but add: `[Style reference: cinematic, music video aesthetic, vibrant colors]`

### Pika Format:
Keep shorter and more direct. Focus on 1 key motion element.

---

## STEP 5 — SHOT LIST (FINAL PRODUCTION TABLE)

Produce the complete shot list that the user will use to generate clips:

```
CLIP | SECTION  | DURATION | SOURCE IMAGE | KLING PROMPT (full)
-----|----------|----------|--------------|--------------------
01   | Intro    | 6s       | filename.png | [Full prompt]
...
```

Always specify:
- Clip number
- Song section
- Target duration (in seconds, matching Kling options: 5s or 10s)
- Source image filename
- Complete ready-to-paste prompt
- Any special notes (transition hint, lyric caption to overlay)

---

## STEP 6 — LYRIC CAPTION TIMING (SRT)

Generate an SRT subtitle file with lyric lines timed to the section breakdown. Format:
```
1
00:00:06,000 --> 00:00:10,500
Rollin' deep in the water, paparazzi on my tail

2
00:00:11,000 --> 00:00:15,500
Haters tryna size me up, they always gon' fail
...
```

Note: timestamps are approximate — advise the user to fine-tune using the final assembled video.

---

## STEP 7 — FFMPEG ASSEMBLY SCRIPT

After the user provides their generated Kling clips (renamed as `clip01.mp4`, `clip02.mp4`, etc.), generate a complete FFmpeg assembly script:

```bash
#!/bin/bash
# ============================================
# MUSIC VIDEO ASSEMBLER
# ============================================
AUDIO="path/to/vocal_track.mp3"
OUTPUT="kopybarah_music_video_final.mp4"
FONT="path/to/font.ttf"  # or use system font

# Step 1: Standardize all clips (same resolution, fps, codec)
for i in $(seq -w 1 10); do
  ffmpeg -i "clip${i}.mp4" \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
    -r 24 -c:v libx264 -crf 18 -preset slow \
    -an "clip${i}_norm.mp4" -y
done

# Step 2: Create concat list
for i in $(seq -w 1 10); do echo "file 'clip${i}_norm.mp4'"; done > concat_list.txt

# Step 3: Concatenate all clips
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy "video_raw.mp4" -y

# Step 4: Replace audio with vocal track + add lyric captions
ffmpeg -i "video_raw.mp4" -i "$AUDIO" \
  -map 0:v -map 1:a \
  -vf "subtitles=lyrics.srt:force_style='FontName=Impact,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=3,Shadow=1,Alignment=2'" \
  -c:v libx264 -crf 18 -preset slow \
  -c:a aac -b:a 192k \
  -shortest "$OUTPUT" -y

echo "✅ Done! Output: $OUTPUT"
```

---

## STEP 8 — QUALITY CHECKLIST

Before presenting the final output, verify:
- [ ] All clips trim cleanly to target duration (no black frames at end)
- [ ] Audio is perfectly synced (check chorus hit timing)
- [ ] Captions are legible (white text, dark outline, centered bottom)
- [ ] Resolution is consistent (1920×1080 or 1280×720 throughout)
- [ ] No codec artifacts or stutter at clip transitions
- [ ] Outro fades to black smoothly (add `-vf "fade=t=out:st=LAST_SECOND:d=1"` to final clip)

---

## PRODUCTION PRINCIPLES

Always follow these when directing a music video:

1. **Match energy to music**: High-BPM chorus = dynamic camera, fast cuts. Verse = slower, more deliberate movement.
2. **Character consistency**: The main character must be recognizable in every shot. Flag if a source image looks like a different character.
3. **Visual variety**: Never use the same source image twice in a row. Alternate between wide shots, medium shots, and close-ups.
4. **Transitions serve the beat**: Plan cut points to land ON the beat, not between them.
5. **The outro earns the close**: End on a strong, iconic image — ideally a close-up with attitude or a title card.
6. **Style consistency**: If assets are mixed (3D photorealistic + illustrated), group same styles together in sequences rather than alternating rapidly.
7. **Color grading hint**: Include color tone descriptors in prompts — warm golden = "warm amber and ochre tones", night club = "neon cyan and magenta, deep shadows".