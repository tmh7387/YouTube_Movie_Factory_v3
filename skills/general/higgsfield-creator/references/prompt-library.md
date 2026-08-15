# Higgsfield Prompt Library
## Prompt Formulas by Tool: Cinema Studio 2.5, Soul Cinema, and Higgsfield Chat

---

## IMPORTANT: Cinema Studio 2.5 vs. Chat — Different Prompt Styles

Cinema Studio 2.5 takes **director's scene notes** — short, action-focused, character-centric descriptions. Camera, lens, movement, and grade are set via UI controls, not text.

Higgsfield Chat (and Soul Cinema) takes **cinematographer's full briefs** — layered, technical, detailed prompts with all visual specifications embedded in the text.

Never use the Chat-style long prompt in Cinema Studio, and never use the short scene-note style in Chat.

---

## PART 1: CINEMA STUDIO 2.5 SCENE DESCRIPTIONS

### The Scene Description Formula

Cinema Studio prompts describe **the world and what's happening in it** — the director's note on set.

```
[Environment context]. [Character @mention + action, natural and specific]. [Secondary elements / background action]. [Atmosphere or lighting note]. [Any special instruction for foreground/background layers].
```

**Key principles:**
- Use @[CharacterName] for Soul Cast actors — be specific about what they're doing
- Write as a director's note, not a prompt: "walks with measured authority toward" not "walking character"
- Describe background and foreground elements to give the AI layered world-building
- Keep to 2–4 sentences — Camera Studio handles the cinematic optics separately

### Cinema Studio Scene Description Examples

**Control Room — Executive at Display:**
```
The aviation intelligence center at night, operators at workstations, large curved display showing live flight route arcs in teal. @AS-Executive-01 stands at the center display, traces a flight anomaly arc with one hand, expression focused. Colleagues visible at peripheral stations. Soft volumetric haze from screen glow, atmosphere of quiet operational authority.
```

**Analyst — Data Interaction:**
```
Modern aviation intelligence office, city visible through floor-to-ceiling windows at blue hour. @AS-Analyst-Female-01 gestures across a large touchscreen dashboard, anomaly indicators activating as she interacts with the data. A second colleague visible in background at adjacent workstation. Teal screen light as key light, deep fill beyond.
```

**Two-Character Scene — Debrief:**
```
Aviation safety debrief room. @AS-Executive-01 stands at the head of the table, indicating a flight path replay visualization on the wall screen. @AS-Analyst-Female-01 is seated, reviewing a tablet that mirrors the wall data. Professional, focused atmosphere. Meeting room lighting, screen as secondary source.
```

**Environment Only — No Characters:**
```
Empty state-of-the-art aviation control center at 2am, all screens active showing real-time global flight data, route arcs in sky teal and light teal pulsing gently, coral anomaly indicators blinking at two route points. No people. Systems operating autonomously. Atmosphere: calm intelligence, the hum of continuous vigilance.
```

**Aerial / Tarmac — No Characters:**
```
Major commercial airport tarmac at golden hour, three aircraft in various stages of servicing, ground crew moving purposefully, runway lights beginning to activate as dusk deepens. Distant terminal building lit warm. Heat shimmer near engines of the foreground aircraft. Wide environment, sense of operational scale.
```

---

## PART 2: SOUL CINEMA PROMPTS

Soul Cinema generates cinematic-grade images using the Nano Banana Pro model with authentic film characteristics: grain, shallow DOF, mood lighting, editorial composition.

### Soul Cinema Prompt Formula

```
[Shot type + framing]. [Subject identity — specific]. [Action or state]. [Environment — specific and layered]. [Lighting description — source, color, quality]. [Atmosphere]. [Film/color grade descriptor]. [Style reference]. [Negatives].
```

### Soul Cinema Examples

**Executive Portrait — Cinematic Still:**
```
Cinematic medium close-up, shallow depth of field. A Southeast Asian male aviation authority figure in his early 50s, dark professional suit, silver-streaked hair, slight three-day stubble, positioned at 3/4 angle to camera, gaze forward with quiet command. Background: blurred floor-to-ceiling window, blue-hour city lights out of focus. Key light: cool blue-hour window backlight, rim lighting defining jawline. Fill: soft teal bounce from left side. Color grade: cool temperature, deep charcoal shadows, sky teal highlight. Film grain: subtle. Style: premium aviation brand photography, Annie Leibovitz editorial precision. No text, no watermarks, no stock photography feel.
```

**Data Visualization — Abstract Cinematic:**
```
Cinematic wide shot, deep focus. A holographic aviation safety intelligence visualization floating in a dark room — flight routes of Southeast Asia rendered as luminous arcs in sky teal and light teal, anomaly indicators pulsing in coral at two intercept points, the visualization expanding outward from center. No human subjects. Environment: pure darkness beyond the hologram. Lighting: the hologram as sole light source. Color grade: near-black, sky teal and coral as only colors, ultra-high contrast. Style: premium data visualization art direction, Minority Report × premium brand film. No text visible, no watermarks.
```

**Brand Story — Atmospheric:**
```
Cinematic 2.39:1 anamorphic wide shot. Empty airport tarmac at 5am, blue hour, a single aircraft being readied for departure, ground crew silhouetted against landing lights, vast concrete extending to horizon, city lights visible beyond airport perimeter. Camera: locked-off static. Key light: practical runway and apron lights. Color grade: deep navy shadows, amber apron light pools, sky teal in shadows. Film grain: medium — atmospheric. Anamorphic lens flare: subtle horizontal on runway lights. Style: premium airline brand film, Antonioni pacing, IMAX quality. No text, no watermarks, no stock feel.
```

### Soul Cinema — Color Transfer (Soul HEX) Integration

When Soul HEX color is active, add this note at the end of the prompt:
```
Apply color signature from [Moodboard/HEX reference name] — maintain the [deep navy / teal / coral] palette signature throughout.
```

### Available Soul Cinema Style Presets (Built-In)

These built-in presets can be selected in the Soul Cinema UI instead of prompting the style. Match to content type:

| Preset | Aviation Synergy Application |
|---|---|
| **Theatrical light** | Executive portraits, authority character shots |
| **Nature light** | Aspirational aerial / tarmac content |
| **Muted cool film** | Brand story atmospheric content (closest to AS palette) |
| **Warm contrast film** | Golden hour tarmac / airport scenes |
| **BW film** | Heritage or documentary content |
| **Mystique city** | Night cityscape / urban aviation environment |
| **Street photography** | Documentary-style training content |
| **Digital camera** | Modern clean product/tech content |

---

## PART 3: HIGGSFIELD CHAT PROMPTS (Quick Generation)

Use for: single clips, fast iteration, Higgsfield Assist conversational workflow.

### Universal Prompt Architecture (Chat)

```
[SUBJECT & IDENTITY] + [ACTION / STATE] + [ENVIRONMENT] + [CAMERA] + [LIGHTING] + [ATMOSPHERE] + [STYLE] + [NEGATIVES]
```

Always build all 8 layers. Earlier layers have stronger influence.

### Model Selection for Chat

| Use Case | Model |
|---|---|
| Cinematic brand films, atmospheric imagery | **Sora 2** |
| Character-driven content, motion-rich clips | **Kling 3.0** |
| Photorealistic product demos, training | **Veo 3.1** |
| Fast concept drafts | **Kling 3.0 Lite** |

### Sora 2 Chat Prompt Formula

```
Cinematic [aspect ratio] [shot type]. [Subject + identity]. [Action]. [Environment description + time of day]. [Camera movement]. [Lighting description]. [Atmosphere]. [Color grade tone]. [Style reference]. [Negatives].
```

**Aviation Synergy Sora 2 Example:**
```
Cinematic 16:9 wide shot. A state-of-the-art aviation safety control center at night, multiple operators at curved workstations, large curved display wall showing live flight path data in sky teal and cloud white on deep navy background, holographic route overlays active. Camera: slow cinematic push-in from 40m toward center of room. Lighting: teal screen glow as primary key, deep navy ambient, coral anomaly indicators at two stations. Color grade: deep navy shadows, sky teal primary highlights, cloud white specular. Atmosphere: volumetric haze, focused operational calm. Style: premium APAC aviation brand film, Boeing campaign × McKinsey institutional, IMAX quality. No text overlays, no watermarks, no stock footage aesthetic, no lens flare.
```

### Kling 3.0 Chat Prompt Formula

```
[Camera movement]. [Subject + identity], [specific action with motion verbs]. [Environment with movement elements]. [Lighting]. [Energy/pace]. Duration: [5s or 10s]. Negative: [exclusions].
```

**Note:** Kling prompts always lead with camera movement — this significantly improves output.

**Aviation Synergy Kling 3.0 Example:**
```
Slow cinematic push-in. A Southeast Asian male aviation authority figure in his early 50s, dark professional suit, silver-streaked hair, stands at a floor-to-ceiling window overlooking an airport tarmac at blue hour, turns deliberately toward camera with measured authority. Background: aircraft movements on tarmac, teal ambient light reflection in glass. Lighting: cool blue-hour window backlight, soft teal fill from left. Energy: composed, commanding. Duration: 5s. Negative: morphing faces, distortion, extra limbs, watermarks, text overlays, stock footage aesthetic.
```

### Veo 3.1 Chat Prompt Formula

```
Photorealistic [shot type]. [Subject + identity + exact context], [action with precision]. [Environment, specific details]. [Camera]. [Lighting setup]. [Grade]. No text, no watermarks, photorealistic, 8K detail.
```

**Aviation Synergy Veo 3.1 Example:**
```
Photorealistic medium close-up. An aviation safety software dashboard on a large curved monitor, flight data anomaly detection interface in deep navy with teal route arcs and coral alert indicators, analyst's hands visible at bottom of frame interacting with a trackpad, smooth data animation in progress. Camera: static with subtle push-in. Lighting: soft overhead diffuse with screen as secondary key. Color: deep navy interface, teal primary data, coral alerts. Photorealistic, 8K detail, no watermarks, no readable text on screen, clean aviation AI platform aesthetic.
```

---

## PART 4: PROMPT TROUBLESHOOTING

| Problem | Likely Cause | Fix |
|---|---|---|
| Output looks like stock footage | Missing prestige signal | Add: `premium aviation brand film aesthetic, Boeing campaign quality, avoid stock footage look` |
| Characters look wrong or generic | Underspecified subject | Specify: exact age range, ethnicity, clothing items, distinctive feature |
| Camera barely moves | Vague movement instruction | Use named preset: `slow cinematic push-in at 20% scale change over clip duration` |
| Colors washed out | No color grade layer | Add: `color grade: deep navy shadows, sky teal highlights, cloud white specular` |
| Too many artifacts | Scene too complex | Reduce element count; add `no morphing, no distortion` to negatives |
| Text/watermarks appear | Not excluded | Always add: `no text, no captions, no watermarks, no logos` to negatives |
| Doesn't feel cinematic | Missing film reference | Add: `anamorphic lens character` or `ARRI Alexa film science` or `shallow depth of field, natural grain` |
| Wrong tone for Aviation Synergy | Missing brand tone signal | Add: `authoritative and precision-engineered, aviation-grade intelligence aesthetic, systems-level gravitas, no startup hype` |
| Soul Cast character drifts between scenes | Inconsistent @ reference | Ensure Soul Cast actor is saved and selected in Cinema Studio library before each scene — do not rebuild |

---

## PART 5: MOODBOARD STYLE PRESETS — REFERENCE

For Aviation Synergy content that doesn't use a custom Moodboard, these built-in Higgsfield style presets are closest matches:

| Built-In Preset | Match to AS Content |
|---|---|
| **Theatrical light** | Executive portraits, authority character close-ups |
| **Muted cool film** | Brand identity, atmospheric control room content |
| **Warm contrast film** | Tarmac / aerial golden-hour content |
| **Nature light** | Aspirational outdoor aviation scenes |
| **Editorial street style** | Documentary-feel training content |
| **BW film** | Heritage, institutional authority moments |

For all official Aviation Synergy brand productions, use the custom AS Moodboard (see `brand-prompts.md`) rather than built-in presets. Built-in presets are for quick/exploratory work only.