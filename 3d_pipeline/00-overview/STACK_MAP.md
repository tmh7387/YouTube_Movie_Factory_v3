# STACK MAP — Tool Inventory, Tenancy Rules & Capability Matrix

**Version:** 1.0 · **Evidence base:** [`../20-reference/SOURCES.md`](../20-reference/SOURCES.md)

This document answers one question: *for this particular job, which tool is authoritative, and
what are its limits?* Read it before routing any work.

---

## 1. The three layers

The pipeline is three layers deep. Each layer has a different job, a different cost profile, and
a different failure mode. Confusing the layers is the most common and most expensive mistake.

| Layer | Job | Tools | Cost profile |
|---|---|---|---|
| **L1 — Structure** | Solve space, camera and time. Produces a *reference*, not a picture. | Blender (code-driven or add-on), 3D Jutsu | ~free locally · 50–100 cr/server side |
| **L2 — Identity & Look** | Produce the *assets* the final shot is built from: character, wardrobe, location, product. | Soul 2.0, Soul Cinema, Nano Banana, GPT Image 2, Cinema Studio Image | image-grade credits |
| **L3 — Realisation** | Turn L1's reference + L2's assets into finished frames, with motion and audio. | Seedance 2.5, Genjutsu, Cinema Studio, Seedance 2.0 | the expensive layer |

**Rule:** work L1 → L2 → L3, in that order, and never let an L3 model invent what L1 already
solved. This single sequencing rule is what the entire credit saving rests on.

---

## 2. Tool roster

### L1 — Structure

#### Blender (local, code-driven) — *authoritative for precision*
- **Role:** deterministic blockout. Camera paths, timeline, character stand-ins, set volumes,
  lettering/UI plates, previz renders.
- **Access:** `tools/blender-5.2.1-windows-x64/blender.exe --background --python <script>`
- **Why code rather than chat:** a blockout built by a script is *reproducible* — same spec in,
  same blockout out, every time. Chat-built blockouts are not. For a factory pipeline that must
  run unattended, that difference is decisive.
- **What it buys:** exact coordinates, exact focal lengths, exact frame numbers, versionable spec
  files, and a blockout library that can be re-rendered in a new visual style for free.
- **Limits:** no AI inference. It executes what the spec says. It is not a creative partner.
- **Install:** portable zip, no admin required. See
  [`../10-sops/SOP-01-pipeline-setup.md`](../10-sops/SOP-01-pipeline-setup.md).

#### Higgsfield Blender add-on (+ MCP bridge) — *authoritative for conversational building*
- **Role:** lets an AI agent (Claude / Astra) build and edit real, editable 3D geometry inside
  Blender over an MCP bridge; also exposes Higgsfield's own generation surface in the viewport.
- **Access:** download zip from <https://higgsfield.ai/plugins/blender>, drag onto an open Blender
  window. Copy the **bridge URL** from inside the add-on, then in Claude: Settings → Connectors →
  Add custom connector → paste bridge URL → name it → sign in.
- **Viewport surface (press N):** recent assets, Scene Builder models, and tabs for **3D /
  Animation / Image / Video**, with resolution, fps and cost shown on the Generate button.
  Camera tab exposes a **QR code that pairs a mobile device as a physical camera-move capture rig**.
- **Version compatibility:** reported as Blender **4.2 – 5.1**
  ([Gachoki, Sep 2026](https://gachoki.com/block-in-blender-finish-with-ai/)). Blender 5.2 is
  *outside* that window — hence both LTS builds are installed locally.
- **Status in this workspace:** bridge URL not yet captured → see open item in
  `../40-memory/MODEL_NOTES.md`.

#### 3D Jutsu (Higgsfield, browser) — *authoritative for speed and team access*
- **Role:** AI-native blocking and previz workspace. Prompt or reference image → editable 3D scene
  with objects, layout, lighting, cameras and animation → video, without leaving the chat.
- **Confirmed capability surface** ([Higgsfield 3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)):

  | Tool | What it does |
  |---|---|
  | Scene generation | prompt or reference → full scene as editable geometry |
  | Add object | primitives (sphere, cube, pyramid), lights (sun, point, spot), cameras |
  | Asset library | curated GLB assets + Mixamo characters drop into the active scene |
  | Scene properties | background colour, resolution, light intensity; full object hierarchy |
  | Animation | timeline with playhead; motion from camera trajectory, animated character, or GLB-with-animation |
  | Camera work | camera presets + trajectory editing; `Esc` exits camera view |
  | Revision history | every edit session saved as a revision; restore as new head |
  | Export | animated **MP4**, static frame, or **GLB** (dimensions + file size set before render) |

- **Parameters:** Model (LLM driving the agent — `Auto` is the free default; also GPT 6 Astra,
  Claude Fable 5.1, Claude Opus 5, GPT 5.6 Sol, GLM-5.3 Flash) · Duration **1–60 s** (default 15) ·
  Aspect **16:9, 9:16, 1:1, 4:3, 3:4, 21:9**.
- **Agent behaviour modes:** *generate without asking* (autonomous) · *ask before generating*
  (confirmation per generation) · separate *ask mode* that answers questions without touching the
  scene.
- **Computed on:** Higgfield "Supercomputer" — the LLM choice is a per-chat selector.
- **Collaboration:** share by email as admin / collaborator / viewer; team access from
  invited-only to anyone-with-link. Scenes persist under **My Scenes**.
- **Reference-video ingestion:** a reference video can be supplied and 3D Jutsu extracts the
  blocking and camera move from the footage — i.e. it can act as a *deconstructor*, not only a
  builder ([official tutorial](https://www.youtube.com/watch?v=vUYq38wC_xI), ch. 07:48).

### L2 — Identity & Look

| Tool | Use it for | Notes |
|---|---|---|
| **Soul 2.0 / Soul ID** | character identity + wardrobe carrier | train on a turnaround sheet; once trained, stop re-describing appearance in prompts |
| **Soul Cinema** | location plates | used in the official workflow for the desert-columns concert location |
| **Nano Banana 2 / Pro** | layout reference → cinematic interior | official workflow used it to turn a blockout opening frame into a finished location |
| **GPT Image 2** | typography, design, reference editing | see existing `core-gpt-image-2-prompt-guide-library.md` in `reference_documents/` |
| **Cinema Studio Image 2.5** | cinematic stills with element support | supports reference-element placeholders |

**Asset rule:** one asset, one job. A "character sheet" carries identity *and* wardrobe; a
"location plate" carries set *and* light; a "product reference" carries form *and* finish. Do not
ask one reference to carry two jobs — that is where drift enters.

### L3 — Realisation

| Tool | Best for | Reference grammar | Notes |
|---|---|---|---|
| **Seedance 2.5** | finished cinematic shots, narrative coverage | image refs only in practice (the previz video is moderation-rejected) | 4–30 s; 480p ~2.5 cr/s, 720p ~6.5 cr/s. **Set `mode: "omni_reference"` or every reference call fails.** **Obeys a text-encoded camera composition** — the working route for narrative work |
| **Genjutsu** (`hf_mult_motion_control`) | **recasting** a shot that already exists | 1 video ref + image refs; accepts the blockout video | two techniques: **Motion Transfer** and **Object Swap**. **Transfers motion and timing but NOT composition** — it ignores the blockout's camera target. Measured 98.46 cr for 15 s at 720p |
| **Seedance 2.0 / 2.0 mini** | Performance Anchor method — identity + audio continuity | image + video + audio refs simultaneously | std 1080p/4K; mini 720p cap |
| **Cinema Studio 4.0** | alternate front-end for the same reference+prompt handoff | asset import + prompt paste, `@`-reference objects | used interchangeably with Seedance 2.5 in the askNK workflow |

### The finding that re-routed the pipeline

The pipeline was designed around one inference: because Genjutsu performs Motion Transfer, a grey
Blender blockout should drive real characters and locations **and lock the camera path**. The first
half is true. The second half is **false**, and it was only settled by spending credits.

| | Genjutsu | Seedance 2.5 |
|---|---|---|
| Accepts the blockout video | **yes** | **no** — `nsfw`, and no prompt wording changes it |
| Reproduces motion & timing | yes, smoothly | n/a (no video accepted) |
| **Holds the specified composition** | **no** — subject left frame at the mid-shot beat | **yes** — framing matched the spec at every beat checked |
| Cost, 15 s @ 720p | 98.46 cr (measured) | ~97 cr |

**Consequence:** the two models accept different reference packs, so **the reference pack cannot be
model-agnostic**. For narrative shots the route is Seedance 2.5 with image references only and the
camera path written into the prompt in the house grammar — which `make_prompt.py` generates from
`shot.json`. That gives up per-frame camera fidelity and gains compliance.

Full isolation matrix and evidence in [`../40-memory/MODEL_NOTES.md`](../40-memory/MODEL_NOTES.md).

---

## 3. Tenancy rules — who owns the truth

When two sources disagree, resolve by this precedence. Higher wins.

| # | Authority | Example |
|---|---|---|
| 1 | **Observed behaviour in this workspace, logged in `MODEL_NOTES.md`** | re-checked credit cost on our account |
| 2 | **Higgsfield primary documentation** (help centre, changelog, official blog) | documented duration cap |
| 3 | **Official Higgsfield video tutorials** | the workflow as demonstrated |
| 4 | **Reputable third-party write-ups / tutorials**, dated | version compatibility windows |
| 5 | **This knowledge base's own summaries** | the routing tables above |

Never let #5 override #1. `MODEL_NOTES.md` exists precisely to correct these documents.

---

## 4. Capability matrix — what each tool *cannot* do

The limits matter more than the features.

| Claim | Reality | Consequence |
|---|---|---|
| "The agent builds it for you" | In the conversational route, the agent is *non-deterministic*. Same prompt, different blockout. | Converge the *spec*, then build from code, when repeatability matters. |
| "Add-on works on Blender 5.2" | Reported support is **4.2–5.1** | Run the add-on on the 4.5.9 LTS build; keep 5.2.1 for code-driven work. |
| "Genjutsu will generate your shot" | It **requires a driving video**. It recasts; it does not originate. | You must own a blockout or a plate first. |
| "Long shots are easy" | Seedance 2.5 caps at **30 s**, Genjutsu inherits the driver's length. | Anything longer is built as sequences, or extended via video_extension. |
| "The blockout is just reference" | The blockout is a **permanent, style-agnostic asset** | Same 19-shot blockout regenerates as photoreal, 2D-ink, or stylised-toy with frame-for-frame matching cuts. Archive it. |
| "3D previz is free" | Local code-driven previz is ~free; **server-side 3D generation costs 50–100 cr** | Route planning-heavy work to Blender; route speed-critical work to 3D Jutsu. |
| "You don't need Blender skills" | True for *operating* the conversational route. **Not** true for judging a blockout. | The craft being protected is cinematography, not software. |

---

## 5. Environment as verified in this workspace

Machine readings, current session. These are facts about *this* machine, not documentation.

| Item | Value | How verified |
|---|---|---|
| Blender 5.2.1 LTS | `tools/blender-5.2.1-windows-x64/blender.exe` | `--version` → `Blender 5.2.1 LTS`, build 2026-08-25 |
| Blender 4.5.9 LTS | `tools/blender-4.5.9-windows-x64/blender.exe` | `--version` → `Blender 4.5.9 LTS` |
| Headless render engine | `BLENDER_EEVEE` default; Cycles requires enablement | `--background` probe of `RenderSettings.engine` |
| Headless MP4 mux | `MPEG4` / `MKV` / `WEBM` / `AVI` / `QUICKTIME` containers available | probe of `FFmpegSettings.format` |
| Bundled Python | 3.13.13 | probe `sys.version` |
| ffmpeg / ffprobe | on PATH (`WinGet\Links`) | `Get-Command` |
| yt-dlp | `%APPDATA%\Python\Python312\Scripts\yt-dlp.exe` | `Get-Command` |
| Higgsfield MCP | connected · plan `ultra` · balance read live via `balance` | MCP tool call |
| Higgsfield credit balance | **2,214.87** (at knowledge-base authoring) | `mcp__higgsfield__balance` |

**Credit balance is a production input, not trivia.** It belongs in the project log and it gates
how many variants a shot may have.

---

## 6. Model routing quick table

| Need | Route | Why |
|---|---|---|
| Lock camera path, timing, occupancy | **Blender (code)** or **3D Jutsu** | L1 |
| Continuous take through geometry the model would break | **Blender blockout → Genjutsu Motion Transfer** | motion comes from geometry, not from a guess |
| Show a client a different look, same edit | **same blockout → Seedance 2.5, different style refs** | structural layer is style-agnostic |
| Character-driven performance with dialogue/music | **Seedance 2.0/2.0 mini Performance Anchor** | native multi-reference incl. audio |
| Location established shot, no performance | **Soul Cinema plate → Seedance 2.5** | cheap L2 asset, no identity needed |
| Recast an existing real video into a new world | **Genjutsu Motion Transfer** with the real video as driver | purpose-built |
| Single object/wardrobe swap on an otherwise good take | **Genjutsu Object Swap** | point edit, keeps everything else |
| Crowd / formation-heavy scene | **Blender blockout (boxes for bodies, distinct shape for lead) → Seedance 2.5 with choreography in prompt** | model keeps movement fluid; blocking only positions |
| Shot longer than 30 s | sequence of ≤30 s shots, or `video_extension` | hard cap |

---

## 7. Open items blocking full verification

| Item | Why it matters | Owner |
|---|---|---|
| **Blender add-on bridge URL not captured** | the conversational Blender route is the official front door; unverified here | needs Higgsfield UI sign-in |
| **Add-on behaviour on Blender 5.2.1** | compatibility window says 4.2–5.1; is 5.2 actually broken? | test once bridge is captured |
| **3D Jutsu exact credit costs** | community figure is 50–100 cr/env; needs our-account confirmation | measure on first 3D Jutsu scene |
| **Genjutsu cost per motion transfer** | L3 routing is cost-blind until this is measured | measure on first transfer |
| **Soul 2.0 vs Soul ID training cost** | affects L2 budget per project | measure on first character |
| **Discord access** | ~200k-member community; not reachable without an authenticated session | user action or Community web surface |
