# Higgsfield 3D Jutsu → Blender → Higgsfield Video: Practical Best Practices, Gotchas, Limits and Costs

**Research date:** 13 September 2026
**Method:** Public-web research only. No Discord login, no private channels, no gated communities. Every factual claim carries an inline link to its source. Claims that could not be confirmed from a primary source are marked `[UNVERIFIED]`; material behind a login/JS wall or simply not published is marked `[NOT PUBLICLY AVAILABLE]`.
**Currency convention:** Higgsfield credits convert at roughly **$0.05 / credit** (derived from official figures: 40 credits = $2.00 on the [Genjutsu pricing table](https://higgsfield.ai/blog/higgsfield-genjutsu), and 52 credits = $2.55 on the [Seedance 2.5 pricing post](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)).

**Two headline resolutions up front** (both verified directly, and both correct the brief):

1. **The "~200,000 users" figure is the Discord server's member count, not a platform user count.** Discord's own invite API returns `approximate_member_count: 193059` for guild **"Higgsfield AI"** (vanity `higgsfield`, presence **11,757** online, 225 boosts), and the guild's own description reads *"Join **190K+** creators..."* — [Discord invite API, retrieved 13 Sep 2026](https://discord.com/api/v10/invites/higgsfield?with_counts=true). So ~193k is **Discord members**, against a **self-reported platform** figure of **25–30 million users**. See [Topic 6](#6-discord--community-what-is-and-is-not-publicly-findable).
2. **The "~200 credits for a 20s Seedance 2.5 render" claim is a garbling of an official *Supercomputer* number.** Higgsfield's own [Supercomputer guide](https://higgsfield.ai/blog/higgsfield-supercomputer-guide) (3 Jul 2026) prices *"a **full end-to-end production workflow**"* at **~200 credits (~$10)**, with the animation step being Seedance 2.0 10 s 1080p at 90 credits. It is **not** a 20-second Seedance 2.5 render. See [§5.11](#511-on-the-community-claim-of-50100-credits-per-3d-environment-and-200-credits-for-a-20s-seedance-25-render).

---

## 1. 3D Jutsu mechanics: UI, agent behaviour, limits, exports, determinism

### 1.1 What it is and when it shipped

3D Jutsu is Higgsfield's AI-native 3D workspace — "scene blocking and previz" moved from desktop 3D software into the browser. It is a standalone workspace, not a plugin, and scenes live in your Higgsfield account under **My Scenes** ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu), 5 Sep 2026).

It shipped **4 September 2026**, logged in the official changelog as *"Introducing 3D Jutsu"* under Release / Platform, described as working "together with Supercomputer" ([changelog](https://higgsfield.ai/creator-hub/changelog)).

### 1.2 Scene parameters and limits (documented)

| Parameter | Documented range | Source |
|---|---|---|
| Scene duration | **1 to 60 seconds**, default **15 seconds** | [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |
| Aspect ratio | **16:9, 9:16, 1:1, 4:3, 3:4, 21:9** | [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |
| Driving LLM | Auto (free default) plus named models; **30+ LLMs** in the selector | [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |
| Object count limit | **`[NOT PUBLICLY AVAILABLE]`** — no published cap found | — |
| Polygon/mesh budget | **`[NOT PUBLICLY AVAILABLE]`** | — |
| GLB file-size cap | **`[NOT PUBLICLY AVAILABLE]`** — the guide says file size is *set before render*, not capped in public docs | [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |

Named selectable LLMs: **GPT 6 Astra, Claude Fable 5.1, Claude Opus 5, GPT 5.6 Sol, GLM-5.3 Flash**, switchable per chat ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)). GPT-6 Astra arrived the same day in Supercomputer per the changelog ([changelog, 4 Sep 2026](https://higgsfield.ai/creator-hub/changelog)); GLM-5.3 Flash *replaced Ox Alpha in Supercomputer* on 26 Aug 2026 ([changelog, 26 Aug 2026](https://higgsfield.ai/creator-hub/changelog)).

### 1.3 Agent behaviour modes

Two autonomy modes plus a read-only mode, all in the in-workspace chat panel:

- **"Generate without asking"** — the agent runs without confirmation.
- **"Ask before generating"** — it checks with you before each generation.
- **A separate "ask mode"** answers questions *without touching the scene*.

Source: [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu). The chat also accepts natural-language edits like *"move the car closer to the streetlamp, add a second character across the street"*, and the same chat sends the finished scene to video generation ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

### 1.4 Editor, asset library, Mixamo, GLB, cameras, revision history, exports

The guide's own tool table ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)):

| Tool | Documented behaviour |
|---|---|
| Scene generation | Prompt or reference → objects, layout, and light as **editable geometry** |
| Add object | Primitives (**sphere, cube, pyramid**); three light types (**sun, point, spot**); cameras added manually |
| Asset library | **Curated GLB assets and Mixamo characters** drop directly into the active scene |
| Scene properties | Background colour, scene resolution, light intensity from a side panel; **full object hierarchy visible** |
| Animation | Timeline with a playhead; motion from a **camera trajectory**, an **animated character**, or a **GLB imported with its animation** |
| Camera work | Camera **presets and trajectory editing**; **Esc** exits a camera view back to free viewport |
| Revision history | **Every editing session saves as a revision**; preview a checkpoint or **restore it as a new head** |
| Export | Animated **MP4**, **static frame**, or **GLB**, with **dimensions and file size set before render** |

Post-generation manual editing: objects move/rotate/scale/duplicate, lights swap, cameras reframe; **undo, redo and revision history apply to every change** ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

Viewport navigation: **drag to orbit, scroll to zoom, right-drag to pan** ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

**GLB round-trip is confirmed by the official FAQ:** "Yes. GLB files import into the scene with their animation intact, and finished scenes export back as GLB, animated MP4, or a static frame." ([3D Jutsu guide FAQ](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

### 1.5 Collaboration

Share invites by email as **admin, collaborator, or viewer**; team access ranges from invited-people-only to anyone with the link; revision history keeps every version restorable ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

### 1.6 Determinism / reproducibility

- **Revision history** is the documented reproducibility mechanism: every editing session is a revision, previewable and restorable as a new head ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).
- **"Recreate" links** are a documented share/reproduce mechanism — the blog's own prompt examples are published as URL-encoded `?recreate=` deep links into `https://higgsfield.ai/3d-jutsu` (see [Topic 2](#2-prompting-grammar-that-works-for-3d-scene-agents)).
- **Seeds:** `[NOT PUBLICLY AVAILABLE]` — no seed control is documented for 3D Jutsu scene generation, previz render, or GLB export.
- Because the agent is LLM-driven and the model is switchable per chat, **identical prompts across different LLMs are not guaranteed to reproduce the same scene**. This is inference from the documented design, not a published guarantee. `[UNVERIFIED]`

### 1.7 The critical bridge to Blender (documented in the 3D Jutsu guide itself)

> "the same scene layer runs in the **Higgsfield Blender plugin**: Scene Builder assembles blockouts in an open `.blend` file, on the same account and the same credits."

Source: [3D Jutsu guide, "Where does a finished scene go?"](https://higgsfield.ai/blog/higgsfield-3d-jutsu).

### 1.8 Access and plan requirements, and documented use cases

- **Scenes live in your account under My Scenes** ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).
- **Auto-model messages are free**, but a Higgsfield account and active subscription are still required — and because the agent runs on **Supercomputer**, the Supercomputer commercial gate applies: *"**It is not free.** Supercomputer is available on **paid plans only**. Most meaningful actions require **Plus or above**."* ([Supercomputer Guide](https://higgsfield.ai/blog/higgsfield-supercomputer-guide)). The 3D Jutsu guide does **not** state a plan requirement itself `[UNVERIFIED]`; this is an inference from the documented Supercomputer dependency, and it is the most likely reason a free-tier user would find 3D Jutsu gated.
- **No 3D experience required** — the official FAQ: *"No. The agent assembles the scene from a text description, and manual editing is limited to moving objects, adding primitives and lights, and framing cameras. Knowing 3D software helps but is not required."* ([3D Jutsu guide FAQ](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).
- **3D Jutsu is explicitly not a Blender plugin:** *"No, it is a standalone browser workspace. Higgsfield's Blender plugin is a separate product that works inside Blender; 3D Jutsu requires no installation."* ([3D Jutsu guide FAQ](https://higgsfield.ai/blog/higgsfield-3d-jutsu)). They share the scene layer and the credit balance, but they are two products.
- **Three documented use cases** ([3D Jutsu guide, "When can creators use it?"](https://higgsfield.ai/blog/higgsfield-3d-jutsu)):
  1. **Previz before committing** — *"compare several camera angles and lighting setups on grey boxes in minutes, then spend credits on the final render of the version that works."*
  2. **A pitch due tomorrow** — *"a rough blocked scene with a camera move communicates the idea without a production day."*
  3. **Planning multi-shot sequences** — *"block the whole scene once, then frame each shot from the same geometry, keeping spatial continuity across the sequence."*

---

## 2. Prompting grammar that works for 3D scene agents

### 2.1 The two official "Recreate" prompts, decoded verbatim

The [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) contains exactly **two** `?recreate=` links. Both were extracted from the page source and URL-decoded. They are reproduced below **verbatim**.

#### Prompt A — Step 1, the grey-proxy blockout prompt (**"recreate" link 1**)

Source URL (raw, encoded): `https://higgsfield.ai/3d-jutsu?recreate=8+seconds%2C+16%3A9....`
Decoded prompt:

```
8 seconds, 16:9. A character stands in a subway car and raps. The character has NO arms and NO hands: none rendered, nothing at the shoulders.

FRAMING: medium close-up throughout: head, shoulders and upper torso only, no legs, no waist. An invisible camera target is placed separately from the head so the head is always in frame as the camera moves.

CAMERA = robo-arm. One continuous, perfectly smooth 360-degree orbit around the character's head and shoulders at chest height, with a slight upward angle: starting front-left, sweeping around behind, continuing around the far side and returning to the front. Constant unhurried speed, near-constant radius that closes slightly on the back half. The camera never stops, never reverses, never zooms, and stays inside the subway car. Nothing passes through the camera and the camera passes through nothing: no walls, no floor, no ceiling, no poles, no seats.

CHARACTER: keeps rapping the whole time, and his head continuously turns to follow the camera through the orbit, face toward the lens the whole way, including a look over the shoulder as the camera passes behind.

Clean sharp digital image, no motion blur smear, no film grain, no vignette, no lens flare, no readable text or logos in the car, no neon, no yellow cast.
```

#### Prompt B — Step 4, the previz-driven final-generation prompt (**"recreate" link 2**)

This is the long structured prompt that consumes the previz render as `<<<video_1>>>`. Its **section grammar** is the reusable artefact:

```
SCENE CONTEXT
ACTIVE REFERENCES
  <<<image_1>>>: THE RAPPER. …
  <<<video_1>>>: THE CAMERA PATH AND THE FIGURE'S BEHAVIOR. …
LOCATION MAP
FIRST FRAME AND SPATIAL BLOCKING
  Frame map at 0.0s / 2.0s / 4.0s / 6.0s / 8.0s: …
FORMAT MODE
OPTICS
CAMERA
  0.0s to 2.0s: …
  2.0s to 4.0s: …
  4.0s to 6.0s: …
  6.0s to 8.0s: …
THE PERFORMANCE (critical, mirroring the previz figure)
  BODY / HEAD / EYES / HANDS
THE RAP (critical, delivery and text)
ACTION TIMING
  0.0s to 2.0s: LINE ONE. …
PHYSICS
LIGHTING
AUDIO
POSITIVE CONSTRAINTS
```

Key extracts, verbatim, showing how the previz is *scoped* to specific controls:

> "`<<<video_1>>>`: THE CAMERA PATH AND THE FIGURE'S BEHAVIOR. Reference controls two things: (1) the camera move… (2) the figure's behavior… **Nothing else from the previz (its grey materials, proxy geometry or lighting) is inherited.**"

And the positive-constraint block that closes the prompt:

> "He is the only person in the entire clip; the car stays empty of other passengers and no one enters.
> He matches `<<<image_1>>>` in every frame: same face, hazel eyes, hood up, all layers, strap, pendant, rings, camo skirt, check trousers and boots, **with zero drift**; the hood never comes down.
> THE CAMERA PATH MATCHES `<<<video_1>>>`: …
> THE FIGURE'S BEHAVIOR MATCHES `<<<video_1>>>`: …
> **No speed ramps, no slow motion, no freeze frames**; all motion is real time and anatomically human.
> No signage, route letters, station names, ad text, logos or readable text appear anywhere…"

Both prompts are published in full on the [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu). The full body of Prompt B (including all five frame maps, the 47° optics line, the four rap bars, and the physics/lighting/audio blocks) is reproduced in the page's second `?recreate=` link and was decoded during this research.

### 2.2 The recurring grammar rules (analysis)

Distilled from the two official prompts plus Higgsfield's other prompt guidance:

1. **Open with duration + aspect ratio as literal tokens** — `8 seconds, 16:9.` Not prose.
2. **State hard negatives as explicit "NO" rules with a rationale**, e.g. *"has NO arms and NO hands: none rendered, nothing at the shoulders."* The colon-plus-explanation pattern is used repeatedly.
3. **Separate the camera target from the subject.** *"An invisible camera target is placed separately from the head so the head is always in frame as the camera moves."* This is a rigging instruction disguised as prose.
4. **Name the camera rig by its physical archetype** — `CAMERA = robo-arm`, plus *"zero handheld shake, zero jitter"*. Compare Higgsfield's own camera vocabulary elsewhere: *dolly in, truck left, arc shot, push in, pull back wide, handheld follow, crane up, orbital move* ([How do I use Seedance?](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)).
5. **Quantify optics numerically** — *"47° diagonal field of view held for the entire shot"*, *"1.2 meters from his face closing to about 1.0 meter"*. Numbers, not adjectives.
6. **Break the timeline into explicit time segments** (`0.0s to 2.0s: …`) — both for camera and for performance.
7. **Use frame maps with x/y percentages** for spatial blocking — *"His hooded head at x 40-62%, y 18-70%"*. This is unusually precise and appears to be the mechanism that pins composition.
8. **Declare the collision rule both ways** — *"Nothing passes through the camera and the camera passes through nothing: no walls, no floor, no ceiling, no poles, no seats."*
9. **Isolate reference roles with `<<<image_N>>>` / `<<<video_N>>>` placeholders**, and explicitly state what is **not** inherited from each reference. This placeholder syntax matches the documented reference-element convention used across Higgsfield models (cf. `<<<element>>>` usage in the wider Higgsfield toolchain).
10. **Close with a POSITIVE CONSTRAINTS block** that restates the must-holds as affirmatives — a belt-and-braces duplication of the negatives.
11. **Negative style tail** — a trailing list of forbidden artefacts: *"no motion blur smear, no film grain, no vignette, no lens flare, no readable text or logos… no neon, no yellow cast."*

### 2.3 Other published prompt resources

- **Higgsfield Academy Prompt Bank** — a first-party, categorised prompt library at [higgsfield.ai/academy/apps/prompt-bank](https://higgsfield.ai/academy/apps/prompt-bank), with a **Camera** section of **46 examples** (Static shot, Pan right, Tilt up, Zoom in, …). Each entry ships a **"Recreate"** deep link that embeds the full URL-encoded prompt, e.g. the Static shot entry: *"The camera stays planted in one immovable position from the first frame to the last. Zero motion — no drift, no shake, no breathing, no stabilization float, no micro-drift; absolute rock-solid stillness throughout. Angle, elevation, distance to the scene and the overall composition are frozen and never altered; every ounce of motion comes from the scene itself, never from the camera. The clip closes on precisely the framing it began with, identical down to the pixel."* ([Academy](https://higgsfield.ai/academy)). These are video-model prompts rather than 3D Jutsu agent prompts, but they share the same NOT-rule grammar.
- **Seedance prompt structure** (useful because the Blender plugin's Video tab and the 3D Jutsu render path both route to Seedance): *"what the subject is doing, setting and lighting, camera move, mood or atmosphere"* — "four things in order"; plus *"change one thing per iteration… not both at once"* ([How do I use Seedance?](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)).
- The [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) is the **only first-party document that publishes a 3D-Jutsu-specific agent prompt**. There is no separate 3D Jutsu help-centre article (see §Access limitations).

### 2.4 The shared house grammar: the Seedance 2.5 Prompting Guide

The single most valuable additional prompt resource is **[Seedance 2.5: Complete Prompting Guide (Full Prompt Library)](https://higgsfield.ai/blog/seedance-2-5-prompting-guide)** (13 Aug 2026, 15 min). It is a genuine **prompt library** — *"10 strong prompt categories: drama, action, commercial, horror, and more. Each category was tested across multiple generations"*, each entry giving **the model, the settings used, the actual prompt, and the video it produced**.

Critically, it publishes a **formal section grammar** that the 3D Jutsu Prompt B almost exactly mirrors — which strongly suggests the 3D Jutsu prompt style is a **specialisation of Higgsfield's Seedance prompt house-style**, not an ad-hoc invention:

| Seedance 2.5 guide section | 3D Jutsu Prompt B equivalent |
|---|---|
| `GLOBAL STYLE` (genre, colour grade, film stock, aspect ratio, shutter, **"anything that shouldn't appear"**) | `FORMAT MODE` + the trailing negative style tail |
| `SCENE` (one-line logline) | `SCENE CONTEXT` |
| `CHARACTERS` (face, hair, build, wardrobe; *"note which reference is which character"*) | `ACTIVE REFERENCES` `<<<image_1>>>` |
| `LOCATION` (space and props, *"separate from the people in it"*) | `LOCATION MAP` |
| `FIRST FRAME AND BLOCKING` (*"pins down exact starting positions"*) | `FIRST FRAME AND SPATIAL BLOCKING` |
| shot-by-shot breakdown — *"each one labeled 'Shot 1', 'Shot 2'… ending in 'Hard cut' wherever a cut belongs"* | time-segmented `ACTION TIMING` / `CAMERA` blocks |
| `OPTICS` and `CAMERA` (*"focal length, camera height, handheld or dolly or crane"*) | `OPTICS` + `CAMERA` |
| `PHYSICS` (*"how fabric, smoke, hair, and liquid should move"*) | `PHYSICS` |
| `LIGHTING` (*"where it's motivated from, its direction, how it falls on faces"*) | `LIGHTING` |
| `AUDIO` (*"usually 'No music, no discernible dialogue' unless the scene needs otherwise"*) | `AUDIO` (*"No music track, no beat, no score"*) |

The guide's own framing of *why* the structure matters is the key operational rule:

> *"A prompt works best as **one continuous block of text, broken into labeled sections**. **Skip a section and the output tends to fail in a specific, predictable way.**"*

And the mnemonic for the overall shape:

> *"Most working Seedance 2.5 prompts follow the same shape: **one visual rule at the top, one sound rule at the bottom**, and everything in between broken into shots."*

Source: [Seedance 2.5 Prompting Guide](https://higgsfield.ai/blog/seedance-2-5-prompting-guide). This is the closest thing to an official **prompt template** for the final-generation half of the 3D Jutsu → Blender → video pipeline. Note it contains **one** mention of "3D Jutsu" but no Blender-specific blockout prompts.

### 2.5 Documented production tactics from a shipped film

Higgsfield's *Passport Rush* team notes (reported by [AI Primer, 2 Sep 2026](https://www.ai-primer.com/creative/stories/higgsfield-blender-camera-control)) give four concrete tactics:

- **Previs first:** storyboard → Blender previs → AI generation.
- **Wide shots:** start with a close or medium character shot, then transition into the wide view.
- **Blank faces:** taxi passengers who needed expressionless faces were deliberately kept out of view.
- **Style blending:** use the prompt *"take the style of the character and apply it to the background"*, then push the blend harder or softer to control the result.

### 2.6 The only fully published Astra → Blender agent prompt

Higgsfield published exactly **one** complete prompt for the Astra → Blender ("Scene Builder"-style) workflow, in an X post on **8 September 2026**. It was recovered directly from the post and is reproduced **verbatim** ([@higgsfield_ai, status 2097407934598930472](https://x.com/higgsfield_ai/status/2097407934598930472)):

```
Turn my winged-heart concept into a functional, openable AirPods Pro 3 case.

Use Higgsfield SOUL 2.0 through MCP to generate several design variations, then show me the strongest options for approval. Model and paint the selected design in Blender using verified AirPods dimensions. Make sure the lid opens correctly and all ports, controls, and indicators remain accessible.

Prepare correctly scaled STL and 3MF files in Anycubic for printing with white PLA. Deliver the concept images, Blender file, renders, and print-ready files. Do not guess measurements or printer settings.
```

**Why this prompt matters — it demonstrates a completely different grammar from the 3D Jutsu blockout prompts.** It is a short, outcome-oriented **brief** rather than a section-labelled shot specification. Its reusable moves:

1. **Name the starting asset** ("my winged-heart concept") — so the agent has a reference.
2. **Name the tool chain explicitly**: *"Use Higgsfield SOUL 2.0 through MCP"* → then *"Model and paint the selected design in Blender."* The prompt routes work across **two** systems.
3. **Insert an approval gate**: *"show me the strongest options for approval."* Compare the 3D Jutsu **"ask before generating"** behaviour mode ([§1.3](#13-agent-behaviour-modes)) — here the user writes the gate into the prompt itself.
4. **State a functional correctness requirement, not just a look**: *"Make sure the lid opens correctly and all ports, controls, and indicators remain accessible."*
5. **Name the deliverable list and the downstream format**: STL + 3MF, scaled, for a named slicer (Anycubic), with a named material (white PLA).
6. **Close with an anti-hallucination guard**: *"**Do not guess measurements or printer settings.**"* — the analogue of the 3D Jutsu prompt's collision NOT-rules and *"zero drift"* clause. Note it targets **dimensional accuracy**, which is the dominant failure mode for AI-generated geometry.

**Other Astra/Blender demos published no prompt at all** — only outcomes. Confirmed demo posts (linked via [AI Primer](https://www.ai-primer.com/creative/stories/astra-reference-3d-production), tweet text retrieved via direct fetch):

- Mies van der Rohe house — *"studied an existing scene → found the original plans → built the full 3D setup; Materials, lighting, vegetation, camera angles. **Fully editable**"* ([X](https://x.com/higgsfield_ai/status/2097474491857482142)).
- Space Shuttle Discovery — reportedly **192 assemblies** ([X](https://x.com/higgsfield_ai/status/2097481392313758124)).
- Nail-art → Blender model ([X](https://x.com/higgsfield_ai/status/2097515771782205831)).
- 2D artwork → editable Blender scene ([X](https://x.com/higgsfield_ai/status/2098241266886852698)).
- An interactive 3D product website where *"every element made in Blender via Higgsfield plugin"* ([X](https://x.com/higgsfield_ai/status/2097048653886312732)).

**Prompt text for these is `[NOT PUBLICLY AVAILABLE]`.** Only the AirPods case prompt above was published.

### 2.7 A second 3D-grammar prompt, and the prompt-pack inventory

**A second prompt in the identical section grammar** appears in [Generate AI Videos from ChatGPT with Higgsfield](https://higgsfield.ai/blog/generate-ai-videos-from-chatgpt), with sections: `SCENE CONTEXT` → `ACTIVE REFERENCES` → **`CABIN DIRECTION LOCK — READ BEFORE ANYTHING ELSE`** → `FIRST FRAME AND SPATIAL BLOCKING` → `LOCATION MAP` → `FORMAT MODE` → **`REALISM LOCK`** → **`EMOTIONAL PERFORMANCE LOCK`** (beats with timecodes) → `OPTICS` (`LENS LOCK = 84°`) → `CAMERA` → `ACTION TIMING` (0.0–3.0s … 28.45–30.0s) → `PHYSICS` → `LIGHTING` → `AUDIO` → **`POSITIVE LOCKS`**. Reference placeholders here are **named** (`@hero`) rather than numeric. This confirms the grammar is a **house style**, with the "LOCK" sections as optional, topic-specific additions.

**Inventory of Higgsfield's recreate-linked prompt packs** (counted by occurrences of `recreate=` in page source):

| Page | Recreate links | Notes |
|---|---|---|
| [Seedance 2.5: Complete Prompting Guide](https://higgsfield.ai/blog/seedance-2-5-prompting-guide) | **10** | 915–6,962 chars each; full section grammar |
| [Full AI Car Commercial Tutorial](https://higgsfield.ai/blog/ai-car-commercial-youtube-guide) | **23** | Uses a `— REFERENCE DEFINITIONS —` header with named refs (`@hero_03`, `@car_sheet`, `@loc_street_main`) |
| [How To Make Realistic VFX Shots With Seedance 2.5](https://higgsfield.ai/blog/ai-vs-vfx) | **16** | Largest single prompt: 19,430 chars |
| [Common AI Video Prompt Mistakes](https://higgsfield.ai/blog/ai-video-prompt-mistakes) | **14** | Each a naive "bad" prompt paired with its engineered rewrite — **the single most instructive page for learning the rules by contrast** |
| [How to Make a Game Trailer with AI](https://higgsfield.ai/blog/make-game-trailer-with-ai) | **12** | |
| [Talking AI Avatar in Claude](https://higgsfield.ai/blog/talking-ai-avatar-inside-claude) | **12** | |
| [Higgsfield Academy Prompt Bank](https://higgsfield.ai/academy) (camera section) | **10** | All camera-move templates with `[bracketed]` slots: locked-off stillness, pan, tilt up, zoom (`from [84] degrees to [29 or 18] degrees`), dolly-zoom, rack focus, jib rise (`[1.2]→[9] m`), circular drone (8 m radius, 4 m altitude, 200° arc), fly-away, dolly-in on rails |
| [UGC videos](https://higgsfield.ai/blog/how-to-make-ai-ugc-videos) | 4 | Introduces a `=== KEY === … === END KEY ===` block and a `RELIGHT (CRITICAL)` instruction |
| [Full ad campaign in Claude](https://higgsfield.ai/blog/full-ad-campaign-inside-claude) | 4 | |
| [Claude creative studio](https://higgsfield.ai/blog/claude-higgsfield-mcp-creative-studio) | 3 | |
| [Cinema Studio 4.0](https://higgsfield.ai/blog/cinema-studio-4-0) | 2 | |
| [Storyboard shot list](https://higgsfield.ai/blog/script-to-ai-storyboard-shot-list) | 1 | |
| [Prompt adherence comparison](https://higgsfield.ai/blog/ai-video-prompt-adherence-comparison) | 1 | 10,179 chars |
| **[3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)** | **2** | The only 3D-Jutsu-specific ones |
| Supercomputer, Genjutsu, Blender plugin, Academy course, help-centre pages | **0** | |

**Notable negative finding:** there is **no dedicated 3D Jutsu prompt pack or prompt bank.** Higgsfield's prompt bank is **camera-moves-only and generic**; the only 3D-Jutsu-specific prompts in existence are the two in the blog post.

### 2.8 A structural finding: there is no "NEGATIVE CONSTRAINTS" section

Verified by direct string search of the 3D Jutsu guide: **the string "NEGATIVE" does not occur anywhere on the page.** The brief's description of the guide as using "explicit NOT-rules" is correct in substance but the *structure* is different from what that phrasing implies:

- Negatives are carried **inline, inside the section they belong to** — e.g. *"no legs, no waist"* inside `FRAMING`; *"never stops, never reverses, never zooms"* and *"no walls, no floor, no ceiling, no poles, no seats"* inside `CAMERA`; *"no motion blur smear, no film grain, no vignette, no lens flare"* in the trailing style sentence.
- They are then **restated affirmatively** in a closing block titled **`POSITIVE CONSTRAINTS`** (Prompt B) / **`POSITIVE LOCKS`** (the ChatGPT-blog prompt) — deliberately *not* called "negatives".

**Practical rule:** in this house style you do not write a negative-prompt block. You place each denial next to the thing it constrains, then close with a positively-phrased restatement.

### 2.9 Adjacent community and vendor guidance worth adopting

- **Community 3D prompt collection** — [github.com/petergpt/3d-prompt-collection](https://github.com/petergpt/3d-prompt-collection): **63 full 3D scene prompts** across six sections (Big 3D Worlds 1–30, Playable/Game-Like 31–42, Living Art Worlds 43–49, Impossible Vantages 50–52, Natural Spectacles 53–59, Elemental & Cosmic 60–63). These target **Three.js code agents, not 3D Jutsu**, but the grammar transfers: a `#### FIRST FRAME - …` rule (*"open on the complete thing, no slow reveal, no menus/titles"*), `THE ZOOM IS THE SPECTACLE`, `EXPLORATION AND CONTROLS`, `PERFORMANCE`, `#### LIVING WORLD SIMULATION`, plus an explicit engineering contract (import-map, instancing, `devicePixelRatio ≤ 2`). Related community skill repos: [OSideMedia/higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill), [beshuaxian/higgsfield-seedance2-jineng](https://github.com/beshuaxian/higgsfield-seedance2-jineng), [NatiDvir/video-skills](https://github.com/NatiDvir/video-skills).
- **Community Blender blockout + AI render guide** — [Gachoki Studios, "Block Your Shot in Blender, Then Let AI Do The Rendering"](https://gachoki.com/block-in-blender-finish-with-ai/): build the blockout in Blender via the Higgsfield MCP bridge, export a viewport reference clip, feed it to the video model. Its core advice — *"give Claude an **actual shot list**, not a vague 'make it cinematic' request, but specific rails, targets, and cuts"* — matches Higgsfield's own documented model. It also advises separating the **structural layer** from the **style layer** for reuse.
- **[OpenAI's own GPT-6 Astra prompting guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)** — directly relevant because Astra is the flagship 3D Jutsu LLM: keep skill descriptions short; use **progressive disclosure** (a root doc acting as a minimal router); over-specific "itineraries/recipes" now *hinder* rather than help; **state completion criteria explicitly because Astra stops earlier than Sol**; do not over-constrain boundaries. ⚠️ This is in **tension** with the ultra-specific 3D Jutsu blockout prompts — the blockout prompt's specificity works for *scene specification*, while Astra's guidance concerns *task routing*. Worth testing both.

### 2.10 Determinism, restated

The **only** documented reproducibility mechanisms for 3D Jutsu are:

1. **The shared `?recreate=` URL**, which re-seeds the tool with the exact prompt text ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).
2. **Revision history** — *"preview a checkpoint or restore it as a new head"* ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

**No seed parameter is documented for 3D Jutsu.** Its documented scene inputs are **model, duration and aspect ratio only**, and seeds do not appear as a slot in any recreate link. `[NOT PUBLICLY AVAILABLE]`

---

## 3. Higgsfield for Blender: install, bridge, N-panel, compatibility, bugs, headless, non-Claude clients

### 3.1 Ship date and docs

- Changelog entry **"Higgsfield. Now in Blender"**, **21 August 2026**, categorised Feature / **MCP & Integrations** ([changelog](https://higgsfield.ai/creator-hub/changelog)). At launch the entry listed: *"Tools: Scene Builder, 3D Model, Character Animation, Image and Video, and Camera."*
- Official guide: [Higgsfield for Blender: Features, Installation, and MCP Bridge Setup](https://higgsfield.ai/blog/higgsfield-blender-plugin), **20 Aug 2026**.
- Product page: [higgsfield.ai/plugins/blender](https://higgsfield.ai/plugins/blender).
- Russian-language coverage confirming launch and same details: [Postium, 30 Aug 2026](https://postium.ru/higgsfield-predstavila-plagin-dlya-blender/).

### 3.2 Exact install steps (three steps, verified against two sources)

1. **Download the `.zip`** from [higgsfield.ai/plugins/blender](https://higgsfield.ai/plugins/blender). *"It's one signed file, no installer to run, and no helper app required."* **Keep the downloaded file zipped** — Blender installs the archive directly ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)).
2. **Drag the `.zip` onto any open Blender window** — *"It installs and enables itself."* Manual alternative: **Edit → Preferences → Add-ons → Install** ([ibid.](https://higgsfield.ai/blog/higgsfield-blender-plugin); corroborated by [Postium](https://postium.ru/higgsfield-predstavila-plagin-dlya-blender/)).
3. **Sign in** in the floating Higgsfield bar over the viewport and start generating ([ibid.](https://higgsfield.ai/blog/higgsfield-blender-plugin)).

### 3.3 Version compatibility and hardware requirements

- **Blender 4.2 through 5.1, on Windows or macOS** ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin); corroborated by [Postium](https://postium.ru/higgsfield-predstavila-plagin-dlya-blender/)).
- Internet connection + active Higgsfield account required.
- **"AI generation runs in the cloud, so a powerful GPU is not required for generation"** — your hardware only affects local Blender rendering ([ibid.](https://higgsfield.ai/blog/higgsfield-blender-plugin)).
- **Offline:** no new generation offline; *"Files already saved in your project or disk stay available offline."* ([ibid.](https://higgsfield.ai/blog/higgsfield-blender-plugin)).

### 3.4 What the panel exposes

The **product page** lists **seven** tabs — *"Scene Builder, 3D Model, Animation, Image, Video, Camera, Asset"* ([higgsfield.ai/plugins/blender](https://higgsfield.ai/plugins/blender)). The **guide** also counts seven: *"The bar covers seven tabs: Scene Builder, 3D Model, Character Animation, Image, Video, Camera, and Asset."* ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)). Note the changelog at launch listed only five groupings (Image and Video as one) — **Asset appears to have been added to the documented set after the 21 Aug launch**. `[UNVERIFIED]` exact date of the Asset tab's addition.

Documented per-tab behaviour ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)):

| Tab | Documented behaviour |
|---|---|
| **Scene Builder** | Describe a set; **objects, layout and light are placed directly in your Blender scene as real, editable geometry, not a rendered image**. Move/scale/delete like any object. Can feed directly into a Video generation. |
| **3D Model** | Prompt or reference → mesh at the **3D cursor** with **clean topology (quads, unwrapped UVs)**, materials included, **PBR maps linked** |
| **Character Animation** | **Rig included** (armature fitted and weighted, **no manual skinning**); plain-language move description → keyframes on the timeline; **standard Blender bones and actions**, curves editable like mocap |
| **Image** | **Native 4K without an upscale step**; any model per shot (Nano Banana Pro, Seedream, full catalogue in one dropdown); **viewport in, frame out** |
| **Video** | **Seedance 2.5 fed straight from your viewport**, with an **"Anti-Slop" mode** "built to reduce the melted hands and jelly physics common in generated video"; **generation to clip in about a minute** |
| **Camera** | Camera movement set by **physically moving your phone**; the scene camera follows **in real time**, producing natural handheld motion without keyframing |
| **Asset** | One library for 3D, images and clips; one click drops into the scene **as an object, a plane, or a texture**, with a **folder shortcut to the raw files on disk** |

The prompt bar sits **at the bottom of the 3D view**; you pick a tab and a model, set resolution and fps, and the **cost is on the Generate button** ([higgsfield.ai/plugins/blender](https://higgsfield.ai/plugins/blender)).

#### Two corrections to the brief's description of the panel

The brief describes "what the **N-panel** exposes (asset library, Scene Builder, 3D/Animation/Image/Video tabs, **camera QR-code capture from a mobile device**)". Verified against the official documentation, two of those details do **not** hold:

1. **It is not an N-panel.** Higgsfield's own wording is *"a **floating bar** over the 3D viewport"* / *"The bar covers seven tabs"* / *"The prompt bar sits at the **bottom of the 3D view**"* ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin); [plugin page](https://higgsfield.ai/plugins/blender)). The strings **"N-panel" and "sidebar" appear zero times** in the official guide — verified by direct string search of the recovered page text. Whether the bar is technically hosted in Blender's N-panel region `[UNVERIFIED]`; it is **not described that way**.
2. **No QR code is documented anywhere.** The Camera tab is described only as *"Camera movement is set by **physically moving your phone**, the scene camera follows in **real time**"* ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)). The string **"QR" appears zero times** in the official guide, and not on the plugin page, in the changelog entry, or in any third-party coverage reviewed. **A QR-code pairing step is `[NOT PUBLICLY AVAILABLE]`** — it may exist in-product, but it is **not published**, and the premise's "camera QR-code capture" should be treated as unconfirmed.
3. The tab set is also slightly different from the brief's phrasing: the seven tabs are **Scene Builder, 3D Model, Character Animation, Image, Video, Camera, Asset** ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)) — i.e. **Asset** and **Character Animation** are present, and "3D/Animation/Image/Video" is a compression of them.

Evidence gathered on the phone-camera workflow (all from Higgsfield's own X posts, quoted via [AI Primer](https://www.ai-primer.com/creative/stories/higgsfield-blender-camera-control), since X itself is login-walled): a [virtual-camera demonstration](https://x.com/higgsfield_ai/status/2095221421949825265) *"mapping its physical movement into a Blender scene"*, and a [camera-control clip](https://x.com/higgsfield_ai/status/2095295054634238091) *"carrying that virtual move through to its generated take"*. Neither is described as involving a QR code.

### 3.5 Bridge URL mechanics

Documented three-step setup ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin); repeated on the [plugin page](https://higgsfield.ai/plugins/blender)):

1. **Copy the bridge URL: `https://bridge.higgsfield.ai/mcp`**
2. **Add the Bridge through your assistant's MCP or connector settings**, name it **Higgsfield Bridge**, paste the URL. (Plugin page phrases this as *"Settings → Connectors → Add a custom connector"*.)
3. **Sign in when prompted**, then ask for a scene directly — the official example being **"Build me a calibration bay blockout in Blender."**

The guide draws an explicit distinction:

> "Higgsfield MCP can generate assets through an AI assistant on its own… The **Blender Bridge is a separate connection**: it adds access to the installed Blender add-on specifically, letting the assistant work with the scene that's currently open, not just generate an asset in isolation."

### 3.6 Headless operation — yes, but via a *different* package

The bridge URL above drives the **installed add-on**, which requires an open Blender window. However, Higgsfield also publishes an MIT-licensed npm package, **`fnf-blender-mcp`**, which explicitly **does not need the add-on**:

> "The independent `fnf-blender-mcp` package … controls a dedicated **background Blender process**. **No add-on, HTTP listener, WebSocket, cloud account or open Blender window is required.**"
>
> `Desktop MCP client → stdio → Node MCP → process pipes → Blender --background → bpy`

Source: [npm `fnf-blender-mcp` README](https://www.npmjs.com/package/fnf-blender-mcp) / [npm registry metadata](https://registry.npmjs.org/fnf-blender-mcp).

**Version history (from registry metadata, [registry.npmjs.org/fnf-blender-mcp](https://registry.npmjs.org/fnf-blender-mcp)):**

| Version | Published | Description | Model |
|---|---|---|---|
| `0.1.0` | **11 Sep 2026** | "Higgsfield use Blender: local stdio MCP and **authenticated loopback Blender add-on**." | add-on based |
| `0.2.0` | **12 Sep 2026** | "Higgsfield use Blender: local stdio MCP controlling a **background Blender process without add-ons**." | headless |

- Author/maintainer: `arsu@higgsfield.ai`; licence **MIT**; requires **Node ≥ 24**, **Blender 4.2+**.
- Repo: **[github.com/higgsfield-ai/fnf-local-pluging-bridge-mcp](https://github.com/higgsfield-ai/fnf-local-pluging-bridge-mcp)** (the Blender package lives in the `blender/` subdirectory; the repo root holds an independent After Effects package).
- **19 tools**, verified by the package's own `test:package`: `bl_health`, `bl_get_scene_summary`, `bl_get_object`, `bl_add_primitive`, `bl_delete_object`, `bl_set_transform`, `bl_set_material`, `bl_import_model`, `bl_add_camera`, `bl_set_active_camera`, `bl_add_light`, `bl_set_frame`, `bl_insert_keyframe`, `bl_save_project`, `bl_open_project`, `bl_render`, `bl_execute`, `bl_job_status`, `bl_get_skill` ([README](https://www.npmjs.com/package/fnf-blender-mcp)).

### 3.7 Whether the bridge can be driven by non-Claude MCP clients

**Yes — documented and first-class.** The 0.2.0 package prints configuration for non-Claude clients:

- `node dist/cli.js config --blender <path> --format json` — *"For another desktop MCP client… prints a JSON configuration using the current Node and server paths."*
- `node dist/cli.js config --blender <path> --format toml` — *"prints a Codex entry."*
- *"Both formats include absolute Node/server paths and `BLENDER_EXECUTABLE`; merge the entry into the intended client and refresh its connection."*

Source: [fnf-blender-mcp README](https://www.npmjs.com/package/fnf-blender-mcp). The repository README likewise documents a **Codex** registration path via `install-codex` for the sibling After Effects package, and states plainly that *"A remote web client cannot directly launch a local stdio process."* ([repo README](https://raw.githubusercontent.com/higgsfield-ai/fnf-local-pluging-bridge-mcp/main/README.md)).

For the **bridge URL** route, the official guide only names "your assistant's MCP or connector settings", so non-Claude support for the hosted bridge is *architecturally implied* but not enumerated. `[UNVERIFIED]` for a named non-Claude client on `bridge.higgsfield.ai/mcp`.

### 3.8 Known bugs, regressions, and hard gotchas

There is **no public bug tracker with filed issues** that I could locate `[NOT PUBLICLY AVAILABLE]`. What *is* documented are operational limits from the headless package's own README ([fnf-blender-mcp](https://www.npmjs.com/package/fnf-blender-mcp)):

- **Platform verification gap — the biggest one:** *"Verified on **macOS arm64 with Blender 4.2.23 LTS**… **Windows/Linux native Blender execution has not been verified locally.**"* The README also warns *"Offline tests… do not replace live Blender validation."*
- **No access to your open Blender window.** *"Each MCP connection owns one process… it **cannot access unsaved work in an already-open desktop Blender**."* You must `bl_open_project` a saved file, edit/render, then save a `.blend` to inspect in the UI.
- **Disconnecting loses unsaved session changes.** *"Disconnecting loses unsaved session changes."*
- **No crash recovery.** *"If Blender crashes, the session fails and is **not restarted automatically**."*
- **Closing the MCP kills the child process, including a running job.**
- **Timeouts don't cancel.** *"A timed-out job continues and keeps its `job_id`… additional execution commands are rejected while it runs. **No automatic retries or rollbacks occur.**"*
- **Bounded outputs:** Python stdout/stderr capped at **64 Ki characters each**; **JSON results limited to 4 MiB**; status retains **at most 128 jobs**; renders up to 4 MiB get an inline preview.
- **Serial execution:** *"Python runs sequentially on the process's main thread. Scene datablocks persist, while **script-local variables do not**."*
- **Guard rails are bypassable:** *"Arbitrary Python is **not sandboxed** and can bypass these typed-tool guards."* Conversely, *"Automatic execution of Python embedded in opened `.blend` files is disabled."*
- **Overwrite guards:** save/render require `overwrite: true` for existing files; opening a different project refuses unsaved changes unless explicitly discarded.
- **0.2.0 removed features relative to 0.1.0:** *"`launch`, `install-addon`, `bl_screenshot`, bridge discovery, PID selection and runtime-directory overrides are removed. **Use camera renders for visual evidence.**"* — a real regression for anyone relying on screenshots from 0.1.0.
- **Version-pinning gotcha in the README itself:** *"Verify that 0.2.0 is published before installing it; this source change alone does not publish a release."*

**Plugin-level gotchas documented by Higgsfield:**

- **Unlimited does NOT cover plugins or MCP.** *"Unlimited model generations and the free generations included in your plan… **Both apply only on the Higgsfield website**… any generation made outside it, including through **MCP, CLI, Canvas, Supercomputer**, and other automated tools, **always deducts credits, regardless of plan**."* ([How do credits work?](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)). The same rule is restated as *"exclusively on the web app, since **MCP, CLI, Supercomputer, Canvas, and plugins still draw from your regular balance** regardless of Unlimited status"* ([AI Video Credits Explained](https://higgsfield.ai/blog/ai-video-credits-explained)) and *"All generations through Canvas, MCP, CLI, and Supercomputer always deduct credits regardless of any Unlimited access on the web"* ([How do I use Seedance?](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)).
- **Free generations also do not apply outside the web app** ([How do credits work?](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)).
- **Commercial rights follow your plan** — the guide says to check terms before commercial use, an explicit non-answer ([Blender guide FAQ](https://higgsfield.ai/blog/higgsfield-blender-plugin)).
- **No refund for generations that come out wrong:** *"No, generation cost is charged at the point of generation regardless of whether you keep the result. **There's no automatic refund mechanism** for output that doesn't match what you wanted."* ([AI Video Credits Explained FAQ](https://higgsfield.ai/blog/ai-video-credits-explained)). Note the tension with the credits help page, which says failed generations *usually* auto-refund within minutes ([How do credits work?](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)) — the distinction is **failed** vs **unsatisfactory**.
- **The Unlimited toggle must be switched on manually** in the model menu, or the generation spends credits anyway ([Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)).

---

## 4. Genjutsu vs Seedance 2.5 vs Cinema Studio for final generation

### 4.1 Genjutsu

Shipped **1 September 2026** ([changelog](https://higgsfield.ai/creator-hub/changelog)); official guide [31 Aug 2026](https://higgsfield.ai/blog/higgsfield-genjutsu); product page [higgsfield.ai/genjutsu](https://higgsfield.ai/genjutsu).

**Two techniques:**

- **Motion Transfer** — *"Uses the motion from an existing video as a reference, then applies that movement to a new character or rebuilt scene."*
- **Object Swap** — *"Replaces the object or element you specify while preserving the rest of the original footage."*

Source: [Genjutsu guide](https://higgsfield.ai/blog/higgsfield-genjutsu). The product page frames it as *"Keep the motion and camera. Rebuild everything around them"* vs *"Point edits — outfit, location, characters, objects"* ([higgsfield.ai/genjutsu](https://higgsfield.ai/genjutsu)).

**Documented limits** ([Genjutsu guide](https://higgsfield.ai/blog/higgsfield-genjutsu)):

| Setting | Limit |
|---|---|
| Video input | **1 clip, 4 to 30 seconds** |
| Reference images | **Up to 30 per generation** |
| Prompt | **Optional** — short description or preset only |
| Presets | **30+** |
| Output resolution | **Up to 1080p** |

It works on **either real footage or generated video** ([ibid.](https://higgsfield.ai/blog/higgsfield-genjutsu)). Russian coverage independently reports the same 4–30 s / 30-reference / 1080p envelope ([Postium, 2 Sep 2026](https://postium.ru/higgsfield-zapustila-genjutsu/)).

**Aspect ratio:** `[NOT PUBLICLY AVAILABLE]` — the guide does not state Genjutsu output aspect ratios.

### 4.2 Seedance 2.5

Launched **6 August 2026** ([changelog](https://higgsfield.ai/creator-hub/changelog)); **1080p early access 14 Aug 2026** ([changelog](https://higgsfield.ai/creator-hub/changelog)).

| Spec | Seedance 2.5 | Seedance 2.0 |
|---|---|---|
| Clip length | **4s to 30s** | 4s to 15s |
| Resolution | model generates **480p / 720p / 1080p**, up to 4K upscaling | 480p to 4K |
| Aspect ratio | **9:16 to 21:9** | — |
| References | **up to 50** (30 images + 10 video clips + 10 audio files) | up to 9 images + 3 video + 3 audio |
| Audio | **native, generated in the same pass**; ambience, foley and score | native |
| Prompt adherence | **~20% better than 2.0** | baseline |
| Plan availability | **Pro and Plus and above; not Starter or Basic** | — |

Sources: [How do I use Seedance?](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance) and [Seedance 2.5 on Higgsfield in 2026](https://higgsfield.ai/blog/seedance-2-5-on-higgsfield-2026).

**"Seedance 2.5 Edit" is a separate model:** resolution **480p–720p**, length **matches the source clip**, supports **region-level edits** marked directly on the frame, plus audio editing ([How do I use Seedance?](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)).

**Audio behaviour — important for cost modelling:** *"Does native audio increase credit cost? **No.** The sound toggle doesn't change the cost of a generation: credit cost depends on the model, resolution, and clip duration."* ([How do I use Seedance? FAQ](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)). Note this contradicts the *general* pricing post's claim that "Audio and reference inputs" are billed on top **on some platforms** ([Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)) — on Higgsfield specifically, audio is free.

**Hard ceiling:** *"Can I make a Seedance clip longer than 30 seconds? **No.** 30 seconds is the maximum per generation in Seedance 2.5."* ([ibid.](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)).

**Reference system semantics** ([ibid.](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)):

| Reference | What it does |
|---|---|
| `@character` | Holds face geometry, skin tone and style consistent **within the clip** |
| `@style` | Applies lighting, palette and mood from an image or film still |
| `@motion` | Reads camera behaviour and motion pattern from a video clip and replicates it |
| `@audio` | Syncs visuals to audio, generates lip sync, matches ambient sound |

For consistency **across separate generations**, save the character as an **Element** (or train a **Soul ID** first if it's a real person) — `@character` alone is intra-clip only ([ibid.](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)).

### 4.3 Cinema Studio

Cinema Studio is Higgsfield's "professional filmmaking environment with camera and lighting control, multi-shot scenes, reusable characters and locations, and access to all image and video models" ([Which Higgsfield tool should I use?](https://higgsfield.ai/creator-hub/help-center/tools/which-higgsfield-tool-should-i-use)). **Cinema Studio 4.0** shipped **12 August 2026** ([changelog](https://higgsfield.ai/creator-hub/changelog)); a [Cinema Studio 4.0 blog post](https://higgsfield.ai/blog/cinema-studio-4-0) exists. Higgsfield cites **1,296 camera lenses** and cinematic colour grading in Cinema Studio ([Cryptopolitan via Mitrade, 17 Aug 2026](https://www.mitrade.com/insights/news/live-news/article-3-2004956-20260817)).

### 4.4 Which one, when — the documented pipeline

The pipeline Higgsfield itself documents ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)):

| Stage | Tool | Why |
|---|---|---|
| Block the previz | **3D Jutsu** (agent on Supercomputer) | Grey-proxy geometry, camera path, framing, timing — cheap to iterate |
| Render the previz | **3D Jutsu → Export** | *"the camera timeline renders as a video: the grey blockout becomes a reference clip"* |
| Generate identity + location | **Soul 2.0** (character portrait) + **Soul Cinema** (empty location) | *"Both are regular Higgsfield generations, ready to drop into the chat"* |
| Final generation | **Same 3D Jutsu chat** → video model | Previz becomes `<<<video_1>>>`; character becomes `<<<image_1>>>` |
| Inside Blender instead | **Blender plugin → Video tab** | *"Seedance 2.5 fed straight from your viewport"*, with Anti-Slop mode |
| Recast an existing finished take | **Genjutsu** | Motion Transfer / Object Swap without a reshoot |

Additional evidence that Seedance 2.5 is the default final-render model in this pipeline: the Blender plugin's Video tab is described as *"Seedance 2.5 fed straight from your viewport"* ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)); a Russian-language write-up of the 3D Jutsu + Astra flow states the video render goes *"через Seedance 2.5"* ([vc.ru, 5 Sep 2026](https://vc.ru/ai/3122081-sozdanie-3d-stsen-s-pomoshchyu-tekstovogo-zaprosa)); and Seedance 2.5 is positioned as the model that makes the 3D scene builder meaningful — *"Motion control and the **3D scene builder** go further, letting you set a camera path or block out a scene spatially instead of describing it"* ([Seedance 2.5 on Higgsfield](https://higgsfield.ai/blog/seedance-2-5-on-higgsfield-2026)).

**Cinema Studio vs Seedance — Higgsfield's own split, from the pricing post:** *"Cinema Studio handles camera and lens control"* and Seedance runs inside Higgsfield's own tooling rather than as a standalone generator ([Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)).

**Genjutsu vs the other two:** Genjutsu is *post-hoc*. It consumes a finished clip and rebuilds part of it — it is not a scene-construction tool. The product page's example prompts are instructive: *"Move the whole fight into this pastel valley by the turquoise stream"*, *"Replace the defender with this girl, keeping her watch on her wrist"*, *"Recast both fighters and restage the fight in the pastel valley — **every move and camera stays**"* ([higgsfield.ai/genjutsu](https://higgsfield.ai/genjutsu)).

---

## 5. Costs in Higgsfield credits

### 5.1 The credit rate

Roughly **$0.05 per credit** (derived from multiple official tables: 40 cr = $2.00, 104 cr = $5.20, 144 cr = $7.20 on [Genjutsu](https://higgsfield.ai/blog/higgsfield-genjutsu); 52 cr = $2.55 on [Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)).

**Plan tiers** (credits per cycle): **Basic 120**, **Plus 1,000**, **Ultra 3,000** ([AI Video Credits Explained](https://higgsfield.ai/blog/ai-video-credits-explained)). The $49 plan carries **1,000 credits** ([Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)). Seedance 2.5 requires **Pro/Plus and above** ([How do I use Seedance?](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance)).

### 5.2 3D Jutsu — cost per agent message (official table)

This is the single most important cost finding, and it is **published officially** ([3D Jutsu guide, "What does it cost?"](https://higgsfield.ai/blog/higgsfield-3d-jutsu)):

| Model | Approximate cost per message |
|---|---|
| **Auto** (default) | **Free** |
| DeepSeek V4 Flash | ~0.4 credits |
| Seed 2.1 Turbo | ~1 credit |
| Gemini 3.5 Flash | ~2 credits |
| Gemini 3.1 Pro | ~3 credits |
| GPT 5.6 Sol | ~7 credits |
| Claude Opus 5 | ~8 credits |
| **Claude Fable 5.1** | **~11 credits** |
| **GPT 6 Astra** | **~17 credits** |

Verbatim context: *"3D Jutsu prices agent messages by model. On Auto, the free default, messages cost nothing; picking a specific LLM charges credits per message. The selector carries **30+ LLMs** across price ranges, the estimated cost shows before you send, **longer chats use more**, and the credits are the same balance you use everywhere on Higgsfield."* ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

**Practical consequence:** driving the 3D Jutsu agent with **GPT 6 Astra at ~17 credits/message** costs roughly **$0.85 per agent turn**. A 30-turn scene-building conversation on Astra is therefore on the order of **~510 credits (~$25.50)**. On **Auto it is free**.

### 5.3 3D Jutsu — cost per previz render, static frame, and GLB export

**`[NOT PUBLICLY AVAILABLE]`.** No published credit price exists for the 3D Jutsu MP4 previz render, static-frame export, or GLB export. The official FAQ on pricing addresses **only agent messages** ([3D Jutsu guide FAQ](https://higgsfield.ai/blog/higgsfield-3d-jutsu)), and the export row of the tool table describes *dimensions and file size*, not credits ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).

**Important caveat:** because 3D Jutsu's agent runs on **Supercomputer**, and because *"Each generation step deducts credits at standard rates"* on Supercomputer with *"the running cost… shown as the task proceeds"* ([How do I use Supercomputer?](https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-supercomputer)), any **video generation requested from inside the 3D Jutsu chat** should be assumed to bill at the underlying model's rate. Treat "free exports" as unconfirmed.

### 5.4 Seedance 2.5 — official Higgsfield figures

| Setting | Credits | Approx. $ |
|---|---|---|
| 8s **720p** | **52** | $2.55 |
| 8s **480p** | **24** | ~$1.18 |
| 8s 720p, **Seedance 2.0** (for comparison) | 36 | $1.76 |

Source: [Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026).

**Derived per-second rates at 720p:** 52 ÷ 8 = **6.5 credits/second**. Under linear scaling, a **20-second 720p** Seedance 2.5 render ≈ **130 credits (~$6.50)**. At 1080p, where the same post implies a roughly 2× multiplier (Seedance 2.0: 45 cr at 5s/1080p vs 23 cr at 5s/720p), 20 s at 1080p would be on the order of **220–260 credits**. `[CALCULATED — not an official figure]`

### 5.5 Genjutsu — official pricing

Motion Transfer and Object Swap cost the **same**; priced by length and resolution ([Genjutsu guide, Pricing](https://higgsfield.ai/blog/higgsfield-genjutsu)):

| Length | Credits | Approx. Price |
|---|---|---|
| 15 sec, **480p** | **40** | $2.00 |
| 15 sec, **720p** | **104** | $5.20 |
| 15 sec, **1080p** | **144** | $7.20 |

*"Pricing verified September 2026. Credit costs may vary by generation settings."* Independently corroborated by [Postium](https://postium.ru/higgsfield-zapustila-genjutsu/), which cites the same 40 / 104 / 144 figures and attributes them to the company.

### 5.6 Cinema Studio and other models — official comparison table

From [AI Video Credits Explained](https://higgsfield.ai/blog/ai-video-credits-explained) (headings in the source say "5 seconds, 720p" / "10 seconds, 720p", but note the table labels inside the page are inconsistently rendered — the figures below are as printed):

| Model | 5s 720p | 5s 1080p | 10s 720p | 10s 1080p |
|---|---|---|---|---|
| Seedance 2.0 | 23 cr ($1.15) | 45 cr ($2.25) | 45 cr ($2.25) | 90 cr ($4.50) |
| Kling 3.0 | 10 cr ($0.50) | 12.5 cr ($0.63) | 20 cr ($1.00) | 25 cr ($1.25) |
| **Cinema Studio** | **25 cr ($1.25)** | **50 cr ($2.50)** | **50 cr ($2.50)** | **100 cr ($5.00)** |
| Wan 2.7 | 8 cr ($0.40) | 13 cr ($0.65) | 15 cr ($0.75) | 25 cr ($1.25) |

The page's stated rule: *"**Resolution** tends to be the single biggest multiplier of the three"* — bigger than duration ([ibid.](https://higgsfield.ai/blog/ai-video-credits-explained)).

### 5.7 Soul 2.0 / Soul Cinema — per-image cost

**`[NOT PUBLICLY AVAILABLE]`.** No published per-image credit price for Soul 2.0 or Soul Cinema was found. What *is* documented:

- Soul Cinema generates **up to 4 images per generation** ([How do I use Soul Cinema?](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-soul-cinema)).
- Some plans include **free generations** on Soul 2.0 and Soul Cinema — *"a one-time pool granted when you purchase the plan… Free generations do not renew."* The exact pools are listed on the Pricing page's *Unlimited & Free Gens* section ([How do credits work?](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)).
- The exact cost is always on the Generate button before you confirm ([ibid.](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)).

### 5.8 Blender plugin — per-tab costs

**`[NOT PUBLICLY AVAILABLE]`** as a numeric table. Higgsfield documents only the mechanism: *"The number on the Generate button is the credit price, visible before you press it, and the **variants counter multiplies it** if you're generating more than one at a time… Everything runs on the **same Higgsfield credits** as the web platform"* ([Blender guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)). Since the tabs wrap known models (Seedance 2.5 for Video, Nano Banana Pro / Seedream / Z Image for Image, **Meshy 5 for 3D**), the underlying model rates in §5.4–5.6 are the best available proxy ([ibid.](https://higgsfield.ai/blog/higgsfield-blender-plugin)). Note **Meshy 5** is named as the 3D model in the plugin — it is *not* a Higgsfield-native model, so its rate is external.

### 5.9 Unlimited — what it actually covers

Two separate layers ([AI Video Credits Explained](https://higgsfield.ai/blog/ai-video-credits-explained)):

1. **A 365-day Unlimited set** built into plans above the entry tier — *"a one-time inclusion that lasts 365 days from activation, doesn't roll over, and doesn't renew with your next billing cycle."*
2. **All Unlimited** — a separate short window, **1 to 7 days**, covering **23 models** across image, video and audio. Shipped **20 July 2026** ([changelog](https://higgsfield.ai/creator-hub/changelog)).

**Critical constraints:**

- *"During either layer, eligible generations cost zero credits, **exclusively on the web app**, since MCP, CLI, Supercomputer, Canvas, and plugins still draw from your regular balance regardless of Unlimited status."* ([AI Video Credits Explained](https://higgsfield.ai/blog/ai-video-credits-explained))
- *"The tradeoff is **concurrency**, not quantity: **1 generation per format at a time, shared across every model**. Regenerating the same shot five times to nail a camera movement still costs nothing, it just happens sequentially rather than in parallel."* ([ibid.](https://higgsfield.ai/blog/ai-video-credits-explained))
- Seedance 2.5 unlimited windows run **~33 days** at up to 720p, with max clip length rising by tier and annual billing; separate Seedance 2.0 windows run 7/14/33 days at up to 1080p with a 15 s cap; **the cheapest plans are not included** ([Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)).
- The **Unlimited toggle must be switched on** in the model menu, or the generation spends credits regardless ([ibid.](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)).
- **Unlimited is not available via the Blender plugin.** This is the single biggest cost trap in this pipeline.
- **Fourth independent confirmation of the same rule**, from a comparative pricing analysis: *"Unlimited applies on higgsfield.ai; **MCP, CLI, Canvas, Supercomputer, and Marketing Studio run on credits**."* The same source adds: *"Unlimited runs on higgsfield.ai in standard queue at **one video or two images at a time**, while credits power the rest of the suite, from Supercomputer batches to MCP generation"*, and *"**Canceling mid-term pauses the set**; it resumes on reactivation before expiry, and **there is no priority queue inside unlimited mode**."* ([Annual unlimited AI video plans compared](https://higgsfield.ai/blog/annual-unlimited-ai-video-plans)).

⚠️ **The consequence for this pipeline specifically:** a 3D Jutsu scene built and rendered through the **Blender plugin** or the **MCP bridge** consumes credits at full rate no matter what Unlimited tier the account holds. Only the browser workspace can benefit from Unlimited — and only for eligible models.

### 5.10 Refunds, expiry, and billing terms

- Subscription credits **reset each cycle and do not roll over**; on annual plans they reset **every 30 days**, not on the calendar date ([How do credits work?](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)).
- Credit Pack / Auto-Refill / Boost credits expire **90 days** from purchase; promo credits expire on the date shown ([ibid.](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)).
- Spend order: **subscription credits first**, then remaining credits **by soonest expiry** ([ibid.](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)).
- Failed generations usually **auto-refund within a few minutes**, but *"Specific models might not refund credits for failed generations."* ([ibid.](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)).
- **Refund policy per press reporting:** refunds only within **7 days of purchase**, only if **no credits have been used**, **minus a 6% service fee**; **renewals excluded entirely** ([WION, 18 Aug 2026](https://www.wionews.com/world/the-new-ftx-higgsfield-ai-has-1-customer-care-guy-for-300-000-paying-customers-sitting-on-discord-1786997058623)).

### 5.11 On the community claim of "50–100 credits per 3D environment" and "~200 credits for a 20s Seedance 2.5 render"

Both claims are **corrected below**; neither survives as stated.

#### "~200 credits" — REAL NUMBER, WRONG SUBJECT (traced to source)

The number is genuine, but it comes from **Higgsfield's own Supercomputer documentation**, not a community report, and it describes a **whole multi-step production**, not a single 20-second render. Verbatim, from the [Higgsfield Supercomputer Guide, "The Credit Math"](https://higgsfield.ai/blog/higgsfield-supercomputer-guide) (3 Jul 2026):

> *"The agent generates a 4K character image in step one, then uses that image as a reference to animate a scene at 1080p using Seedance 2.0 in step two… That two-step workflow runs approximately **90 credits**, around $4.50. A full end-to-end production runs closer to **200 credits**, approximately $10."*

The guide's own table:

| Metric | Detail |
|---|---|
| Animation step (Seedance 2.0, 10-sec, 1080p, High) | **90 credits (~$4.50)** |
| **Full end-to-end production workflow** | **~200 credits (~$10)** |
| Max clip duration | Up to 15 seconds |
| Output quality | 480p, 720p, 1080p, 4K |
| Aspect ratio options | 16:9, 9:16, 4:3, 1:1, 3:4, 21:9 |

Source: [Supercomputer Guide](https://higgsfield.ai/blog/higgsfield-supercomputer-guide).

So **"~200 credits" = a full agentic production (character image + animation + orchestration) on the Seedance-2.0-era stack with ≤15 s clips.** It is **not** a 20-second Seedance 2.5 render. Nothing in any source prices a 20 s Seedance 2.5 clip at 200 credits. `[REFUTED as stated / REFINED to its actual meaning]`

#### The correct figure for a 20 s Seedance 2.5 render

Official 720p rate is **52 credits / 8 s = 6.5 credits/second**, giving **~130 credits for 20 s at 720p** ([Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026)). This **6.5 credits/sec at 720p** rate is corroborated independently by a third-party pricing breakdown ([techsifted.com, 5 Sep 2026](https://www.techsifted.com/roundups/higgsfield-ai-pricing-2026/)), which lists *"Seedance 2.5 at 720p ≈ 6.5 credits/second."* At 1080p the figure would be materially higher. Also remember to multiply by attempts: *"Multiply the credit cost of one generation by the average number of attempts it takes you to get a usable result. That number, not the sticker price, is your real cost per clip."* ([AI Video Credits Explained](https://higgsfield.ai/blog/ai-video-credits-explained)).

#### "50–100 credits per 3D environment" — ORIGIN NOT FOUND

**No source for this claim could be located** — not in Higgsfield's blog, not in the 3D Jutsu announcement coverage, not on Reddit, not in any third-party write-up. **Do not repeat it as sourced.** Two hypotheses are consistent with verified data but neither is confirmed:

- It may describe **agent messages**: 50–100 credits is ~3–6 turns on **GPT 6 Astra** (~17 cr each) or ~50–100 turns on **Seed 2.1 Turbo** (~1 cr) ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)).
- It may have originated in the **"What does it cost?"** section of the [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) — but that section (recovered in full during this research) prices **only agent messages** and contains **no per-environment figure**, which argues against this.

`[UNVERIFIED — origin not found]`

### 5.12 Supercomputer is the billing context for 3D Jutsu — and it is not free

Because the 3D Jutsu agent *"runs on Supercomputer"* ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)), the Supercomputer commercial terms apply to the agentic layer. From the [Supercomputer Guide](https://higgsfield.ai/blog/higgsfield-supercomputer-guide):

- *"**It is not free.** Supercomputer is available on **paid plans only**. Most meaningful actions require **Plus or above**."*
- *"**It is not a real-time editor.** The agent generates and delivers finished assets."*
- *"**It is not cheap for high-fidelity output.** A full production at 200 credits is approximately $10."*
- Credit rate parity: *"Why is a generation more expensive in Supercomputer? **It's not. The credit rate is the same as standard generation.**"*
- Crucially: *"The credit cost appears before generation and requires an **Approve button click** before anything is spent."* — and the chat *"shows you the cost before anything runs, and executes on approval"* ([ibid.](https://higgsfield.ai/blog/higgsfield-supercomputer-guide)).

### 5.13 Realistic end-to-end budget for the Astra → 3D Jutsu → Seedance pipeline

`[CALCULATED — composition of official figures, not an official total]`

| Stage | Credits | Basis |
|---|---|---|
| 30 agent turns on **Auto** | **0** | [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |
| 30 agent turns on **GPT 6 Astra** | ~510 | 17 cr × 30 ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)) |
| 30 agent turns on **Claude Fable 5.1** | ~330 | 11 cr × 30 ([ibid.](https://higgsfield.ai/blog/higgsfield-3d-jutsu)) |
| Previz render + GLB export | **unpublished** | `[NOT PUBLICLY AVAILABLE]` |
| Final 8 s @ 720p Seedance 2.5 | 52 | [Seedance 2.5 pricing](https://higgsfield.ai/blog/seedance-2-5-pricing-2026) |
| Final 8 s @ 720p, 3 attempts | 156 | ×3 iteration ([AI Video Credits Explained](https://higgsfield.ai/blog/ai-video-credits-explained)) |
| Optional Genjutsu recast, 15 s @ 720p | 104 | [Genjutsu](https://higgsfield.ai/blog/higgsfield-genjutsu) |

**The dominant cost is agent messages, not renders** — which is why the free **Auto** default matters so much.

---

## 6. Discord / community: what is and is not publicly findable

### 6.1 Honest framing

I have **no Discord access**. I did not read any Discord channel, thread, or message. Everything below is either (a) Higgsfield's **own published description** of its Discord server, or (b) third-party press reporting **about** that server. **No Discord content is indexed by search engines**, so no community prompt packs, gotchas, or bug reports from Discord could be retrieved. **Any statement about what users discuss inside the Higgsfield Discord would be fabrication, and none is made here.**

### 6.2 What Higgsfield publishes about its own Discord

The help-centre article [How do I join the Higgsfield community on Discord?](https://higgsfield.ai/creator-hub/help-center/getting-started/higgsfield-community-on-discord) (30 Jul 2026) is public and documents the server structure in detail:

- **Invite:** [discord.com/invite/higgsfield](https://discord.com/invite/higgsfield), also linked in account settings and official social channels.
- **Scale claim:** *"home to **thousands of creators**"* — note: **"thousands"**, not hundreds of thousands.
- **Channel groups:** *Start here* (`#rules`, `#introductions`, `#help-center`); *Updates* (`#announcements`, `#updates`, `#community-events`, `#community-streams`, `#our-social-media`); *Community hub* (`#general-chat`, `#prompt-discussion`, `#tutorials`, `#learning-hub`); *Create and share* (`#your-creations`, `#collaborations`, `#daily-soul`, `#hall-of-fame`, `#stream-spotlight`); *Recognition* (`#monthly-awards`); *Support and feedback* (`#support`, `#community-support`, `#bug-reports`, `#suggestions`).
- **Verified hub:** gated channels unlocked by clicking **"Verify with Higgsfield"** in `#verification`; grants a plan-reflecting role. *"Verification is optional, all public channels stay open without it."*
- **Roles:** Higgsfield Team, Moderators, Ambassadors, **Power Users**, **Bug Hunters** (Power Users focused on finding and verifying bugs), **Allies** (multilingual helpers), **CPP** (Creator Partner Program), Verified / Verified [Plan]. *"There's no application"* for Power Users.
- **Events:** Weekly Challenge (credit prizes), **Daily Soul Challenge** (`#daily-soul`, three winners/day, credit rewards, must use a Soul model — Soul, Soul 2.0 or Soul Cinema — and must post the generation link), community streams, Community Feedback sessions, Community Podcast, monthly awards.
- **Notably absent:** there is **no documented 3D Jutsu, Blender, or Genjutsu-specific channel**. `[NOT PUBLICLY AVAILABLE]` — no 3D-dedicated community space is documented.

### 6.3 Publicly reported community and company size

**The "~200,000 users" premise is resolved: it is the Discord member count.** Discord's own invite API returns the guild's member count directly, which is hard, exact data rather than a self-reported marketing figure:

```
GET https://discord.com/api/v10/invites/higgsfield?with_counts=true   →   HTTP 200
{
  guild.id:              "1173418785630330921"
  guild.name:            "Higgsfield AI"
  guild.vanity_url_code: "higgsfield"
  guild.premium_subscription_count: 225
  approximate_member_count:  193059
  approximate_presence_count: 11757
  guild.description: "The official Higgsfield AI community. … Join 190K+ creators
                      sharing work, trading prompts, and exploring the future of
                      generative AI"
}
```

Retrieved **13 September 2026**. Source: [Discord invite API](https://discord.com/api/v10/invites/higgsfield?with_counts=true) (verified directly, not via a mirror).

**So: ~193,000 Discord members, of whom ~11,757 (~6%) were online at query time.** Note the guild description itself says *"190K+ creators"* — Higgsfield's own rounding.

This sits in a very different range from the **platform** user counts, which are self-reported and mutually inconsistent:

| Figure | Source | Date | Reliability |
|---|---|---|---|
| **193,059 Discord members** / 11,757 online / 225 boosts | [Discord invite API](https://discord.com/api/v10/invites/higgsfield?with_counts=true) | 13 Sep 2026 | **Hard data, API-exact** |
| "Join **190K+** creators" | guild description, same API response | 13 Sep 2026 | Self-description |
| **~15 million users; ~300,000 paying**; ~4.5 M clips/day | [WION](https://www.wionews.com/world/the-new-ftx-higgsfield-ai-has-1-customer-care-guy-for-300-000-paying-customers-sitting-on-discord-1786997058623) | 18 Aug 2026 | Reported |
| **30,000,000+ users; $700 M annualized revenue; 390 Fortune 500 customers** | Higgsfield via [PR Newswire](https://www.prnewswire.com/news-releases/higgsfield-raises-400-million-series-b-financing-at-5-4-billion-valuation-with-annualized-revenue-reaching-700-million-302852430.html) / [RuntimeWire](https://runtimewire.com/article/higgsfield-gpt-6-astra-blender-2d-artwork-3d-model) | 17 Aug 2026 | **Self-reported** |
| **25 million users; 850 M generations** | [higgsfield.ai/about](https://higgsfield.ai/about) | Sep 2026 | **Self-reported — and inconsistent with the 30 M figure above.** RuntimeWire explicitly flags this: *"Higgsfield's current about page separately displays 25 million users and 850 million total generations, an inconsistency that may reflect different update schedules or measurement windows."* |
| **"Community over 25 MILLION USERS"** | Higgsfield's [Blender plugin page](https://higgsfield.ai/plugins/blender) | live Sep 2026 | Self-reported |
| **22 million users; $300 M revenue** | [digitalbusiness.kz](https://digitalbusiness.kz/2026-04-02/kazahstanskiy-startap-edinorog-podvel-itogi-goda-22-mln-polzovateley-i-300-mln-viruchki/) | 2 Apr 2026 | Reported |
| **$400 M Series B at $5.4 B valuation** (DST Global) | [TechCrunch](https://techcrunch.com/2026/08/17/higgsfield-raises-400m-series-b-quadrupling-its-valuation-in-8-months-to-5-4b/) | 17 Aug 2026 | Multiple independent outlets |
| **$1.3 B valuation** | [TechCrunch](https://techcrunch.com/2026/01/15/ai-video-startup-higgsfield-founded-by-ex-snap-exec-lands-1-3b-valuation/) | 15 Jan 2026 | Multiple outlets |
| **"thousands of creators"** on Discord | Higgsfield [help centre](https://higgsfield.ai/creator-hub/help-center/getting-started/higgsfield-community-on-discord) | 30 Jul 2026 | Higgsfield — **now visibly stale vs its own 190K+ guild description** |

**Reconciliation.** The ~200,000 figure maps to **Discord members (~193 k)**, and separately to the ~300,000 *paying customer* count — those two are distinct. The platform user counts (15 M / 22 M / 25 M / 30 M) are self-reported marketing figures, are internally inconsistent within Higgsfield's own materials, and should not be treated as community size. `[UNVERIFIED — self-reported and mutually contradictory]`

### 6.3b The one substantive public 3D-artist evaluation (a proxy, not the Higgsfield plugin)

The closest thing to independent scrutiny of the *underlying* Astra + Blender capability is a large Reddit thread — note it concerns **Astra driving Blender over MCP generally**, not Higgsfield's plugin specifically:

**r/OpenAI — "Fable 5.1 vs GPT 6 Astra, 3D Blender, mind blowing difference!"** — u/curious_capsuleer, ~5 Sep 2026, 2,337 upvotes, 337 comments, 93% upvoted ([redlib mirror](https://redlib.catsarch.com/r/OpenAI/comments/1w7ppcj/fable_51_vs_gpt_6_astra_3d_blender_mind_blowing/); canonical `reddit.com/r/OpenAI/comments/1w7ppcj/`). Retrieved via a Reddit mirror; the canonical Reddit permalink was not directly fetchable.

- OP: *"I connected it with blender via mcp and gave my prompt on what I wanted for my game asset and it created it from scratch."*
- **Cost/time datapoint:** asked whether this could make a whole movie, OP replied *"Yes the cost will be insane this one took like **30-45 mins and used all my usage reset on plus plan**."*
- **The dominant criticism was that no wireframe was ever shown.** u/LazyLancer: *"The difference is mind-blowing but it's still shit as soon as you start looking at details – to the point it's better to make a model from scratch."* u/No_Basil4168: *"Beyond being a shiny tech demo the modelling on that is atrocious and it'd be unusable without significant cleanup which could take longer than just modelling it from scratch."* u/Impressive-Face-3549: *"All the comments asking op to show wireframe and he isn't responding to those whatsoever lmao."*
- **Counterpoint from a practitioner** — u/Lorunification: *"these models do an excellent job at maintaining topology. Specifically because they do not 'move around' stuff, but interact with the model programmatically and, as far as I can tell, verify after each step."*
- **An unanswered setup question** relevant to [§3.7](#37-whether-the-bridge-can-be-driven-by-non-claude-mcp-clients): u/Alarming_Mammoth8567 asked whether Blender MCP needs a remote server with API calls and whether Astra is watered down on Plus — **no authoritative answer appeared in the thread.** `[UNVERIFIED]`

**Net reading:** the public verdict on AI-driven Blender geometry is *"impressive, topology unverified, likely needs significant manual cleanup."* No Higgsfield-specific equivalent evaluation exists.

### 6.3c Why there is no Blender-plugin community thread

r/blender's rule #2 **already prohibits predominantly-AI work**, and a July 2026 mod thread clarifies enforcement:

**"Generative AI & r/Blender"** — mod u/Avereniect, 5 Jul 2026, 744 upvotes, 418 comments ([redlib](https://redlib.catsarch.com/r/blender/comments/1uo6ke0/generative_ai_rblender/)). The thread was widely misread as a ban vote; the mod wrote *"The amount of people who think this is a 'Do we ban AI?' post is quite frankly frustrating."*

Most relevant exchange, u/mattadvance, on AI-authored Blender add-ons:

> *"Generative AI disrupts 2 and 3, but in my opinion, 4 the most by adding extra mental cost to detecting, verifying, and filtering out AI… I want to know if an add-on is useful, safe, and will be supported by an author that knows what they're doing and **isn't taking shortcuts**."*

And u/damnboychill, naming the marketing pattern that maps onto Higgsfield's *"no 3D experience required"* FAQ answer:

> *"It is also very insane how this AI products pop up as ads in our subreddit claiming 'You don't need any 3D experience or skills!'"*

Users are redirected elsewhere — u/flasticpeet: *"If you're using AI and Blender, feel free to post to r/StableDiffusion… If you're using ComfyUI, your work is welcome in r/comfyui."*

**Consequence for this research:** the single largest 3D-artist community on Reddit is structurally closed to this tool, which is a major reason the Blender plugin has essentially no community bug-report corpus.

### 6.3d The best-evidenced real-world cost/failure report

**「Higgsfieldの新機能「Supercomputer」を使ってみたら、500クレジット溶けて失敗した話」** — デザインおやじ, **16 May 2026**, [note.com/design_oyaji/n/n4f8c0f169eb2](https://note.com/design_oyaji/n/n4f8c0f169eb2). Retrieved via a text-extraction proxy (note.com is JS-gated to direct fetch).

Deliberately non-hostile — *"this is not a story about 'Higgsfield is bad'… rather, it feels quite futuristic"* — which makes it more useful than a complaint post. Concrete figures:

| Action | Credits |
|---|---|
| Image generation (Images 2.0) | **35** per generation |
| Video generation | **135** per generation |
| A text-removal edit | **135** |
| Chat turns | a few credits each |

The failure: he hit the **sensitive-content filter twice**, and *"both times credits were consumed. 135 credits × 2 = 270 credits!"* The final video also had **garbled text** (文字化け). **Total: ~500 credits burned** — roughly half a month's allowance on his plan, ≈¥2,000. His conclusion: *"Wouldn't it have been faster to generate each scene with Seedance 2.0 and stitch them myself?"* — and he abandoned the job.

**Caveat:** this is **Supercomputer, not 3D Jutsu**. It is cited here because Supercomputer *is* the agent 3D Jutsu runs on ([3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)), so it is the closest available analogue for how a multi-step agentic run can burn credits on rejected output.

### 6.3e Other community-sourced gotchas worth carrying forward

| Report | Source | Date |
|---|---|---|
| **$16 of CLI/agent tokens wasted**; the agent auto-generated 4 of 6 requested scenes *without* review; allegation that Higgsfield's starter "skills" steer the agent toward the most expensive models | [r/Higgsfield_AI 1t7m3z7](https://redlib.catsarch.com/r/Higgsfield_AI/comments/1t7m3z7/gemini_31_pro_with_higgsfield_cli/) | 8 May 2026 |
| **"Something goes wrong, please try again"** — unable to generate anything for 2+ weeks with Nano Banana Pro | [r/Higgsfield_AI 1rq8njn](https://redlib.catsarch.com/r/Higgsfield_AI/comments/1rq8njn/something_goes_wrong_please_try_again/) | ~Mar 2026 |
| **Cinema Studio 2.5 and 3.0 merged; character/location reference disabled** → *"Without this, creating consistent scenes across shots is impossible."* Directly undermines the consistency case for the 3D Jutsu → previz → final pipeline | [r/Higgsfield_AI 1sj8t19](https://redlib.catsarch.com/r/Higgsfield_AI/comments/1sj8t19/higgsfield_cinema_studio_why_was_25_and_30_merged/) | ~Apr 2026 |
| Hands-on Supercomputer verdict: *"more like a flashy demo than a production-ready feature"* — AI-sounding voiceovers, strange object physics, inconsistent characters between clips, different voice styles within one video | [codingem.com](https://www.codingem.com/i-tested-every-feature-inside-higgsfield-ai-so-you-dont-have-to/) | ~2026 |
| **Aggregator margin is real:** Higgsfield costs **$0.033–$0.070 per credit** vs Kling **$0.008–$0.010** and Runway **$0.008–$0.019** at comparable tiers | [techsifted.com](https://www.techsifted.com/roundups/higgsfield-ai-pricing-2026/) | 5 Sep 2026 |
| Credits do not roll over; top-up packs expire after 90 days | [thebomb.ca](https://thebomb.ca/blog/higgsfield-ai-review-2026/) | 29 Aug 2026 |
| A "Deceptive Tactics" post alleging quality degradation after top-ups and forced ID verification | [r/Higgsfield_AI 1skvryy](https://redlib.catsarch.com/r/Higgsfield_AI/comments/1skvryy/higgsfield_ai_deceptive_tactics/) | ~2026 — **conspiratorial framing, unsubstantiated; recorded for completeness, do not repeat as fact** |

### 6.3f The December 2025 backlash (predates 3D Jutsu, but shapes the community)

**[digitalbusiness.kz, 11 Feb 2026](https://digitalbusiness.kz/2026-02-11/higgsfield-unlimited-mnenie-storon-o-situatsii-s-beskonechnimi-podpiskami-v-dekabre/)** — the most substantive documented community-backlash episode found. It predates 3D Jutsu but is directly relevant to how much weight to put on Higgsfield's community-size and "creator-first" claims:

- A competitor (Anil Chandra Naidu Matcha, co-founder of Vadoo) published a teardown alleging: unlimited plans sold cheaply then abruptly throttled with upcharges; **mass account bans in December 2025** (thousands of users, especially Russian-language/Russian-IP, losing access without warning or ability to download their work, on grounds of "suspicious payment activity"); and that the product resells third-party models — *"the best effects and cameras are Kling 2.5 Turbo and Minimax Hailuo 2.3, but Higgsfield sells them at several times the price of direct access to those same services."* **This is an interested party's allegation — attribute it as such.**
- **CEO Alex Mashrabov's public response** (linked to `x.com/alexmashrabov/status/2021356329416393164`): *"We recognize that our internal processes and external communication have not always kept pace with our core values, and we have made mistakes. We take full responsibility for this and are actively correcting course. Our 'creator-first' DNA remains unchanged, but you will now see a much more disciplined approach to operations."* He cites **$800,000+ paid to 10,000+ creators** via Higgsfield Earn in three weeks, plus $3 M+ in free credits and $200,000 in contest prize funds.

### 6.3g Chinese- and Russian-language community signal

- **Weibo** — @零重力瓦力 (VIP7), ~13 Sep 2026, [status 5342642843945969](https://weibo.com/2/detail/5342642843945969). Creator **ADIL** demonstrates using **Astra** to drive **Blender + Higgsfield** for five cinematic complex camera-move scenes in one pass, including a seamless infinite loop and a 30-second single-take casino shot crossing four scenes. It also states the browser-side **3D Jutsu** tool can *"directly extract camera movement from a video."* **This is Higgsfield Creator-program content, not neutral commentary** — the same creator appears in Higgsfield's own Filmmaker Grant material.
- **vc.ru** — [«Создание 3D-сцен с помощью текстового запроса и GPT-6 Astra»](https://vc.ru/ai/3122081-sozdanie-3d-stsen-s-pomoshchyu-tekstovogo-zaprosa), 5 Sep 2026: a genuine short hands-on noting *"clean geometry, UV unwrap and PBR materials. Then animation by text description. **Video render via Seedance 2.5.**"* No cost figures, no bug reports.
- **Bilibili** — *"Higgsfield+Blender制作AI动画工作流"* ([BV1W8t968EFo](https://www.bilibili.com/video/BV1W8t968EFo/)) — a Chinese-language Higgsfield + Blender workflow tutorial.
- **Excluded as unreliable:** [qwbw.cn "Blender + Higgsfield AI视频工作流"](http://www.qwbw.cn/news/269571) (13 Sep 2026) is content-farm output — it contains fabricated-looking placeholder code (`API_URL https://your-ai-service.example.com/api/generate`) and admits it lacks facts, e.g. *"there is currently no unified public data on the Higgsfield plugin's specific version number, VRAM usage, supported GPU models, or whether it supports local inference."* **Its "common problems" table (camera drift, VRAM exhaustion, API timeout) is generated boilerplate, NOT user-reported Higgsfield bugs — do not cite it.**

### 6.4 Reddit

- **r/Higgsfield_AI** — **765 members** as of the GummySearch snapshot of **6 September 2026**, with yearly growth of +750 members. Discussion themes are described as "solution requests", focused on *higgsfield, turbo, model, motion, ai* ([GummySearch](https://gummysearch.com/r/Higgsfield_AI/)).
- The subreddit's `/new` and `/top?t=all` listings were read in full: **not one post about 3D Jutsu, the Blender plugin, Genjutsu-by-name, or Astra.** Discord (193 k) dwarfs this subreddit roughly **250:1**.
- **Site-wide Reddit search for "3D Jutsu" returns nothing relevant** — the phrase collides with Naruto/Attack-on-Titan "talk no jutsu" content. **Searching Reddit for "Genjutsu" is worse:** the Naruto term swamps it entirely, making the Higgsfield feature **effectively un-searchable on Reddit by name.**
- No r/StableDiffusion, r/aivideo, r/blender or r/comfyui thread on 3D Jutsu or the Higgsfield Blender plugin surfaced in any search.
- **This is the single strongest structural finding about the community: Reddit is not where Higgsfield users are.** The community is on Discord, and Discord is closed. See [§6.3b](#63b-the-one-substantive-public-3d-artist-evaluation-a-proxy-not-the-higgsfield-plugin) for the one large Reddit thread that does evaluate the underlying Astra + Blender capability.

### 6.5 Third-party press and analysis (public, findable)

Because Discord is closed, the *substantive* publicly findable community signal is **press reporting on user complaints**:

- **[WION, 18 Aug 2026](https://www.wionews.com/world/the-new-ftx-higgsfield-ai-has-1-customer-care-guy-for-300-000-paying-customers-sitting-on-discord-1786997058623)** — the most substantial public account of community friction:
  - Billing disputes reportedly resolved by *"tracking down a single Discord moderator"*, commonly known as **'THEO'**.
  - *"Several users report that questions about accountability posted on the company's Discord server are **removed**."*
  - **Trustpilot rating ~3.2 / 5 across more than 1,200 reviews**; an open complaints record with the **Better Business Bureau**.
  - Higgsfield **refunded $1.35 M** to users affected by slowdowns, attributing them partly to **~40,000 fraudulent bot accounts** shut down over December–January.
  - CEO **Alex Mashrabov** (ex-Snap): *"Rapid scaling brings real challenges. We acknowledge that our internal processes and external communications haven't always kept pace with our core values, and we have made mistakes."*
  - Cofounder **Yerzat Dulat** reportedly suggested negative discussion was amplified by competitors (Runway, Midjourney named) — *"That claim has not been independently verified."*
  - Not independently verified by me: **I did not verify the Trustpilot score or the BBB record directly** — both are second-hand from this article. `[UNVERIFIED — cited to WION, not directly checked]`
- **[digitalbusiness.kz, 11 Feb 2026](https://digitalbusiness.kz/2026-02-11/higgsfield-unlimited-mnenie-storon-o-situatsii-s-beskonechnimi-podpiskami-v-dekabre/)** — "Users are unhappy with Higgsfield — what the startup's CEO answered"; coverage of the December unlimited-subscription controversy.
- **[Mitrade / Cryptopolitan, 17 Aug 2026](https://www.mitrade.com/insights/news/live-news/article-3-2004956-20260817)** — the $400 M raise, $5.4 B valuation, and Mashrabov's claim that *"customers with marketing budgets over $100 million… turn 90% of their ad creative to be generated with AI"*; production cost down from ~$100,000/min to ~$500/min.
- **[AI Primer](https://www.ai-primer.com/creative/stories/higgsfield-blender-camera-control)** — an aggregator that tracks Higgsfield's X/Twitter posts and links each claim back to the original tweet (e.g. the `Passport Rush` previs thread at `x.com/higgsfield_ai/status/2095173490358043110`). This is the most useful **public** proxy for the community's X activity, since it cites primary tweets.

### 6.6 X / Twitter and YouTube

- Higgsfield's X account is **@higgsfield** ([linked from the Higgsfield footer](https://higgsfield.ai/)). Higgsfield's X account was **suspended in February** for what the platform described as inauthentic behaviour ([WION](https://www.wionews.com/world/the-new-ftx-higgsfield-ai-has-1-customer-care-guy-for-300-000-paying-customers-sitting-on-discord-1786997058623)). `[UNVERIFIED — second-hand]`
- Higgsfield's YouTube channel is **[@HiggsfieldAI](https://www.youtube.com/@HiggsfieldAI)** ([linked from the Higgsfield footer](https://higgsfield.ai/)). I could not load YouTube search results or comment sections through the available fetch path — **YouTube comments are `[NOT PUBLICLY AVAILABLE]` to this research**.
- Direct X/Twitter post retrieval was not possible through the available fetch path. Individual tweet URLs surfaced only **second-hand via AI Primer** (e.g. `x.com/higgsfield_ai/status/2097177127577928003` for the beating-heart demo, `x.com/higgsfield_ai/status/2095141451583963229` for the Blender camera-path workflow). **Tweet content could not be read directly.** `[NOT PUBLICLY AVAILABLE]`
- Chinese-language coverage exists and is findable: a Bilibili tutorial **"Higgsfield+Blender制作AI动画工作流"** ([bilibili.com/video/BV1W8t968EFo](https://www.bilibili.com/video/BV1W8t968EFo/)) and Chinese-language workflow write-ups ([qwbw.cn](http://www.qwbw.cn/news/269571), [ldpk.cn](http://www.ldpk.cn/news/44652)). Weibo posts about Astra also surfaced ([weibo.com](https://weibo.com/2/detail/5342642843945969)). These indicate a real Chinese-speaking creator community, but I could not extract comment-level content.

### 6.7 What is honestly NOT findable

- **Any Discord message, thread, prompt pack, or bug report.** Only **invite metadata** (name, member count, presence, boosts, channel *names*) is public. Discord message content is not indexed by any search engine. The `#bug-reports` channel, the verified hub and the private Power Users hub are all closed. **Any statement about what Higgsfield Discord users think of 3D Jutsu would be fabrication.**
- **Hacker News: nothing.** No discussion found for 3D Jutsu, the Blender plugin, Genjutsu, or Astra-on-Higgsfield.
- **Community-reported 3D Jutsu gotchas, object limits, or failure modes** — none surfaced publicly.
- **Community-reported 3D Jutsu credit costs** — none surfaced. The only 3D Jutsu cost data is Higgsfield's own.
- **A "50–100 credits per 3D environment" claim** — origin not found (see [§5.11](#511-on-the-community-claim-of-50100-credits-per-3d-environment-and-200-credits-for-a-20s-seedance-25-render)).
- **Reddit discussion of 3D Jutsu / Blender plugin / Genjutsu** — none, and "Genjutsu" is un-searchable there because of the Naruto term.
- **YouTube search results and comment sections** — inaccessible; `youtube.com/results` returned **HTTP 401 + CAPTCHA**. No YouTube evidence of any kind was gathered.
- **X / Twitter post bodies** — login-walled. All X content in this report is second-hand via [AI Primer](https://www.ai-primer.com/creative/stories/higgsfield-blender-camera-control) or [RuntimeWire](https://runtimewire.com/article/higgsfield-gpt-6-astra-blender-2d-artwork-3d-model).
- **Product Hunt discussion** — unread; only a second-hand characterisation from [coding4food](https://coding4food.com/en/post/higgsfield-genjutsu-ai-video-motion-transfer-review) that the Genjutsu launch "sparked two clear camps". `[UNVERIFIED]`, and that article itself would not render for direct inspection.
- **No independent benchmark, reproducible test, or third-party quality evaluation of 3D Jutsu output exists.** Every 3D Jutsu demo located is vendor-produced or Creator-program-produced.

---

## 7. Higgsfield Academy — 3D, Blender, Astra, Genjutsu, Seedance content

The Academy at [higgsfield.ai/academy](https://higgsfield.ai/academy) organises courses into three categories: **Movie making**, **UGC & Social Content**, and **Automate & Agents**, filterable by level and duration ([Academy courses](https://higgsfield.ai/academy/courses)).

### 7.1 Courses found (as listed publicly)

| Course | Category | Level | Modules | Length |
|---|---|---|---|---|
| Blockbuster 4K: The AI Filmmaking Pipeline | Movie making | Intermediate | 10 | 40 min |
| Build an Ultra-Realistic Short Film in 4K | Movie making | Intermediate | 19 | 33 min |
| Add AI VFX to Real Footage | Movie making | Advanced | 11 | 12 min |
| Make an AI Animated Short | Movie making | Intermediate | 11 | 17 min |
| How to evaluate AI filmmaking demos | Movie making | Beginner | 11 | 20 min |
| The 3-Step Realistic AI Ad Workflow | UGC & Social Content | Intermediate | 16 | 36 min |
| Build an AI Ad Agency with Claude + Higgsfield | UGC & Social Content | Beginner | 12 | 22 min |
| Seedance 4K: Cinematic Realism | — | — | — | — |
| Automate a Faceless Niche Channel | Automate & Agents | Intermediate | 11 | 10 min |
| **Build 3D Games with MCP** | **Automate & Agents** | **Beginner** | **10** | **12 min** |

Sources: [Academy](https://higgsfield.ai/academy), [Academy courses](https://higgsfield.ai/academy/courses), [Automate & Agents filter](https://higgsfield.ai/academy/courses?category=automate-agents).

### 7.2 Relevance assessment — the honest answer

- **"Build 3D Games with MCP"** is the **only** course with 3D in its title: *"Build and publish three no-code 3D game prototypes with an MCP-connected workflow, then compare output, cost, and early marketplace results."* It is about **games via MCP**, not 3D Jutsu or the Blender plugin ([Automate & Agents](https://higgsfield.ai/academy/courses?category=automate-agents)).
- **No dedicated 3D Jutsu course, Blender plugin course, Astra course, or Genjutsu course is published.** `[NOT PUBLICLY AVAILABLE]` — none appeared in the Academy index, the category filters, or any search.
- **Astra appears only as a *tool* inside other courses, not a subject:** the "Build an Ultra-Realistic Short Film in 4K" course is *"built shot by shot with **Claude Fable 5** and Seedance 2.0 4K"* ([Academy](https://higgsfield.ai/academy)) — and "Make an AI Animated Short" is also in the Movie making track.
- **The Academy is the home of the Prompt Bank**, which is the most directly reusable 3D-adjacent asset: [higgsfield.ai/academy/apps/prompt-bank](https://higgsfield.ai/academy/apps/prompt-bank), with a **Camera** section of **46 examples** ([Academy](https://higgsfield.ai/academy)). See [§2.3](#23-other-published-prompt-resources).
- Academy product milestones: *"Higgsfield Academy. Learn by generating"* (**14 Jul 2026**) and *"Higgsfield Academy. New video-lesson format"* (**10 Aug 2026**) ([changelog](https://higgsfield.ai/creator-hub/changelog)).

---

## 8. Changelog — entries relevant to 3D Jutsu, Blender, Astra, Genjutsu

Source for all rows: [higgsfield.ai/creator-hub/changelog](https://higgsfield.ai/creator-hub/changelog). **Note:** Higgsfield's changelog entries carry **dates and titles but no version numbers**, so no semver-style version can be reported for the platform itself. The only public version numbers found in this research are the npm package versions in [§3.6](#36-headless-operation--yes-but-via-a-different-package).

### 8.1 Directly relevant entries (verbatim titles)

| Date | Title | Type / Category | Key content |
|---|---|---|---|
| **4 Sep 2026** | **Introducing 3D Jutsu** | Release / Platform | *"3D Jutsu is an AI-native 3D workspace from Higgsfield that works together with Supercomputer."* Turns a prompt or reference into an editable 3D scene with objects, layout, lighting, cameras and animation, then into video. *"Edits individual objects in the scene without regenerating everything."* *"Describe what you want in a prompt and pick a model, **GPT-6 Astra included**."* |
| **4 Sep 2026** | **GPT-6 Astra. Now in Supercomputer** | Feature / Supercomputer | *"GPT-6 Astra, OpenAI's new flagship model, is now available in Supercomputer."* Holds multi-step workflows; produces documents/spreadsheets/presentations; stronger visual judgment for sites, games, apps and renders. |
| **3 Sep 2026** | **Claude Fable 5.1. Now in Supercomputer** | Feature / Supercomputer | New Anthropic model, successor to Claude Fable 5; stronger on long agentic tasks; adaptive thinking always on with an effort selector. |
| **1 Sep 2026** | **Introducing Genjutsu** | Release / Video Tools | *"changes an object, location, product, or character in a video while leaving everything else as it was. **No prompt needed**: pick from 30+ presets or briefly describe the change."* Motion Transfer + Object Swap. *"Inputs: one video (up to 30 seconds) and up to 30 reference photos. Output up to 1080p."* |
| **21 Aug 2026** | **Higgsfield. Now in Blender** | Feature / **MCP & Integrations** | *"Higgsfield is now available inside Blender… with generation and scene work built right into the plugin."* Tools at launch: *"Scene Builder, 3D Model, Character Animation, Image and Video, and Camera."* Install: download the `.zip`, drag onto any open Blender window, open the panel, log in. |
| **14 Aug 2026** | **Seedance 2.5 in 1080p. Early access** | — | 1080p for the pipeline's default final-render model. |
| **12 Aug 2026** | **Cinema Studio 4.0** | — | Cinema Studio major release. |
| **6 Aug 2026** | **Seedance 2.5** | — | Seedance 2.5 launch. |

### 8.2 Adjacent entries worth knowing

| Date | Title | Why it matters here |
|---|---|---|
| 26 Aug 2026 | GLM-5.3 Flash replaces Ox Alpha in Supercomputer | GLM-5.3 Flash is one of the 3D Jutsu LLM options |
| 23 Aug 2026 | Projects. Now in Supercomputer | Shared workspace keeping context; project-scoped skills, connectors, memory, assets and Elements |
| 22 Aug 2026 | Grok Bot. Now in Higgsfield MCP | MCP agents that run on their own cloud computer with browser, filesystem and terminal |
| 20 Aug 2026 | Faceless Studio. Out now | — |
| 10 Aug 2026 | Higgsfield Academy. New video-lesson format | Academy evolution |
| 10 Aug 2026 | Audio. Redesigned, with a new model | — |
| 20 Jul 2026 | All Unlimited. Every top model, unlimited | The 1–7 day Unlimited window; **web-only**, so it excludes the Blender plugin |
| 14 Jul 2026 | Higgsfield Academy. Learn by generating | Academy launch |
| 13 Jul 2026 | Adobe After Effects in Supercomputer and MCP | The sibling plugin in the same bridge family |
| 14 Jun 2026 | Higgsfield in Photoshop | Plugin family |
| 7 Jun 2026 | Higgsfield in DaVinci Resolve | Plugin family |
| 3 Jun 2026 | Higgsfield in Figma and FigJam | Plugin family |

**Coverage:** the public changelog page renders entries back to **2 June 2026** in a single scroll; **no pagination or older archive was reachable**. `[NOT PUBLICLY AVAILABLE]` — entries before 2 Jun 2026 are not published on that page.

**Notable gap:** there is **no changelog entry** for the **Blender Bridge / `fnf-blender-mcp` headless package** (npm-published 11–12 Sep 2026) or for the phone-as-virtual-camera capability as a separate item — the bridge appears only in the Aug 20 blog guide and the plugin page. The changelog's most recent entry as of this research is **4 Sep 2026** (the page's `lastmod` in the [creator-hub sitemap](https://higgsfield.ai/creator-hub/sitemap.xml) is **2026-09-05**).

---

## Access limitations

Exactly which URLs and search paths failed, and how. All failures below are reported as observed; nothing here is inferred.

### Hard blocks

| URL / path | Failure |
|---|---|
| `https://www.npmjs.com/package/fnf-blender-mcp` | **HTTP 403** — Cloudflare interstitial ("Just a moment..."). Worked around successfully via `https://registry.npmjs.org/fnf-blender-mcp`, which returned the full package metadata **and** the complete README. |
| `https://r.jina.ai/https://higgsfield.ai/blog/higgsfield-3d-jutsu` | **HTTP 403** `AbuseAlleviationError` (code 40305): *"Anonymous access to domain higgsfield.ai blocked until Sun Sep 13 2026 08:05:41 GMT+0000… DDoS attack suspected: Too many requests."* The text-extraction proxy was unavailable for the whole higgsfield.ai domain. |
| `https://r.jina.ai/https://higgsfield.ai/creator-hub/changelog` | Same **HTTP 403** abuse block. |
| `https://higgsfield.ai/academy/courses?category=movie-making` | **HTTP 504 Gateway Timeout** when fetched via shell. Retried via the unfiltered `/academy/courses` and `/academy` pages, which succeeded. |
| `https://www.reddit.com/r/Higgsfield_AI/search.json?q=…` | **HTTP 403.** |
| `https://www.reddit.com/…` and `https://old.reddit.com/…` (direct and via text proxy) | **HTTP 403** — *"You've been blocked by network security"* / *"whoa there, pardner! … network policy"*. |
| `https://redlib.catsarch.com/…` (direct) | **HTTP 429 + Anubis proof-of-work anti-bot wall.** Worked around **only** via a text-extraction proxy (`r.jina.ai`), which succeeded — all Reddit content in this report came through that path, which is a **reliability caveat**. |
| `https://www.youtube.com/results?search_query=…` | **HTTP 401 Unauthorized + CAPTCHA warning.** No YouTube search results or comments obtainable. |
| `https://note.com/design_oyaji/n/n4f8c0f169eb2` (direct) | HTTP 200 but **body JS-gated to the title only**; recovered via text-extraction proxy. |
| `https://search.marcia.cc/…` (attempted Reddit mirror) | **DNS failure — ENOTFOUND.** |

### Truncation (content exists but the fetch tool cut it off)

The web-fetch tool truncates long pages. This affected, and was worked around by fetching raw HTML with `Invoke-WebRequest` and extracting text, for:

- `https://higgsfield.ai/blog/higgsfield-3d-jutsu` — truncated before the **"What does it cost?"** section and the second Recreate link. **Recovered in full** via raw-HTML extraction (this is where the official 3D Jutsu per-message price table came from).
- `http://web.archive.org/web/20260910081616/https://higgsfield.ai/blog/higgsfield-3d-jutsu` — the archived copy truncated at the **same** point. **Also recovered** via raw-HTML extraction against the live URL.
- `https://higgsfield.ai/plugins/blender`, `https://higgsfield.ai/genjutsu`, `https://higgsfield.ai/academy`, `https://higgsfield.ai/academy/courses` — all truncated; **recovered** via raw-HTML extraction where the content was server-rendered.

### JavaScript-only rendering and other access walls

| URL | Failure |
|---|---|
| `https://higgsfield.ai/3d-jutsu` | **Loads but renders no content server-side** — returns only a loader SVG and the site footer. The actual workspace is behind a **login wall**. All 3D Jutsu mechanics in this report therefore come from the blog guide, the changelog, and the official FAQ, **not** from direct inspection of the tool. The `?recreate=` deep links could not be opened to confirm they hydrate. |
| `https://higgsfield.ai/creator-hub/changelog` (via the fetch tool) | Returned **only the `<head>`/header**. The workaround (raw `Invoke-WebRequest`, strip `<script>`/`<style>`, strip tags) **fully recovered** the changelog text back to 2 Jun 2026. |
| `https://higgsfield.ai/creator-hub/changelog` (via `web.archive.org`) | Archived copy likewise rendered **only the header** — Web Archive did not capture the hydrated list. |
| `https://higgsfield.ai/creator-hub/changelog?page=1` | No pagination; identical header-only result. **No pre-June-2026 changelog is publicly reachable.** |
| `https://higgsfield.ai/pricing` | HTTP 200 but **JS-only** — the recovered text is 367 characters containing just the nav and footer. **No plan/credit numbers are server-rendered**, so all plan-tier figures in this report come from the blog and help-centre pages rather than the pricing page itself. |

### Source-specific gaps

| Target | Outcome |
|---|---|
| **Discord (`discord.com/invite/higgsfield`)** | Not accessed — no Discord login in this research scope. **No Discord content was read, and none is claimed.** Whether the invite is currently live was **not** verified. |
| **X / Twitter posts** | Direct retrieval failed; X post URLs surfaced only **second-hand** through AI Primer's citations. Tweet content was **not** read directly. |
| **YouTube** | Channel identity confirmed via the Higgsfield footer (`@HiggsfieldAI`); **video descriptions and comment sections could not be retrieved**. YouTube comments are `[NOT PUBLICLY AVAILABLE]` to this research. |
| **Reddit** | No r/higgsfield, r/Higgsfield_AI, r/StableDiffusion, r/aivideo, r/blender or r/comfyui thread on 3D Jutsu, the Blender plugin, or Genjutsu surfaced in any search. Only aggregate r/Higgsfield_AI stats were obtainable ([GummySearch](https://gummysearch.com/r/Higgsfield_AI/)). |
| **GitHub issues** | The repository declares an issues URL ([github.com/higgsfield-ai/fnf-local-pluging-bridge-mcp/issues](https://github.com/higgsfield-ai/fnf-local-pluging-bridge-mcp/issues)) but the repo landing page returned mostly GitHub chrome and **no issue list or filed bug reports were retrievable**. **No public bug/regression list exists that I could find.** |
| `https://coding4food.com/en/post/higgsfield-genjutsu-ai-video-motion-transfer-review` | Fetched HTTP 200 but the **body did not render** — only page chrome returned. **A Genjutsu review article exists on this site but its content is not obtainable.** |
| `https://digg.com/tech/627fi5zb` | Fetched HTTP 200 but **only the title rendered** ("Higgsfield AI Launches Genjutsu for Seamless Video Transformations"). Body content not obtainable. |
| `https://radiofacts.media/…/ai-video-is-starting-to-look-more-like-a-film-set-than-a-generator/` | Fetched HTTP 200, dated **9 Sep 2026**, but the article **body did not render** past the byline. |
| `https://www.wionews.com/…` | Fetched successfully, but the page returned a very large shared-chrome payload; the article body **was** recovered. **The Trustpilot score (~3.2/5) and BBB record cited from it were not independently verified** against Trustpilot or BBB directly. |

### Additional access walls found while extracting prompts

| URL / path | Failure |
|---|---|
| `https://higgsfield.ai/academy/apps/prompt-bank` | **HTTP 504 Gateway Timeout**; the `?section=camera` variant returned **41 bytes**. The prompt-bank templates are only obtainable from the server-rendered `/academy` page payload, not from the prompt-bank URL itself. |
| `https://higgsfield.ai/prompt-guide`, `https://higgsfield.ai/supercomputer` | Both returned the **same 5,293-byte error shell** as the 504 page. |
| `https://api.sanity.io` (`s479xw3z.api.sanity.io`) — the CMS behind Higgsfield's blog | Queries `*[_type=="post"]` and `array::unique(*[]._type)` both returned **`result: []`**. **The dataset is not anonymously readable**, so raw CMS payloads (and any unpublished content) could not be obtained. |
| `https://archive.ph/newest/https://higgsfield.ai/blog/higgsfield-3d-jutsu` | **HTTP 404 — "No results"**. archive.today holds no capture. |
| Web Archive CDX for the 3D Jutsu post | Only **2 snapshots** exist (`20260910081517`, `20260910081616`), both with **identical** truncated content; the `id_` raw variant reached slightly further but still truncated. |
| `https://x.com/...` | **`web_fetch` is not viable on X** (login wall). Tweet text *is* retrievable via `curl` from the `<h1 class="sr-only">` block — this is how the [Astra → Blender AirPods prompt](https://x.com/higgsfield_ai/status/2097407934598930472) was verified directly for this report. `og:description` truncates at ~200 chars, so the `sr-only` block is the reliable target. |
| `https://r.jina.ai/https://web.archive.org/...` | **HTTP 403** — the proxy also refuses `web.archive.org`, flagging *"Request to local network"*. |
| Higgsfield YouTube video descriptions/transcripts | **Not retrieved** — no transcript tooling available, and `youtube.com/results` returned 401/CAPTCHA. |

### Structural gaps in Higgsfield's own documentation

These are **publisher-side** gaps rather than access failures, and they matter:

- **No 3D Jutsu entry in the help centre.** The [creator-hub sitemap](https://higgsfield.ai/creator-hub/sitemap.xml) lists help-centre articles for Cinema Studio, Marketing Studio, Supercomputer, Canvas, AI Influencer, Soul, Seedance, Kling, Nano Banana, Popcorn and DoP — but **no article for 3D Jutsu and none for the Blender plugin**. All first-party 3D Jutsu documentation is the single blog post plus the changelog entry.
- **No published object-count limit, polygon budget, seed control, or GLB size cap** for 3D Jutsu, anywhere.
- **No published credit cost for previz MP4 export, static-frame export, or GLB export.**
- **No published per-image credit price for Soul 2.0 or Soul Cinema.**
- **No published Genjutsu aspect-ratio list.**
- **No version numbers in the changelog.**

---

## Appendix B: Higgsfield Academy camera prompt bank — all 10 templates, verbatim

Recovered from the server-rendered [Academy](https://higgsfield.ai/academy) payload, section `?section=camera`. These are the **only first-party, reusable, slot-parameterised prompt templates** Higgsfield publishes. Note the `[bracketed]` slot convention and the enumerated alternative inside slot 4 (`[29 or 18]`). Each ships a **"Recreate"** deep link on the Academy page.

**1. Static / locked-off**
```
The camera stays planted in one immovable position from the first frame to the last. Zero motion — no drift, no shake, no breathing, no stabilization float, no micro-drift; absolute rock-solid stillness throughout. Angle, elevation, distance to the scene and the overall composition are frozen and never altered; every ounce of motion comes from the scene itself, never from the camera. The clip closes on precisely the framing it began with, identical down to the pixel.
```

**2. Pan right**
```
Rotate the camera horizontally from left to right from one fixed point, like a standing head-turn, starting on [composition A] and sweeping across [the environment]; no sideways travel, no dolly, no truck, no arc, no slide, no zoom, no tilt. Speed: smooth constant rotation, decelerating gently at the end. Framing: keep the horizon level while new space enters from the right side of the frame only through rotation; [the landing subject] stays beyond the right edge until the rotation brings them in. End: settle on a clear final composition on [the landing subject] and hold.
```

**3. Tilt up**
```
Fixed camera position at [lens height]. Pure TILT UP: the camera rotates vertically upward at one constant smooth speed from [the lower anchor] to [the upper framing], no crane rise, no pedestal, no dolly, no zoom, no horizontal drift; the camera's position never changes. The tilt starts on [the lower anchor] and finishes framing [the subject] in the upper third, decelerating into a static hold.
```

**4. Optical zoom**
```
Locked tripod, zero rotation, zero travel — the entire move is optical, a focal-length change only: one slow perfectly even continuous zoom in from [84] degrees to [29 or 18] degrees across the full duration, no speed changes, no steps, no wobble. The camera position is fixed and never moves; only the field of view changes; perspective stays constant and there is no parallax — the background keeps the exact same apparent size relative to the subject while the framing tightens.
```

**5. Dolly-zoom (Vertigo)**
```
The camera physically dollies forward from [6] meters to [2.5] meters while the lens simultaneously zooms out from [18] to [84] degrees field of view, in one continuous, perfectly synchronized ramp. The subject's head size stays EXACTLY constant in frame the entire time; the background behind them visibly stretches, elongates and recedes into depth, [the repeating background elements] pulling away. Constant lens height, no pan, no tilt, no handheld drift; the two motions start and end together.
```

**6. Rack / follow focus**
```
The camera hard-locked on a tripod with no pan, no tilt, no push, no drift; the only optical change is FOCUS. Hold sharp on [plane A — the far anchor]; then rack once to [plane B — the near subject]; then follow focus on the subject if they move toward the lens. Speed: the rack is slow, smooth and continuous with no hunting and no overshoot; the follow focus tracks without breathing. Framing: the composition never changes; exactly one plane is sharp at any moment, the other melts into clean bokeh; the subject grows in frame only by physically approaching the lens. End: settle sharp on [the final subject framing], the far plane dissolved to soft bokeh behind.
```

**7. Jib rise**
```
A smooth jib rise from [1.2] meters to [9] meters altitude over the shot, with a gentle continuous downward tilt that keeps the subject anchored in [the lower third] of frame as the world opens above and around them. No lateral orbit, no truck, no zoom, no speed ramps; one continuous vertical reveal easing into a high hold.
```

**8. Circular drone**
```
A smooth constant-speed circular drone flight around the subject — [8]-meter radius, [4]-meter altitude, traveling screen-[right] (clockwise seen from above), covering roughly a [200]-degree arc across the shot. The horizon rotates continuously behind the subject; no altitude change, no radius drift, no zoom, no speed ramps.
```

**9. Fly-away**
```
The camera starts [2.5] meters ahead of the subject at [3] meters altitude and flies backward and upward along the axis in one continuous accelerating move, reaching about [40] meters distance and [25] meters altitude by the end. The subject stays centered, then the whole [craft / scene] centers itself in frame as it shrinks; the horizon line rises steadily through the frame. No orbit, no zoom, no speed reversals.
```

**10. Dolly-in on rails**
```
One continuous decisive dolly in on straight ground rails — pure forward travel at constant speed along the axis toward the subject, at a locked constant lens height of [1.5] meters, decelerating smoothly into a static hold at the end framing. The field of view never changes — no zoom: the perspective shifts because the camera physically approaches, near objects sweeping out past the frame edges with strong parallax. No pan, no tilt, no crane, no handheld drift; dead-level travel from first frame to last.
```

Source: [higgsfield.ai/academy](https://higgsfield.ai/academy), camera prompt bank (46 examples; the 10 above are the recoverable full templates).

**Why this matters for the 3D Jutsu pipeline:** these are the **exact register** the 3D Jutsu camera NOT-rules imitate — *"the camera never stops, never reverses, never zooms"* is template 1's and template 4's logic applied inside a blockout prompt. If you are authoring a 3D Jutsu camera trajectory, cribbing the denial lists from these ten templates is the fastest route to the house style.

---

## Appendix C: The Astra/Blender demo corpus (prompt text not published)

| Demo | Claimed outcome | Source |
|---|---|---|
| Mies van der Rohe house | *"rebuilt an iconic Mies van der Rohe house with millimeter accuracy. >studied an existing scene >found the original plans >built the full 3D setup. Materials, lighting, vegetation, camera angles. Fully editable."* Tool chain: 3ds Max + Corona + Higgsfield + GPT-Images 2.5 | [X](https://x.com/higgsfield_ai/status/2097474491857482142) |
| AirPods Pro 3 case | Print-ready STL/3MF from a sketch — **the only one with its prompt published** (see [§2.6](#26-the-only-fully-published-astra--blender-agent-prompt)) | [X](https://x.com/higgsfield_ai/status/2097407934598930472) |
| Nail art → 3D printable | *"The designs came from Higgsfield Soul 2.0. Astra recreated the flowers, butterflies, and intricate details in Blender."* | [X](https://x.com/higgsfield_ai/status/2097515771782205831) |
| Space Shuttle Discovery | *"192 assemblies and crew items to explore. Take it apart, put it back together, look inside."* | [X](https://x.com/higgsfield_ai/status/2097481392313758124) |
| Photo → building-block model | *"Rotate it. Take it apart. Put it back together with a slider. Assembly instructions and a parts list included."* | [X](https://x.com/higgsfield_ai/status/2097488254555857226) |
| Interactive 3D product website | *"Every element was made in Blender via Higgsfield plugin."* | [X](https://x.com/higgsfield_ai/status/2097048653886312732) |
| Interactive anatomy | *"GPT-6 Astra built a heart you can take apart while it's beating."* | [X](https://x.com/higgsfield_ai/status/2097177127577928003) |
| Studio rebuild | Creator reports GPT-6 Astra recreated a studio as a Blender scene from **5 photos + 3 panoramas in 11 minutes** | [AI Primer](https://www.ai-primer.com/creative/stories/astra-studio-blender) |
| Car site (no 3D models) | An Astra workflow whose prompt **and repo** were published — deliberately uses pre-generated forward/reverse LTX clips around a fixed base frame instead of 3D geometry | [prompt](https://x.com/AmirMushich/status/2098464885709386026), [repo](https://github.com/amirmushichge/video-states-website) |

⚠️ **All of these are vendor-published or Creator-program demos.** No independent reproduction, wireframe, or benchmark accompanies any of them. Treat the "millimeter accuracy" and "192 assemblies" claims as **vendor assertions**. `[UNVERIFIED]`

---

## Appendix A: verified fact index by topic

| # | Topic | Primary source |
|---|---|---|
| 1 | 3D Jutsu mechanics, duration, aspect, modes, exports | [higgsfield.ai/blog/higgsfield-3d-jutsu](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |
| 1 | 3D Jutsu ship date | [changelog, 4 Sep 2026](https://higgsfield.ai/creator-hub/changelog) |
| 2 | Both Recreate prompts, decoded | [higgsfield.ai/blog/higgsfield-3d-jutsu](https://higgsfield.ai/blog/higgsfield-3d-jutsu) (page source) |
| 2 | Camera prompt bank, 46 examples | [higgsfield.ai/academy](https://higgsfield.ai/academy) |
| 2 | Seedance prompt library + section grammar | [higgsfield.ai/blog/seedance-2-5-prompting-guide](https://higgsfield.ai/blog/seedance-2-5-prompting-guide) |
| 2 | **Only published Astra → Blender prompt (AirPods case)** | [@higgsfield_ai on X](https://x.com/higgsfield_ai/status/2097407934598930472) — retrieved via direct fetch |
| 2 | Second 3D-grammar prompt ("LOCKS" variant) | [higgsfield.ai/blog/generate-ai-videos-from-chatgpt](https://higgsfield.ai/blog/generate-ai-videos-from-chatgpt) |
| 2 | Community 3D prompt collection (63 prompts) | [github.com/petergpt/3d-prompt-collection](https://github.com/petergpt/3d-prompt-collection) |
| 2 | Community Blender-blockout workflow guide | [gachoki.com](https://gachoki.com/block-in-blender-finish-with-ai/) |
| 2 | OpenAI GPT-6 Astra prompting guidance | [developers.openai.com](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) |
| 3 | Blender install + bridge + tabs | [higgsfield.ai/blog/higgsfield-blender-plugin](https://higgsfield.ai/blog/higgsfield-blender-plugin) |
| 3 | Blender plugin page, 7 tabs, 25 M users | [higgsfield.ai/plugins/blender](https://higgsfield.ai/plugins/blender) |
| 3 | Headless bridge, 19 tools, limits | [registry.npmjs.org/fnf-blender-mcp](https://registry.npmjs.org/fnf-blender-mcp) |
| 3 | Bridge repo | [github.com/higgsfield-ai/fnf-local-pluging-bridge-mcp](https://github.com/higgsfield-ai/fnf-local-pluging-bridge-mcp) |
| 4 | Genjutsu limits + 2 techniques | [higgsfield.ai/blog/higgsfield-genjutsu](https://higgsfield.ai/blog/higgsfield-genjutsu) |
| 4 | Seedance 2.5 specs, refs, audio | [help centre: Seedance](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-seedance) |
| 4 | Seedance 2.5 detail | [higgsfield.ai/blog/seedance-2-5-on-higgsfield-2026](https://higgsfield.ai/blog/seedance-2-5-on-higgsfield-2026) |
| 5 | 3D Jutsu per-message pricing | [higgsfield.ai/blog/higgsfield-3d-jutsu](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |
| 5 | Seedance 2.5 credits | [higgsfield.ai/blog/seedance-2-5-pricing-2026](https://higgsfield.ai/blog/seedance-2-5-pricing-2026) |
| 5 | Genjutsu credits | [higgsfield.ai/blog/higgsfield-genjutsu](https://higgsfield.ai/blog/higgsfield-genjutsu) |
| 5 | Cinema Studio / model comparison | [higgsfield.ai/blog/ai-video-credits-explained](https://higgsfield.ai/blog/ai-video-credits-explained) |
| 5 | Supercomputer credit math (~200 cr full production) | [higgsfield.ai/blog/higgsfield-supercomputer-guide](https://higgsfield.ai/blog/higgsfield-supercomputer-guide) |
| 5 | Credits, plans, expiry, refunds | [help centre: credits](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work) |
| 5 | Unlimited is web-only | [help centre: credits](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work) |
| 5 | Independent corroboration, 6.5 cr/s | [techsifted.com](https://www.techsifted.com/roundups/higgsfield-ai-pricing-2026/) |
| 6 | **Discord member count 193,059 (hard data)** | [Discord invite API](https://discord.com/api/v10/invites/higgsfield?with_counts=true) |
| 6 | Discord structure (publisher's own description) | [help centre: Discord](https://higgsfield.ai/creator-hub/help-center/getting-started/higgsfield-community-on-discord) |
| 6 | Community friction, Trustpilot, refunds | [WION, 18 Aug 2026](https://www.wionews.com/world/the-new-ftx-higgsfield-ai-has-1-customer-care-guy-for-300-000-paying-customers-sitting-on-discord-1786997058623) |
| 6 | Funding, $5.4 B Series B | [TechCrunch, 17 Aug 2026](https://techcrunch.com/2026/08/17/higgsfield-raises-400m-series-b-quadrupling-its-valuation-in-8-months-to-5-4b/) |
| 6 | Reddit size (765 members) | [GummySearch r/Higgsfield_AI](https://gummysearch.com/r/Higgsfield_AI/) |
| 6 | Astra + Blender 3D-artist evaluation | [r/OpenAI 1w7ppcj](https://redlib.catsarch.com/r/OpenAI/comments/1w7ppcj/fable_51_vs_gpt_6_astra_3d_blender_mind_blowing/) |
| 6 | 500-credit failure report (Supercomputer) | [note.com/design_oyaji](https://note.com/design_oyaji/n/n4f8c0f169eb2) |
| 6 | Dec 2025 backlash + CEO response | [digitalbusiness.kz](https://digitalbusiness.kz/2026-02-11/higgsfield-unlimited-mnenie-storon-o-situatsii-s-beskonechnymi-podpiskami-v-dekabre/) |
| 7 | Academy courses & prompt bank | [higgsfield.ai/academy](https://higgsfield.ai/academy) |
| 8 | Full changelog | [higgsfield.ai/creator-hub/changelog](https://higgsfield.ai/creator-hub/changelog) |

---

## Confidence summary

| Claim class | Confidence |
|---|---|
| 3D Jutsu UI, modes, exports, duration/aspect limits | **High** — official guide, recovered in full |
| 3D Jutsu per-message LLM pricing table | **High** — official guide table, recovered in full |
| Both Recreate prompts (verbatim) | **High** — decoded from page source |
| Astra → Blender AirPods prompt (verbatim) | **High** — retrieved directly from the X post's `sr-only` block |
| No `NEGATIVE CONSTRAINTS` section; no seed parameter | **High** — verified by direct string search of the guide |
| Seedance house grammar / prompt-pack inventory | **High** — counted from page source |
| Blender plugin install, tabs, bridge URL, Blender 4.2–5.1 | **High** — official guide + product page + third-party corroboration |
| Headless bridge, 19 tools, limits, non-Claude clients | **High** — npm registry README |
| Windows/Linux Blender unverified | **High** — stated verbatim in the package README |
| Genjutsu limits and pricing | **High** — official guide; pricing corroborated by third party |
| Seedance 2.5 specs, references, audio-is-free | **High** — official help centre + blog |
| Cinema Studio / model credit comparison | **Medium–High** — official, but table headings in the source are inconsistently rendered |
| Discord member count 193,059 | **High** — Discord API, retrieved directly |
| Platform user counts (15 M / 22 M / 25 M / 30 M) | **Low** — self-reported and mutually contradictory |
| "~200 credits" origin | **High** — traced to the official Supercomputer guide |
| "50–100 credits per 3D environment" | **None — origin not found** |
| 3D Jutsu object limits, seeds, render/export costs | **Not published anywhere** |
| **QR-code phone pairing for the Blender Camera tab** | **Not published anywhere — premise unconfirmed** |
| Community sentiment inside Discord | **Unknown and unknowable publicly** |
| Third-party quality evaluation of 3D Jutsu | **None exists** |
| X/Twitter and YouTube content | **Second-hand** — X login-walled; YouTube inaccessible |
| Reddit content | **Medium** — retrieved via a mirror/proxy, not canonical Reddit |
