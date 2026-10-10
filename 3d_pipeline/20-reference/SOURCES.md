# SOURCES — Ingested Evidence Ledger

**Rule:** nothing enters this knowledge base without a source. Every entry records *what it proved*
and *how far to trust it*.

## Confidence scale

| Tag | Meaning |
|---|---|
| **A — Primary** | Higgsfield's own documentation, blog, help centre, or official tutorial video |
| **B — Demonstrated** | a practitioner showing the actual working screen; steps are observable |
| **C — Reported** | a dated third-party write-up or a creator's stated figure; plausible but not reproduced here |
| **D — Inference** | our own synthesis across sources; not directly stated by any single source |

---

## S1 — "I Let Astra Run Blender + Higgsfield — 5 Cinematic Scenes Built"

- **Publisher:** Higgsfield AI (official channel) · **Published:** 2026-09-12 · **Length:** 15:36
- **URL:** <https://www.youtube.com/watch?v=vUYq38wC_xI>
- **Full materials:** <https://higgsfield.ai/s/blender-higgsfieldai-Viyiew>
- **Plugin:** <https://higgsfield.ai/s/blender-higgsfieldai-zHuqyR>
- **Confidence:** **A (primary, official)** for workflow; **B** for specific prompt wording
- **Ingested:** transcript (auto-captions, cleaned) → `research/phase1_sources/raw/vUYq38wC_xI.en.txt`

**Chapter map (verbatim, for timestamp anchoring):**

| Time | Chapter |
|---|---|
| 00:00 | Intro |
| 00:37 | The infinite loop — preview and concept |
| 01:40 | Connect Astra, Blender & Higgsfield |
| 02:09 | Building and refining the infinite loop |
| 05:39 | The impossible mirror shot |
| 07:48 | 3D Jutsu — four locations, one continuous shot |
| 10:39 | Concert — one singer, 66 dancers |
| 12:54 | The one-take vacuum commercial |
| 15:05 | Recap and outro |

**Three-layer demonstration (canonical pattern — this video is the reference implementation):**

| Layer | What was done |
|---|---|
| **L1 Blocking** | Astra builds 3D blocking in Blender: "editable camera path with a bit of handheld drift"; confirms "layout and timing are locked", sets timeline markers, walks the animation. Astra uses **computer-use skills to check the viewport live inside Blender**. |
| **L2 Assets** | Character sheets via Higgsfield (4 detective options generated, one selected); location via **Soul Cinema**; layout frame → cinematic interior via **Nano Banana**. |
| **L3 Realisation** | **Seedance 2.5**, 30 s, 16:9, "one continuous shot", **two versions generated** to choose from. |

**Setup path proven here (canonical):**
1. Higgsfield → Plugins → Blender → download plugin.
2. Open Blender, **drag the plugin in**, log into the account → Higgsfield toolbar appears in the viewport.
3. Open the chat client → Plugins (left) → find Higgsfield → enter *"add Higgsfield / use Blender"* to connect Astra + Blender + Higgsfield.

**Five scene patterns proven:**

| Scene | What it proves | Key mechanic |
|---|---|---|
| Infinite zoom-out loop | loop seam is a *3D problem* | clone the scene; opening and closing frames match **even though the camera is in totally different positions**; previz opening frame becomes the L2 base image used for *both* ends |
| Impossible mirror shot | geometry defeats physics | "a **mirrored copy of the room** with both characters moving in sync; the mirror itself is just an opening — it looks like a reflection, but the camera can pass straight through" |
| 3D Jutsu, 4 locations, 30 s continuous | text prompts cannot hold a journey | separate paths for camera and characters so each is adjustable; colour-codes roles (black = man, white = woman, yellow = kitchen workers); add ceilings/doors on request |
| Concert, 1 singer + 66 dancers | crowd scenes need occupancy planning | dancers as **boxes**, singer as a **different shape**; rings of 10 / 20 / 36; columns; **"handle the actual choreography in the prompt so the model keeps their movement fluid instead of copying the stiff blocking"** |
| One-take vacuum commercial, 30 s | lens changes within one take | "shifting camera sizes and focal lenses on the fly"; ultra-crisp macro; ends on the product; blocking kept for client revisions |

**Cost doctrine stated by the source:** *"You're not just saving credits on endless rerolls.
You're saving tons of time locking in the exact camera movement you want."* And: *"Plan the camera
and timing first — spend fewer AI credits on endless rerolls."*

---

## S2 — "GPT 6 Astra Forever Changed 3D Animations" (Zane Hoyer)

- **Publisher:** Zane Hoyer · **Published:** 2026-09-12 · **Length:** 8:14
- **URL:** <https://www.youtube.com/watch?v=pJLPpB_zueg>
- **Tool link shared:** <https://higgsfield.ai/s/zanehoyer-CDmpQX>
- **Confidence:** **B (demonstrated)** for workflow · **C (reported)** for cost figures
- **Ingested:** transcript → `research/phase1_sources/raw/pJLPpB_zueg.en.txt`

**What it proves — the non-Blender route and the cost model:**

- Astra inside Higgsfield's **3D Jutsu** tab builds a complete, editable 3D environment from a single
  prompt; the author scrolls a real layer stack in "3D software" — i.e. genuine editable geometry,
  not a video.
- **Image → 3D environment** works by uploading a photo, often sourced from Pinterest as a style
  reference.
- **`.glb` upload** works: free models from CGTrader import into the scene and can be animated.
- **Camera control:** camera-view mode lets you place a start and end position, press play, and
  review the move before rendering.
- **Environment reuse is the cost lever:** *"once this is actually built, we can change out objects,
  add in new objects, and we can reuse this 3D scene. You can get like six to eight clips out of
  this one environment."*
- **Prompt-shaping lesson:** *"if you just tell it to generate you a 3D scene, it's usually pretty
  basic... I try and get all of that in the first prompt, so I don't have to keep re-prompting it
  once it generates it."* Requests detail explicitly: *"Spend lots of time on details."*
- **Two-render request pattern** (verbatim, high value): *"I want you to render this out with
  cinematic lighting and add texture to all of the 3D objects so that this looks like a professional
  3D artist did it. Render me one version using the actual 3D objects and the camera, and then one
  version with Seedance 2.5 using the exact positioning and motion from the camera."*
- **Iteration reality:** the first pass was "not super realistic"; refinement requests followed
  (more realistic trees → more skull detail → "make the human more realistic and polished").
- **Costs as reported [C]:** most 3D environments **50–100 credits** each; **rendering out with
  textures, and Seedance 2.5 at 20 s, reached up to ~200 credits** — stated as the main credit sink.
  **17 finished 3D videos ≈ 3,000 credits ≈ 200 seconds of video**, *with a new environment
  generated for every scene.*
- **Delivery:** animations drop straight into **DaVinci Resolve** via an existing plugin.

**Why this source matters:** it is the clearest statement that the expensive layer is L3, and that
L1/L2 reuse — not prompt cleverness — is what controls cost.

---

## S3 — "I Tried The New Blender + Higgsfield Workflow (And It's Insane)" (askNK)

- **Publisher:** askNK · **Published:** 2026-09-12 · **Length:** 9:04
- **URL:** <https://www.youtube.com/watch?v=BmkNqEYjQFA>
- **Higgsfield × Blender landing:** <https://higgsfield.ai/s/higgsfield-x-blender-yt-asknk-BSypdK>
- **Plugin page:** <https://higgsfield.ai/plugins/blender>
- **Confidence:** **B (demonstrated)** — the connector setup is shown step by step on screen
- **Ingested:** transcript → `research/phase1_sources/raw/BmkNqEYjQFA.en.txt`

**Chapter map (verbatim):**

| Time | Chapter |
|---|---|
| 00:00 | Blender Meets Higgsfield |
| 00:42 | Get the Plugin and Bridge |
| 01:27 | Connect Claude to Higgsfield |
| 02:01 | Install and Sign In |
| 02:24 | Tour the Higgsfield Panel |
| 03:10 | Prompt a Chase Scene |
| 04:31 | Build and Review Renders |
| 05:39 | Tweak and Playblast in Blender |
| 06:40 | Claude Writes a Shot Prompt |
| 07:18 | Generate Final Cinematic |
| 08:32 | Wrap Up and Next Steps |

**Setup path (canonical, connector-level detail):**
1. Higgsfield → find the **Blender plugin** → download it.
2. Scroll to the bottom of the plugin page and **copy the bridge URL**. *"The bridge URL would act
   as an agent that will work hand in hand with both Claude and Blender."*
3. In Claude: **+ → Add connector → Browse connectors → search "Blender" → add.**
4. Then **Add connector → Add custom connector → paste the MCP link → name it "Higgsfield" →
   Continue → Add.** This requires signing into the Higgsfield account.
5. In Blender: **drag and drop the downloaded plugin zip directly into Blender** — it installs.
6. Verify: **Edit → Preferences → Add-ons → search "Higgsfield"**. Then burger menu → **Save
   Preferences** → close.
7. Sign into Higgsfield from inside Blender.

**Viewport panel (press `N`):** recent assets, a folder of all recent assets, **Scene Builder**
models, selectable **3D models**, and parameter groups for **character animation, images, video and
camera**. Camera exposes a **QR code to pair a mobile device as the camera-move capture** source.

**The loop, as demonstrated:**
- Describe the scene (either typed directly, or authored by Claude). Example given: build a 30-second
  single-scene chase with a black sports car through a wet city at night, a dark police car behind,
  buildings, street lights, wet road, headlights, tire smoke, realistic vehicle movement, and
  **dynamic chase cameras following from behind**.
- The agent builds the scene from scratch, requesting permissions along the way; **renders are
  produced and land in a folder** you can open directly.
- **Review inside Blender:** hit play — the scene is fully built with street lights, vehicles and
  camera animation; you can leave camera view, orbit the whole set, and inspect.
- Optional manual tweaks, then **render the playblast**: *Output Properties → Output → media = Video,
  container MPEG-4, codec H.264, resolution HD 1920×1080, 24 fps*, then **Viewport → Render Playblast**.
- **Then the key move:** hand Claude the viewport playblast plus object reference images and ask for
  a **30-second prompt based on the blocking**: *"read the input video and write out the prompt
  second by second to match the camera motion in the clip."* Claude reads the clip frame by frame and
  writes the matching prompt.
- Paste that prompt into **Cinema Studio 4.0** (or switch to **Seedance 2.5**) with the assets
  imported; reference individual objects with the **`@` mention** syntax on the image; set duration to
  30 s; generate.

**Why this source matters:** it is the only one that documents the **connector-level setup** and the
**playblast → frame-by-frame prompt** handoff explicitly. That handoff is the mechanism that makes
L1→L3 precision transferable.

---

## S4 — Higgsfield 3D Jutsu guide (official blog)

- **Publisher:** Higgsfield · **Published:** 2026-09-05 · **Updated:** ~1 week after
- **URL:** <https://higgsfield.ai/blog/higgsfield-3d-jutsu>
- **Confidence:** **A (primary)** — authoritative for capability surface, parameters and workflow

**Proved:**
- 3D Jutsu is the browser blocking/previz workspace; scenes persist under **My Scenes**.
- Scene starts from prompt + optional references, with parameters: **Model**, **Duration 1–60 s
  (default 15)**, **Aspect 16:9 / 9:16 / 1:1 / 4:3 / 3:4 / 21:9**.
- Editor surface: add object (primitives, sun/point/spot lights, cameras), curated **GLB asset
  library** + **Mixamo characters**, scene properties (background colour, resolution, light
  intensity), full object hierarchy, **animation timeline**, camera presets and trajectory editing,
  **revision history** (preview a checkpoint, restore as new head), and **export as animated MP4,
  static frame, or GLB** with dimensions and file size set before render.
- Agent behaviour modes: **generate without asking**, **ask before generating**, and a separate
  **ask mode** that answers without touching the scene.
- Agent LLM selector: **Auto** (default, free) plus **GPT 6 Astra, Claude Fable 5.1, Claude Opus 5,
  GPT 5.6 Sol, GLM-5.3 Flash** — switchable per chat.
- Collaboration: share by email as admin / collaborator / viewer; access from invited-only to
  anyone-with-link.
- **The canonical four-step workflow, verbatim in structure:**

  1. **Block the previz** — agent builds grey proxies: set, character, and camera path with framing
     and timing.
  2. **Render the previz** — Export renders the camera timeline to video; "the grey blockout becomes
     a reference clip for the intended camera move and the character's behaviour."
  3. **Generate the references** — character from **Soul 2.0** (portrait carrying identity and
     wardrobe), location from **Soul Cinema**.
  4. **Combine in the same chat** — character + location + previz render in one conversation; one
     message asks the agent to put them together.

**The official blockout prompt (verbatim, highly instructive — reproduced in
`30-library/prompt-vault/RECOVERED-PROMPTS.md`)** demonstrates the house style:
- Hard negatives written as caps: `NO arms and NO hands: none rendered, nothing at the shoulders`
- Explicit framing: `FRAMING: medium close-up throughout... no legs, no waist`
- **Camera target placed separately from the subject** so the head stays framed as the camera moves
- Named rig type: `CAMERA = robo-arm`, with start/end geometry and constant-speed constraints
- Explicit collision rules both directions: *"Nothing passes through the camera and the camera
  passes through nothing: no walls, no floor, no ceiling, no poles, no seats"*
- Performance instruction: *"his head continuously turns to follow the camera through the orbit"*
- Look negatives: `no motion blur smear, no film grain, no vignette, no lens flare, no readable text
  or logos, no neon, no yellow cast`

**The final prompt architecture (verbatim section headers)** — this is the reference-slot grammar
the whole system should reuse:
`SCENE CONTEXT` → `ACTIVE REFERENCES` (`<<<image_1>>>`, `<<<video_1>>>`) → `LOCATION MAP` →
`FIRST FRAME AND SPATIAL BLOCKING` (per-second frame maps, x/y % occupancy) → `FORMAT MODE` →
`OPTICS` → `CAMERA` → `THE PERFORMANCE` → `ACTION TIMING`.

Two details worth their own line:
- The reference declaration states the **exclusion** explicitly: *"Nothing else from the previz (its
  grey materials, proxy geometry or lighting) is inherited."*
- **Frame maps are given as percentages**: e.g. *"His hooded head at x 40–62%, y 18–70%"*. This is
  how spatial precision is communicated in text.

---

## S5 — "Higgsfield for Blender" plugin page (official)

- **URL:** <https://higgsfield.ai/plugins/blender> · **Confidence:** **A (primary)**
- **Proved:** the add-on exists for **Blender, After Effects, Premiere Pro, Photoshop, DaVinci
  Resolve and Figma**; the viewport prompt bar sits at the bottom of the 3D view with **tab selection,
  model selection, resolution and fps, and cost shown on the Generate button**; recent results appear
  above the viewport with the full library beneath, filterable by **3D / Images / Video**, with a
  folder shortcut to disk; **any result can be dropped straight into the scene — an image can land as
  a plane or wire into a material** from the result card. Advertised capability groups: **Scene
  Builder** (describe a set, get it assembled: objects, layout, light), **3D, Animation, Image,
  Video**.

---

## S6 — Higgsfield Genjutsu page (official)

- **URL:** <https://higgsfield.ai/genjutsu> · **Confidence:** **A (primary)**
- **Proved:** Genjutsu is *reality manipulation for video*. **Two techniques:**
  - **Motion Transfer** — *"Keep the motion and camera. Rebuild everything around them."* The motion,
    camera and timing stay the same; everything else is rebuilt from references.
  - **Object swap** — point edits: outfit, location, characters, objects.
- Worked examples on the page: move a fight into a pastel valley by the stream (location ref);
  replace a defender with a specific girl keeping her watch (character ref); recast both fighters
  *and* restage the fight (both refs) — *"every move and camera stays."*
- Marketing line that matches the pipeline's thesis: *"Total control, zero reshoots."*
- **MCP surface (verified by inspection in this workspace):** model id `hf_mult_motion_control`,
  provider Higgsfield, described as *"Transfer motion from a reference video to subjects in reference
  images."* Parameters: `resolution` ∈ {480p, 720p, 1080p}, default 720p. Media roles accepted:
  `image_references`, `video_references`. Aspect ratios: none (inherited from the driver).
- **Consequence for the pipeline [D — inference, but a strong one]:** a grey Blender/3D-Jutsu
  blockout MP4 is a valid `video_references` input, so the blockout can drive real characters and
  locations directly. L1 → L3 with no intermediate step.

---

## S7 — "Block Your Shot in Blender, Then Let AI Do The Rendering" (Gachoki Studios)

- **URL:** <https://gachoki.com/block-in-blender-finish-with-ai/> · **Updated:** 2026-09-07
- **Confidence:** **C (reported)** — third-party write-up, but dated and specific
- **Proved / added:**
  - **Version compatibility: the add-on "currently supports Blender 4.2 through 5.1."**
  - Add-on install by dragging the zip onto an open Blender window; it installs and enables itself.
  - The bridge makes Claude able to *"build and edit real, editable 3D geometry, not just spit out a
    static render."*
  - **Dialogue scenes** are the strongest case for blocking: six characters around a table, four
    cuts, 30 s of dialogue; with a blockout, *"six characters, zero seat swaps, and every line landing
    on the correct face."* Without it, characters visibly swap and the 180-degree rule breaks.
  - **Give camera direction as a shot list** — *"specific rails, targets, and cuts, the way you'd
    brief a real camera operator"* — not "make it cinematic".
  - **Deliberate imperfection:** *"a camera move that's too smooth can look artificial, so asking for
    subtle handheld sway adds weight and realism."*
  - **Blank-on-purpose scenes:** leave specific elements unmodelled in the blockout (liquid, complex
    effects) and let the AI fill them in at generation.
  - **The structural/style split, named explicitly:** a finished blocking file has a **structural
    layer** (cuts, camera moves, timing) and a **style layer** (what the world looks like). The same
    19-shot sequence regenerates as photoreal, then 2D-ink illustration, then stylised 3D toy *with
    every cut and every camera drift matching frame for frame.*
  - Higher-effort model tier + cowork mode measurably improved build efficiency.

---

## S8 — Higgsfield Academy / community / changelog

- **Academy:** <https://higgsfield.ai/academy> · **Community:** <https://higgsfield.ai/community> ·
  **Changelog:** <https://higgsfield.ai/creator-hub/changelog> · **Discord:** <https://discord.gg/higgsfield>
- **Confidence:** pending — coverage being assembled in
  `research/phase1_sources/community/higgsfield-3d-research.md`
- **Discord is not machine-reachable in this workspace** (requires an authenticated session). Any
  synthesis of Discord content must be explicitly marked as reported, never as read.

---

## Cross-source synthesis [D — our inference]

Three independent sources — an official tutorial, a motion-graphics editor, and a technical
reviewer — converge on the same architecture without coordinating:

1. **Solve space in 3D first.** Stated as cost doctrine (S1), as prompt doctrine (S2), and as
   continuity doctrine (S3, S7).
2. **The blockout is the *measurement*, not the picture.** Two sources independently describe
   handing the blockout to a model as a *motion reference* rather than as a look (S1, S3); the
   official guide formalises it as "the grey blockout becomes a reference clip."
3. **Separate structure from style.** S7 names it; S1 demonstrates it (same blocking, different L2
   assets per style); S4 builds it into the prompt grammar as `exclude_from_realisation`.
4. **Reuse is the economic engine.** S2 quantifies it (6–8 clips per environment); S7 generalises it
   (one blockout, many styles).
5. **Choreography belongs in the prompt, position belongs in the blockout** (S1, concert scene).

These five points are the load-bearing walls of the pipeline in
[`../00-overview/PIPELINE_ARCHITECTURE.md`](../00-overview/PIPELINE_ARCHITECTURE.md).
