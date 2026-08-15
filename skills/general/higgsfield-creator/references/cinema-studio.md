# Cinema Studio 2.5 — Complete Control Reference
## Camera Bodies, Lenses, Focal Lengths, Movements & Scene System

---

## Overview

Cinema Studio 2.5 is the first AI production environment with real optical physics, simulated lenses, and deterministic camera control. Unlike prompt-based video tools, it separates:
- **What happens in the scene** (the prompt / scene description)
- **How it's shot** (camera body + lens + focal length + movement — set via UI controls)
- **How it looks** (color grade — applied post-generation without re-render)

This separation is what makes it feel like a real production pipeline rather than a slot machine.

---

## CAMERA BODIES

Select the camera body to define the base sensor characteristics and cinematic response. Each body has a distinct look and feel.

| Camera Body | Character | Best For |
|---|---|---|
| **ARRI Alexa 35** | Clean, natural, skin-tones rich, film-science gold standard | Drama, corporate brand films, character work, any content requiring prestige |
| **RED** | Punchy, high-contrast, digital-crisp, aggressive sharpness | Tech content, product demos, digital-native marketing |
| **Panavision** | Classic Hollywood anamorphic feel, oval bokeh, lens character | Brand story films, authority/heritage content, cinematic narrative |
| **Sony Venice** | Warm, versatile, high dynamic range, naturalistic | Training content, documentary style, corporate explainers |
| **IMAX** | Extreme detail, enormous depth, epic scale | Conference display content, hero brand moments, large-format screens |
| **Additional bodies** | Various | Experiment based on aesthetic target |

**Aviation Synergy Defaults:**
- Primary brand films → **ARRI Alexa 35** (authority, prestige, naturalistic)
- Conference / large-format → **IMAX** (epic scale, maximum detail)
- Tech/product demos → **Sony Venice** (versatile, clean, modern)

---

## LENSES

Lens selection defines spatial compression, depth of field character, and the emotional "feel" of the frame.

| Lens Type | Character | What It Does |
|---|---|---|
| **Spherical** | Clean, precise, neutral | Modern corporate, product, editorial. No anamorphic distortion. |
| **Anamorphic** | Oval bokeh, horizontal lens flares, widescreen feel | Cinematic prestige, brand films, anything needing that "real movie" feeling |
| **Petzval** | Swirling bokeh, vintage glow at edges | Artistic brand content, heritage, luxury aesthetics |
| **Canon K35** | Vintage-warm, soft wide open, character | Nostalgic, editorial, warmth-focused brand content |
| **JC XL Express** | Micro-contrast, fine texture rendering | Documentary feel, detail-forward content |
| **Panavision C Series** | Classic anamorphic, flare control, Hollywood golden era | Heritage content, aspirational brand films, luxury |
| **Additional lenses** | Various characters | Match to aesthetic target per scene |

**Aviation Synergy Defaults:**
- Brand hero shots → **Anamorphic** (cinematic prestige, widescreen authority)
- Character close-ups → **Spherical** at 85mm (clean authority, no distraction)
- Training / documentary → **Spherical** at 50mm (neutral, believable, real)

---

## FOCAL LENGTHS

Focal length fundamentally changes the spatial relationship between subject and environment. Choose deliberately.

| Focal Length | Spatial Effect | Emotional Quality | Best For |
|---|---|---|---|
| **8–18mm** (ultra-wide) | Extreme environment expansion, subject distortion | Disorienting, epic scale, immersive | Opening establishing shots only — use sparingly |
| **24mm** (wide) | Environment-forward, subject in context | Aspiration, scale, freedom, motion | Tarmac/aerial wide shots, establishing scale |
| **35mm** (slight wide) | Natural spatial depth, balanced | Journalistic, grounded, real | Documentary-feel scenes, environment + character |
| **50mm** (standard) | Closest to human eye perception | Neutral, authentic, honest | Training content, procedural scenes, team shots |
| **85mm** (portrait tele) | Subject isolation, background compression | Authority, intimacy, presence | Executive portraits, character reveal shots |
| **135mm** (telephoto) | Heavy background compression, subject floats | Gravitas, power, isolation | Close-up authority moments, detail reveals |
| **200mm+** (long tele) | Subject fully isolated, shallow DOF | Surveillance feel, documentary distance | Candid-style shots, environmental context compression |

**The Focal Length × Story Rule:**
- Wide (24–35mm) = the world is big and the subject inhabits it → use for scale, aspiration, context
- Standard (50mm) = the world is real → use for training, credibility, authenticity
- Tele (85–135mm) = the subject matters above all → use for authority, CTA, character moments

---

## CAMERA MOVEMENTS (50+ Presets)

Select the movement that serves the narrative beat. Never choose randomly — every movement communicates something.

### Foundational Movements

| Movement | Direction / Effect | Narrative Use |
|---|---|---|
| **Static** | No movement | Observation, authority, meditative weight |
| **Dolly In** | Camera moves toward subject | Building tension, revealing, intimacy |
| **Dolly Out** | Camera moves away from subject | Reveal of scale, isolation, context |
| **Dolly Left / Right** | Lateral camera travel | Reveal of environment, following action |
| **Pan Left / Right** | Camera rotates on axis | Following movement, establishing geography |
| **Tilt Up / Down** | Camera pivots vertically | Revealing scale (up) or grounding (down) |
| **Zoom In / Out** | Lens zoom (not camera move) | Attention, urgency (in) or context (out) |
| **Crane Up / Down** | Camera rises or descends | Rising: aspiration, scale; Descending: arrival, gravity |
| **Arc Left / Right** | Camera orbits subject | 360 reveal, showcasing subject from all sides |

### Signature & Specialized Movements

| Movement | Effect | Best For |
|---|---|---|
| **Dolly Zoom (Vertigo)** | Zoom and dolly simultaneously — surreal compression | High-drama reveals, disorienting moments |
| **Crash Zoom** | Rapid dramatic zoom in | Urgency, alert, surprise — use very sparingly |
| **Whip Pan** | Fast pan creating motion blur transition | High energy, modern, cuts between scenes |
| **360 Orbit** | Full circle around subject | Hero moments, product reveals, character establishment |
| **Dutch Angle** | Camera tilted on diagonal axis | Unease, tension, instability |
| **FPV Drone** | First-person aerial movement | Dynamic aerial, through-the-scene travel |
| **Aerial Pullback** | Camera pulls up and backward from subject | Reveals scale dramatically, ending shots |
| **Head Tracking** | Camera follows subject's head movement | Intimate, naturalistic, follows performance |
| **Handheld** | Organic camera shake | Docuemntary authenticity, urgency, realism |
| **Hyperlapse** | Accelerated motion through environment | Time, scale, the passage of processes |
| **Hero Cam** | Low angle, slightly wide, dramatic framing | Power, authority, dynamic character presence |
| **Snorricam** | Camera attached to actor, environment moves | Disorienting, immersive, character POV |
| **Through Object In / Out** | Camera passes through a foreground element | Cinematic reveal, transitions between spaces |
| **3D Rotation** | Full 3D axis rotation | Abstract, artistic, attention-grabbing |
| **Focus Change** | Rack focus between foreground and background | Layered narrative, depth of information |
| **Super Dolly** | Extremely rapid dolly movement | High energy, urgency |
| **Jib Up / Down** | Arm-mounted camera vertical movement | Smooth vertical reveals |
| **Crane Over The Head** | Camera cranes up and over subject | Epic scale, God's-eye view |
| **Low Shutter** | Motion blur at lower shutter speed | Dreamlike, artistic, motion-forward |
| **Glam** | Slow, flattering orbit — beauty treatment | Portrait, character showcase |
| **Fisheye** | Ultra-wide distortion lens simulation | Creative/artistic, not for brand authority |
| **YoYo Zoom** | Alternating zoom in/out rhythm | Rhythmic, musical content |
| **Lazy Susan** | Slow rotation of subject in place | Product reveals, 360 character assessment |
| **Object POV** | Camera takes the POV of an object | Creative perspective, product interaction |
| **Overhead** | Top-down camera angle | Data visualization, maps, procedural content |

### Aviation Synergy Movement Playbook

For brand and marketing content, use these movement × beat pairings:

| Narrative Beat | Recommended Movement | Why |
|---|---|---|
| Opening hero — environment | **Dolly In** or **Aerial Pullback** | Draws audience in or reveals scale |
| Character introduction | **Hero Cam** + **Dolly In** | Authority, power, forward presence |
| Data / intelligence moment | **360 Orbit** or **Arc Right** | Showcases the system from all angles |
| Human expertise in action | **Head Tracking** or **Dolly Left** | Naturalistic, follows the work |
| Scale / aspiration beat | **Crane Up** or **FPV Drone** | Lifts into the world AS serves |
| Closing / CTA | **Static** or **Dolly In** | Weight, authority, call to attention |

---

## RESOLUTION OPTIONS

| Tier | Best For |
|---|---|
| **1K** | Draft reviews, internal previews |
| **2K** | Social media, LinkedIn, website, standard screens |
| **4K** | Broadcast, conference display, large-format screens, archival |

**Aviation Synergy default:** 2K for social/web content, 4K for conference and premium placements.

---

## THE SCENE & CHARACTER SYSTEM

### @ Mention System
In Cinema Studio's scene description field, reference saved Soul Cast actors using `@[ActorName]`:
```
@AS-Executive-01 studies the anomaly alert on the main display. @AS-Analyst-Female-01 approaches from the left with a tablet. The control room hums with quiet urgency.
```

- Up to 3 Soul Cast characters per scene
- Characters maintain visual identity across all angles, lighting, locations
- Name them clearly during Soul Cast setup for easy reference

### Scene Counter (1/4)
Cinema Studio structures productions as 4-scene sequences. Use all 4 slots for a complete narrative arc:
- Scene 1: Establish
- Scene 2: Develop / character
- Scene 3: Peak / action / intelligence beat
- Scene 4: Resolution / CTA

### Keyframe Interpolation
For precise control over start and end frames:
1. Upload a Start Frame image (the first frame you want)
2. Upload an End Frame image (the last frame you want)
3. AI generates all intermediate frames for smooth, controlled motion

Best used for: brand logo/mark transitions, precise character reveals, controlled environment pans.

---

## INTEGRATED COLOR GRADING

After generation, Cinema Studio 2.5 allows full color grading without re-rendering:

| Control | Function |
|---|---|
| **Color Temperature** | Warm (amber) ↔ Cool (teal) — Aviation Synergy sits cool-to-neutral |
| **Contrast** | Lift the drama or soften for accessibility |
| **Saturation** | Full brand colors or desaturated cinematic moodiness |
| **Exposure** | Correct for too-dark or too-bright generations |
| **Highlights** | Control blown whites, especially on screens/windows |
| **Film Grain** | Add authentic grain for cinema feel (use subtly) |
| **Bloom** | Soft glow around light sources — use for teal screen glow emphasis |
| **Sharpness** | Enhance detail or soften for dreamlike quality |

**Aviation Synergy Grade Preset:**
- Color Temperature: Slightly cool (lean toward teal)
- Contrast: Medium-high (deep shadows, sharp highlights)
- Saturation: 80% (not over-saturated, not muted)
- Film Grain: Low (5–10%) for cinematic texture
- Bloom: Low on screen/teal sources
- Sharpness: Medium (85mm portrait clarity, not over-sharpened)

**Apply the same grade to every clip in the project** for visual cohesion. Cinema Studio allows copying grade settings across scenes.

---

## QUICK-REFERENCE: AVIATION SYNERGY SCENE SPECS

For any Aviation Synergy production, these are the go-to defaults. Override only when the narrative demands it.

```
CAMERA BODY:  ARRI Alexa 35 (brand films) / IMAX (conference)
LENS:         Anamorphic (hero/brand) / Spherical (character/training)
FOCAL LENGTH: 85mm (character) / 35mm (environment) / 24mm (scale/aerial)
MOVEMENT:     Dolly In (intimacy/reveal) / Crane Up (scale) / Hero Cam (authority)
RESOLUTION:   2K (social/web) / 4K (conference/broadcast)
COLOR GRADE:  Slightly cool temp / High contrast / Low grain / Teal bloom
```