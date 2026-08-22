# MiniMax H3 — Integration Plan

Status: **planning + API adapter landed, local ComfyUI path not started**
Owner: platform
Last updated: 2026-08-19

This plan covers adding MiniMax H3 as a selectable video generation model, over
two transports: the hosted MiniMax API (near-term) and a self-hosted ComfyUI
deployment (next major upgrade).

Sources reviewed:
- Prompt guides in the model repo — https://huggingface.co/MiniMaxAI/MiniMax-H3
  (`docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md`, `..._ref_en.md`)
- System overview, deployment recipes — https://github.com/MiniMax-AI/MiniMax-H3
- API reference — https://platform.minimax.io/docs/api-reference/video-generation-v2-create
- Product surface — https://hub.minimax.io/

---

## 1. Why bother — what H3 gives us that we don't have

Everything currently in the registry generates picture. H3 generates **picture
and 32 kHz stereo audio from one pass**, including spoken dialogue with matched
lip movement, ambience, and a score, all authored in the prompt.

That collapses three steps of the current pipeline into one for dialogue work:

| Today | With H3 |
|---|---|
| Generate still → animate → separately generate/lay voiceover → mix | One generation |
| Lip-sync via the Performance Anchor trick (`lip-sync-music-video` skill) | Native, prompt-controlled |
| Sound design sourced or licensed separately | Authored in `overall_soundscape` |

It is also the only model in the registry that can copy a **voice timbre** from
a reference clip, which matters for character continuity across a series.

What it does *not* do: long form. 15 seconds is the ceiling. Seedance 2.5
remains the model for anything longer or reference-heavy.

---

## 2. Capability envelope

| | |
|---|---|
| Duration | 4–15s |
| Frame rate | 24 fps |
| Resolution | 768P; 2K via H3-Regenerate-2K |
| Audio | 32 kHz stereo, native |
| Ratios | adaptive, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 |
| Dialogue languages | 11 with stable support |
| Ref2VA inputs | ≤ 9 images, ≤ 3 videos, ≤ 3 audio, ≤ 12 files total |
| Clip constraints | reference video/audio 2–15s each, ≤ 15s per type |
| Request size | ≤ 64 MB — use public URLs, not base64 |

**Mode exclusivity.** Keyframe roles (`first_frame` / `last_frame`) and
reference roles (`reference_image` / `reference_video` / `reference_audio`)
cannot appear in the same request. This is the single most likely source of
runtime 400s once the adapter is live, and it conflicts with how our pipeline
works today — see §6.

---

## 3. System shape (and the part that isn't open source)

H3 ships as three modules:

1. **H3-Context-IR** — hosted preprocessing. Takes free-form multimodal input
   and rewrites it into the structured representation H3-Base consumes. **Not
   open source.**
2. **H3-Base** — the generator. Open weights, two task-specific checkpoints:
   `FL2VA` (text / first / last / first+last frame) and `Ref2VA` (omni
   reference). 768p output. BF16.
3. **H3-Regenerate-2K** — in-context 2K regeneration, reusing the original
   multimodal context rather than conventional super-resolution. **Not open
   source.**

The practical consequence: **self-hosting gets you H3-Base only.** A local
deployment produces 768p and must supply its own Context-IR rewrite. MiniMax's
own guidance is to either call the hosted Context-IR API or follow their
prompting guidance and build the rewrite yourself.

We already have the second option: `skills/general/minimax-h3-director` **is**
our Context-IR substitute. It encodes the same output grammar the hosted service
emits. That makes the local path viable without a MiniMax dependency, at the
cost of 2K output.

---

## 4. Transport A — hosted API (landed, needs verification)

Single endpoint, task + poll.

```
POST {MINIMAX_BASE_URL}/v2/video_generation
Authorization: Bearer $MINIMAX_API_KEY
{
  "model": "MiniMax-H3",
  "content": [
    { "type": "text",      "text": "<Context-IR grammar prompt>" },
    { "type": "image_url", "url": "https://…", "role": "first_frame" }
  ],
  "resolution": "768P" | "2K",
  "duration": 4-15,
  "ratio": "adaptive" | "21:9" | "16:9" | "4:3" | "1:1" | "3:4" | "9:16"
}
→ { "task_id": "…" }
```

Poll the query endpoint until `status` is `succeeded` / `failed`
(`queued`, `running` in between; `cancelled` also terminal). The finished video
arrives as `task.content.url`.

Ratio rules that the adapter has to respect:
- **T2VA** (text only) — ratio is required and must be concrete; `adaptive` is
  rejected.
- **I2VA** (first/last frame present) — always resolves to `adaptive`; anything
  else is accepted but ignored.
- **Ref2VA** — optional, defaults to `adaptive`, concrete values allowed.

Requires the pay-as-you-go API tier.

**Landed:** `media_gen_service.animate_image_minimax_h3` + `_poll_minimax_task`,
registry entry `minimax-h3` (status `preview`), config keys `MINIMAX_API_KEY` /
`MINIMAX_BASE_URL`.

**Still to do before promoting to `available`:**
- [ ] Run a real generation end to end and confirm the polling URL shape
      (`GET /v2/video_generation/{task_id}`) against the live query docs.
- [ ] Confirm whether `content[].url` or `content[].image_url.url` is expected —
      the create-endpoint example only shows the text item in full.
- [ ] Decide the default resolution. 2K costs more and takes longer; 768P is
      probably right for pipeline runs with a 2K opt-in per job.
- [ ] Wire `callback_url` so long renders stop occupying a polling loop. The
      verification handshake echoes a `challenge` field within 3 seconds.
- [ ] Add H3 to `credit-calculator` so cost comparison stays honest.

## 5. Transport B — local ComfyUI (next major upgrade)

ComfyUI is a supported serving path, with official templates:
- Tutorial — https://docs.comfy.org/tutorials/video/minimax/minimax-h3
- Workflow templates — `video_minimax_h3_t2v.json`, `video_minimax_h3_r2v.json`
  in `Comfy-Org/workflow_templates`

Alternative serving stacks if ComfyUI proves awkward: SGLang (has a MiniMax-H3
cookbook and a `--model-variant fl2va|ref2va` flag), vLLM, or diffusers
(`ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-H3")`).

### Hardware reality check
H3-Omni-Transformer is 33B parameters dense, BF16. The SGLang example serves
with `--num-gpus 4 --ulysses-degree 4`. Roughly 13B of that sits in AdaLN
branches which do **not** need loading for inference-only, but this is still a
multi-GPU deployment, not a workstation card. Sparse attention — which is what
would make long sequences cheap — is not in the initial open-source release.

**This is the gating question for the local path.** Before writing any code:
size the hardware, or accept that "local" means a rented multi-GPU box rather
than an on-prem machine.

### Proposed shape

Add a `ComfyUIClient` service alongside the existing transports:

```
backend/app/services/comfyui_service.py
  submit_workflow(workflow_json, inputs)  -> prompt_id      POST /prompt
  poll(prompt_id)                         -> status/outputs GET  /history/{id}
  fetch_output(filename, subfolder)       -> bytes          GET  /view
```

Workflow templates live in `backend/resources/comfyui/` — one per mode
(`h3_t2v.json`, `h3_fl2v.json`, `h3_r2v.json`), checked in, with the node ids we
inject into recorded in a small manifest so a template update doesn't silently
break input wiring.

`media_gen_service` gains `animate_image_minimax_h3_local(...)` dispatched from
the existing `TRANSPORT_COMFYUI` branch, which currently returns a clear
"not wired up yet" error pointing at this document.

Two things a local deployment needs that the API gives for free:

1. **Context-IR.** Run `minimax-h3-director` over the scene brief to produce the
   structured prompt before submission. This is a Claude call in the existing
   prompt-building phase, not a new service.
2. **File hosting.** ComfyUI reads local paths; the pipeline holds Supabase URLs
   and base64 data URIs. Either mount a shared volume and stage inputs into it,
   or upload through ComfyUI's `/upload/image` endpoint. Prefer the volume — the
   SGLang docs make the same point about `file://` URIs being resolved by the
   *server* process, and the same trap applies to a containerised ComfyUI.

### Milestones
1. Hardware sizing decision (blocking).
2. `comfyui_service` with submit/poll/fetch against a stock ComfyUI.
3. Import and pin the two official H3 templates; add the FL2V variant.
4. Input staging (shared volume) + output ingestion into the existing scene
   cache.
5. Promote `minimax-h3-local` from `planned` to `preview`.
6. Side-by-side quality comparison against the hosted 768P output, since local
   has no 2K regeneration.

---

## 6. The pipeline conflict worth flagging early

Our production pipeline is image-first: generate a still, then animate it. That
maps to H3's I2VA mode, which is fine — until a scene also needs character
reference locking, which is Ref2VA, which **cannot include a first frame**.

Three options, in order of preference:

1. **Treat the generated still as a reference, not a keyframe.** Pass it with
   `role: reference_image` and say in the prompt that it establishes the opening
   composition. Loses exact first-frame fidelity; keeps character locking.
2. **Split by scene need.** Scenes with no extra references use I2VA (exact
   first frame); scenes with character/voice references use Ref2VA. The registry
   already carries per-model `modes`, so this is a routing decision.
3. **Skip the still entirely** for H3 scenes and go text-to-video, letting H3
   author the whole shot including audio. Cheapest, least controllable.

Recommend (2), with (1) as the fallback inside reference scenes. The adapter as
written already implements this: supplying `references` drops the image from the
keyframe slot rather than sending an invalid mixed request.

---

## 7. Licensing

H3 is released under the MiniMax H3 Community License Agreement, not a standard
OSI licence. Read it before shipping self-hosted output commercially:
https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE

Both the hosted API and self-hosted inference apply automated moderation to
submitted text, images and video, and to the rewritten prompts. Expect
occasional false positives on otherwise fine creative briefs, and surface the
rejection reason to the user rather than retrying blindly.

---

## 8. Open questions

- Does the Context-IR API's output justify its cost versus running
  `minimax-h3-director` locally? Worth an A/B on the same brief.
- Does 2K regeneration matter for our delivery formats, or is 768P + our
  existing upscaling service (`upscale_service.py`) good enough? If the latter,
  the local path loses its main disadvantage.
- Per-scene model mixing: is a video with some H3 shots and some Seedance shots
  acceptable, or does the audio discontinuity break it? H3 shots carry native
  audio; Seedance shots may not.
