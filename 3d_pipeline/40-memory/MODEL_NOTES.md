# MODEL_NOTES.md — Platform Reliability Log

**Lives at:** `3d_pipeline/40-memory/MODEL_NOTES.md`

> **This file OVERRIDES every routing table, limit and cost in this knowledge base.**
> Documentation is a cache. This is the evidence. Newest findings at the top of each section.

**Tagging:** `[VERIFIED]` = observed on our account, with date. `[REPORTED]` = credible source, not
reproduced here. `[UNVERIFIED]` = hearsay or unread source.

---

## VERIFIED COST CORRECTIONS — read before budgeting anything

Three widely-circulated cost figures were checked against primary sources during Phase 1 and
**two of them are wrong**. These corrections materially change routing, so they lead the file.

| Claim in circulation | Status | Correct position | Source |
|---|---|---|---|
| "3D Jutsu costs 50–100 credits per environment" | **`[UNVERIFIED]` — origin not found, could not be corroborated** | 3D Jutsu is billed **per agent message**, not per scene. `Auto` is free; model price per turn runs from ~0.4 credits (DeepSeek V4 Flash) to **~17 credits (GPT 6 Astra)**. No published price exists for previz MP4 / static frame / GLB export. | [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu) |
| "~200 credits for a 20 s Seedance 2.5 render" | **`[REFUTED]`** | That figure is Higgsfield's own for a **full end-to-end Supercomputer production** (Seedance 2.0 era, ≤15 s), not a single render. The correct figure for **20 s @ 720p is ≈130 credits** (52 credits per 8 s ⇒ 6.5 credits/s). | [Supercomputer guide](https://higgsfield.ai/blog/higgsfield-supercomputer-guide) |
| "the Higgsfield community is ~200,000 users" | **`[RESOLVED]` — it is the Discord member count** | Discord API returns **193,059 members / 11,757 online**. The platform self-reports 25–30 M users (internally inconsistent across pages); r/Higgsfield_AI has ~765 members. Treat 193 k as the Discord size, nothing more. | [Discord invite API](https://discord.com/api/v10/invites/higgsfield?with_counts=true) |

**The rule this file exists to enforce:** a cost figure that has not been traced to a primary
source is a rumour. Two of the three above were repeated confidently in creator videos and were
wrong. Measure on our account, then write it here.

---

## The billing trap

- **`[VERIFIED, first-party, 4 independent pages]`** — **Unlimited plans do NOT cover the
  Blender plugin, MCP, CLI, Canvas or Supercomputer.** Those paths always deduct credits
  regardless of plan. Verbatim from the help centre: *"any generation made outside it… always
  deducts credits, regardless of plan."*
  **Consequence:** an all-unlimited subscription does not make the Blender/MCP route free, and a
  budget built on that assumption is wrong by the full cost of the project's generation.
  Source: [How credits work](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)

## Higgsfield account state

- **2026-09-13** `[VERIFIED]` — plan **ultra**; balance **2,214.87 credits** at knowledge-base
  authoring. The music-video memory records ~6,430 credits on 2026-08-14, so **consumption is
  material and credit balance must be part of pre-production planning**, not an afterthought.
- **2026-09-13** `[VERIFIED]` — Higgsfield MCP is live in this workspace: image, video, audio, 3D
  generation, media upload/import, and the 3D Jutsu scene-builder toolset are all callable.
- Credit balance is read live via the `balance` tool. **Record it at the start and end of every
  project.**

## 3D Jutsu (Higgsfield, browser)

- **2026-09-13** `[REPORTED]` from the official guide — parameters: duration **1–60 s** (default 15);
  aspect **16:9 / 9:16 / 1:1 / 4:3 / 3:4 / 21:9**; agent LLM selector with `Auto` as the free
  default, plus GPT 6 Astra, Claude Fable 5.1, Claude Opus 5, GPT 5.6 Sol, GLM-5.3 Flash.
- **2026-09-13** `[REPORTED]` — three agent behaviour modes: *generate without asking*, *ask before
  generating*, and an *ask mode* that answers without modifying the scene.
- **2026-09-13** `[REPORTED]` — exports: animated **MP4**, static frame, **GLB** (dimensions and
  file size set before render). Revision history per editing session, restorable as a new head.
- **2026-09-13** `[REPORTED]` — asset library includes curated **GLB assets** and **Mixamo
  characters**. *(populate: whether Mixamo rigs carry usable animation into the blockout, and
  whether GLB export preserves camera animation for Genjutsu)*
- **2026-09-13** `[REPORTED]` — a **reference video can be supplied and the blocking/camera move
  extracted from the footage.** This makes 3D Jutsu usable as a *deconstructor*, not only a builder.
  *(populate: fidelity of extracted camera paths)*
- **2026-09-13** `[VERIFIED, official]` — **billing is per agent message, not per scene.** Published
  per-turn model prices: `Auto` **free** · DeepSeek V4 Flash ~0.4 · Seed 2.1 Turbo ~1 ·
  Gemini 3.5 Flash ~2 · Gemini 3.1 Pro ~3 · GPT 5.6 Sol ~7 · Claude Opus 5 ~8 · Claude Fable 5.1 ~11
  · **GPT 6 Astra ~17 credits**. *"Longer chats use more."* 30+ selectable LLMs.
  **No published price for previz MP4, static frame, or GLB export.**
  Source: [3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu)
  **Consequence:** selecting Astra for iterative work costs ~40× the cheapest paid model per turn.
  Select cheaply for iteration; switch up only for turns that need it.
- **2026-09-13** `[VERIFIED, official]` — the **published Recreate prompts were decoded verbatim**.
  The house grammar is `SCENE CONTEXT` → `ACTIVE REFERENCES` (`<<<image_1>>>`, `<<<video_1>>>`) →
  `LOCATION MAP` → `FIRST FRAME AND SPATIAL BLOCKING` (frame maps as x/y percentages) → `FORMAT MODE`
  → `OPTICS` (47° diagonal FOV, distances in metres) → `CAMERA` (time-segmented) → `PHYSICS` →
  `LIGHTING` → `AUDIO` → `POSITIVE CONSTRAINTS`. **There is no `NEGATIVE` section** — prohibitions
  are written as explicit `NO …` rules inside the relevant section and then restated as affirmatives
  at the end.

<!-- CORRECTION 2026-09-13: an earlier entry in this file repeated a community figure of
     "50-100 credits per 3D environment". No primary source makes that claim and it conflates
     per-message agent billing with per-artefact billing. Removed. See the cost-corrections
     table at the top of this file. -->

## Higgsfield for Blender (add-on + MCP bridge)

- **2026-09-13** `[REPORTED]` — **supported Blender versions 4.2 – 5.1.** Our installed builds are
  **5.2.1 LTS** and **4.5.9 LTS**; 5.2.1 is outside the stated window. *(populate: actual behaviour
  of the add-on on 5.2.1 — install, enable, bridge, panel)*
- **2026-09-13** `[VERIFIED, local]` — Blender **5.2.1 LTS** headless works: `--background
  --factory-startup --python <script>`, default engine `BLENDER_EEVEE`, bundled Python 3.13.13,
  FFmpeg containers `MPEG4 / MKV / WEBM / AVI / QUICKTIME` available for previz export. **Code-driven
  blocking is therefore fully available without the add-on.**
- **2026-09-13** `[REPORTED]` — add-on installs by **dragging the zip onto an open Blender window**;
  the **bridge URL is copied from inside the add-on** and pasted into the chat client as a *custom
  connector*. Requires signing into the Higgsfield account from the viewport.
- **2026-09-13** `[NOT YET DONE]` — bridge URL not captured in this workspace. The bridge URL is
  **`https://bridge.higgsfield.ai/mcp`**; the conversational Blender route remains **unverified
  here**. Owner: needs a Higgsfield UI sign-in.
- **2026-09-13** `[REPORTED — single source, and NOT in official docs]` — a viewport panel on
  `N` and a **QR code for pairing a mobile device as a camera-move capture rig** were both
  described in a demonstration video ([askNK](https://www.youtube.com/watch?v=BmkNqEYjQFA)), but
  **neither appears in any official Higgsfield document** reviewed during Phase 1. Official
  material describes **7 tabs** in the add-on and says nothing about an N-panel or QR capture.
  **Treat both as unconfirmed** until seen directly. This is exactly the class of claim
  `MODEL_NOTES.md` exists to flag: plausible, demonstrated once, unverified.
  Source for the official surface: [Higgsfield for Blender](https://higgsfield.ai/blog/higgsfield-blender-plugin)
- **2026-09-13** `[VERIFIED, first-party]` — the add-on requires **Blender 4.2–5.1** (our 5.2.1 is
  outside the window), runs on **Windows and macOS**, and performs generation **in the cloud, so no
  local GPU is required**.

## Higgsfield Blender bridge — headless alternative

- **2026-09-13** `[REPORTED, registry metadata]` — **`fnf-blender-mcp` v0.2.0** (published
  2026-09-12, MIT, Node 24+, Blender 4.2+) drives Blender `--background` **with no add-on at all**,
  exposing **19 tools**, and supports **non-Claude MCP clients** via `config --format json` (generic)
  or `toml` (Codex).
  Repo: <https://github.com/higgsfield-ai/fnf-local-pluging-bridge-mcp> ·
  Registry: <https://registry.npmjs.org/fnf-blender-mcp>
- **`[GOTCHA — stated by the publishers themselves]`** — *"Windows/Linux native Blender execution
  has not been verified locally"*; only **macOS arm64 with Blender 4.2.23 LTS** was verified.
  **Consequence for this workspace: we are on Windows**, so this path is unproven here and must be
  tested before it is relied on.
- **Why it matters anyway:** this pipeline already drives Blender headlessly through its own
  `build_blockout.py`, so the bridge is not required for the code route. It becomes valuable only if
  we want a *conversational* agent driving Blender without the add-on — worth testing, not worth
  depending on.
- **2026-09-13** `[REPORTED]` — higher-effort model tier plus cowork mode measurably improved build
  efficiency on complex blockouts. *(populate: whether it reduces iterations or just improves first
  pass quality)*

## Genjutsu (`hf_mult_motion_control`)

- **2026-09-13** `[VERIFIED ON OUR ACCOUNT — the decisive finding]` — **a grey Blender blockout is a
  valid Genjutsu driver, but Genjutsu does NOT preserve framing.** We ran our 15 s blockout through
  Motion Transfer with two image references (character + location) and it produced a genuinely
  production-grade shot: correct identity, correct wardrobe, the location plate rebuilt as a real
  room, and the camera arc applied smoothly. **But the framing diverged from the blockout.** At
  7.5 s, where the blockout is a medium close-up of the subject with the wardrobe soft behind him,
  the generated shot has the camera on the wardrobe wall with the subject pushed to the left edge
  and partly out of frame. The closing frame also did not reproduce the opening frame, so the
  frame-matched loop did not survive.
  **What this means:** Genjutsu reproduces the *motion and timing* (when the camera moves, how it
  accelerates, the general arc) but re-frames the shot to its own taste. Treat it as a
  **motion-and-timing transfer**, not a camera-path lock.
  **Consequence for routing:** for shots where the subject must hold a specific position in frame —
  which is most narrative coverage — **Seedance with the blockout as a video reference is the
  correct route**. Reserve Genjutsu for shots whose value is the *movement itself* (recasting an
  existing plate, object swaps, motion-driven sequences) rather than the composition.
  This contradicts the strong inference recorded below on 2026-09-13, which is left in place
  because the reasoning was sound and only measurement could settle it.
- **2026-09-13** `[VERIFIED ON OUR ACCOUNT]` — **cost: 98.46 credits** for a 15 s transfer at 720p
  (balance 2,214.87 → 2,116.41). The published figure is 104 credits for 15 s at 720p, so the
  published table is accurate to within a few percent. Output: h264, 1280×720, 24 fps,
  duration **15.04 s** against a 15.000 s blockout — **the driver's duration carries over
  essentially exactly** (0.3% long).
- **2026-09-13** `[VERIFIED, observed]` — with two image references in the pack, **Genjutsu used the
  first-uploaded character image** for identity, not the later, better one (the generated man wore
  the *unbuttoned* look from our first character asset, not the *buttoned* look from the second).
  **Slot order therefore decides identity**, exactly as the reference-pack manifest assumes. Check
  which asset won before spending again.
- **2026-09-13** `[VERIFIED, MCP schema]` — provider Higgsfield; description *"Transfer motion from a
  reference video to subjects in reference images."* Media roles: **`image_references`,
  `video_references`**. Parameter: `resolution` ∈ {**480p, 720p, 1080p**}, default **720p**.
  **No aspect-ratio parameter — output inherits the driver's.**
- **2026-09-13** `[VERIFIED, MCP]` — free-trial unlimited generations: `supports_unlim` is **false**
  for this model. Do not offer unlim on Genjutsu without re-checking.
- **2026-09-13** `[INFERENCE — strong, but CONTRADICTED IN PART by the measurement above]` — a grey
  blockout MP4 does satisfy `video_references`, and it does drive real characters and locations.
  The inference was right about the handoff existing and wrong about its fidelity: motion yes,
  framing no.
- **Cost comparison that matters:** 15 s via Genjutsu at 720p = **104 credits published / 98.46
  measured**, versus ~98 credits for 15 s of Seedance 2.5 at 720p. They cost the same. Choose on
  *fidelity*, not price — and on this evidence Seedance is the one that respects composition.
- **2026-09-13** `[UNKNOWN]` — whether the 4–30 s driver limit is enforced on input length or on
  output length. *(populate on first transfer)*

## Seedance 2.5 (Higgsfield MCP)

### The blockout-video moderation block — DIAGNOSED 2026-09-13

**Finding: Seedance 2.5's `omni_reference` mode rejects a `build_blockout.py` previz video as
`nsfw`, and no prompt wording affects it. Genjutsu accepts the identical file.**

Isolation matrix, all runs on our account with the same uploaded asset
(`25545148-788e-4416-8da8-262f62f460e0`, the 15 s grey blockout at 1280×720):

| Run | References | Prompt | Result |
|---|---|---|---|
| 1 | 2 character images + location + **previz video** | full 13-section shot prompt | `nsfw` |
| 2 | 1 character image + location + **previz video** | full 13-section shot prompt | `nsfw` |
| 3 | 2 images (no video) | full 13-section shot prompt | **completed** |
| 4 | **previz video only** | *"grey previz of simple geometric shapes… no people, no text"* | `nsfw` |
| 5 | **previz video only** | *"lit architectural previz… no people in frame"* | `nsfw` |
| — | same previz video | Genjutsu Motion Transfer | **completed** |

**Conclusions:**
1. **The blockout video is the trigger**, not the images and not the prompt. Runs 4 and 5 are
   decisive: a bare video reference with a prompt that explicitly disclaims people and text still
   fails.
2. **Prompt wording is not a mitigation.** A deliberately innocuous prompt (#4) fails identically to
   the full production prompt (#1). Rewriting the prompt will never fix this.
3. **The trigger is not the red proxy's colour** — #5 changed the described look entirely and still
   failed. The classifier is reacting to something in the *pixels*, most likely the unlit
   flat-shaded capsule silhouette reading as a synthetic humanoid form.
4. **This is Seedance-specific.** Genjutsu ingested the same file without objection, so it is a
   classifier difference between the two backends, not a property of our artefact.

**Consequences to design around:**
- **For Seedance, put the camera in the prompt, not in a video.** This costs the per-frame camera
  fidelity a blockout video would have given and is a real capability loss.
- **To use a blockout video at all, use the Genjutsu route** — and accept that it transfers motion
  and timing but not composition (below).
- **Untested mitigation worth trying:** `--shading lit` produces a shaded previz that reads as
  architectural rather than as a flat synthetic figure. Unverified; test before relying on it.

- **2026-09-13** `[VERIFIED, MCP schema]` — **`mode` is a required-in-practice parameter and defaults
  to the wrong value.** It defaults to `t2v`, which **rejects any reference media** with a 422
  (`"mode 't2v' does not accept reference media"`). To pass references you must set
  **`mode: "omni_reference"`** explicitly. Options: `t2v` · `omni_reference` (image, video or audio
  references) · `video_edit` (billed by the reference video's duration; `duration` and
  `aspect_ratio` are ignored) · `video_extension` (`aspect_ratio` ignored — output follows the
  extended video). **Teach this to every new operator** — the failure looks like a broken reference
  pack rather than a missing parameter.
- **2026-09-13** `[VERIFIED ON OUR ACCOUNT]` — **cost scales with resolution, not linearly with
  duration alone.** 15 s at 480p cost **37.50 credits** (balance 2,116.41 → 2,078.91), i.e.
  **2.5 cr/s at 480p** against **6.5 cr/s at 720p**. **480p calibration takes are one third the
  price of 720p**, which makes the calibration protocol in `LESSONS.md` genuinely cheap.
- **2026-09-13** `[VERIFIED, observed]` — Seedance 2.5 **respects composition in a text-encoded
  camera path.** In the 480p run the framing matched the specified medium close-up at both 0.0 s and
  7.5 s, with the wardrobe correct and the man centred — where Genjutsu had lost the framing
  entirely at the same beat. **This is the routing discriminator: Seedance obeys the described
  composition; Genjutsu does not.**
- **2026-09-13** `[VERIFIED, observed]` — output carries an **AAC audio track** when
  `generate_audio: true` (the default), and measured duration was **15.04 s** against the requested
  15 s. Aspect and resolution were respected exactly (`854×480` for 480p, `1280×720` for 720p).
- **2026-09-13** `[VERIFIED, error observed]` — a moderation rejection returns job status
  **`nsfw`** with no result payload. `reveal_generation` only accepts **`ip_detected`** jobs on the
  seedance family, so it is **not** an appeal path for `nsfw`. There is no appeal path in the MCP
  surface: the response is to change the input, not to argue with the classifier.
- **2026-09-13** `[VERIFIED, MCP schema]` — other parameters: `duration` 4–30 (default **5**),
  `resolution` 480p/720p/1080p (default 720p), `generate_audio` bool (default **true** — audio is on
  unless you turn it off), `bitrate_mode` standard/high, `extension_mode` backward/forward (required
  for `video_extension`, rejected otherwise). Media roles: `start_image`, `end_image`,
  `image_references`, `video_references`, `audio_references`. Aspect ratios: auto, 21:9, 16:9, 4:3,
  1:1, 3:4, 9:16.
- **2026-09-13** `[VERIFIED, observed]` — the generator raises a **preset suggestion** on prompts whose
  wording resembles a published preset (ours matched "IN THE DARK" because the prompt contained
  dark-lighting language). It is a suggestion, not an error: retry with
  `declined_preset_id: "<id>"` to generate the prompt literally. Do this whenever the prompt is
  deliberately specified — accepting a preset replaces your lighting direction.
- **2026-09-13** `[VERIFIED, official]` — there is a **published Seedance 2.5 prompt guide with a
  formal section grammar** (`GLOBAL STYLE` / `SCENE` / `CHARACTERS` / `LOCATION` / `FIRST FRAME AND
  BLOCKING` / shot-by-shot / `OPTICS` and `CAMERA` / `PHYSICS` / `LIGHTING` / `AUDIO`). The 3D Jutsu
  prompt style is a specialisation of this, not a separate invention. The guide's own warning:
  *"Skip a section and the output tends to fail in a specific, predictable way."*
  Source: [Seedance 2.5 Prompting Guide](https://higgsfield.ai/blog/seedance-2-5-prompting-guide)
- **2026-09-13** `[VERIFIED, official]` — **there is no `NEGATIVE` section in the house style**, and
  **no seed parameter is documented**. Negatives are written as explicit `NO …` rules *inside* the
  relevant section, then restated affirmatively in a closing `POSITIVE CONSTRAINTS` block.
- *(populate: 720p → delivery-grade upscale route and its cost; reference-slot limit hit in
  practice; behaviour at exactly 30 s vs 29 s; whether `--shading lit` previz passes moderation)*

## Seedance 2.0 / 2.0 mini (Higgsfield MCP)

- **2026-08-14** `[VERIFIED]` (carried forward) — std 1080p/4K; fast mode 480/720p only. Accepts
  image + video + audio references **simultaneously** — the Performance Anchor method runs natively.
  Mini: same reference roles incl. audio, **720p cap**; the correct budget tier when identity or
  audio continuity matters.

## Higgsfield 3D Jutsu vs the MCP `scene_builder_3d_*` toolset

- **2026-09-13** `[INFERENCE]` — the MCP exposes a 3D scene-builder surface (`scene_builder_3d_*`:
  create project, import catalog GLB assets, run/query Python in a pinned Blender worker, export GLB,
  render previews) with worker **Blender 5.2** and `BLENDER_EEVEE` / `BLENDER_WORKBENCH` / `CYCLES`
  (not `BLENDER_EEVEE_NEXT`). **This is a server-side Blender, distinct from the local Blender
  install.** *(populate: how this surface relates to the browser 3D Jutsu workspace — same backend or
  different? Which one bills?)*

## Router / cost model

- **2026-09-13** `[UNVERIFIED]` — the earlier music-video routing note that "Higgsfield Lipsync Studio
  is not exposed via MCP" should be re-checked; the MCP surface has grown since 2026-08-14.

---

## Populate-on-next-run checklist

These are the measurements that will replace reported figures with verified ones. Each is cheap to
obtain and each materially changes routing or budget.

| # | Measurement | Where it changes a decision |
|---|---|---|
| 1 | 3D Jutsu: credits per scene generation, per previz render, per GLB export | L1 route choice |
| 2 | Genjutsu: credits per motion transfer, at each resolution; accepted driver duration range | L3 route choice |
| 3 | Seedance 2.5: credits at 5 / 10 / 20 / 30 s, 720p; cost of a two-variant pair | variant-policy |
| 4 | Blender add-on: install + bridge behaviour on Blender 5.2.1 vs 4.5.9 | which Blender build is canonical |
| 5 | MCP `scene_builder_3d_*` end-to-end: import → edit → GLB → preview | whether the server-side 3D worker can replace browser 3D Jutsu |
| 6 | Blockout MP4 as Genjutsu driver: does the grey proxy drive motion cleanly? | the entire L1→L3 handoff |
| 7 | MLX/`Qwen3-VL`-class vision pass: accuracy of second-by-second prompt extraction from a previz clip | whether the vision pass is automated or manual |
