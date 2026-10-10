# SOP-04 — Generation, Selection & Delivery

**Stage:** S8–S10 · **Cost:** the expensive stage · **Prerequisite:** Gate 3 passed
**Output:** selected takes, cost log, updated memory

> Everything before this SOP is free or cheap. **This is where money is spent.** The SOP
> exists to make the spending bounded, measured and explainable.

---

## 0. The budget law, restated

`cost(shot) ≈ cost(L1) + cost(L2) + n × cost(L3)`

The pipeline exists to drive `n` toward **2**. If `n` is climbing, stop and return to Stage
Gate 2 — the fault is upstream, and generating more takes will not fix it.

**Before spending, run the routing decision in §1.** The models are not interchangeable and
the price difference between the right and wrong route is routinely 5–10×.

---

## 1. Route selection

| Situation | Route | Why |
|---|---|---|
| A blockout exists and the shot must keep its exact motion | **Genjutsu — Motion Transfer** | motion and timing come from the geometric driver. **But see the framing warning below.** |
| A real video exists and one element must change | **Genjutsu — Object Swap** | point edit; keeps everything else untouched |
| Narrative coverage where the subject must hold position in frame | **Seedance 2.5, image references only, camera described in the prompt** | Seedance obeys the described composition; Genjutsu does not. **Do not pass the previz video — see below.** |
| Character performance with dialogue or music | **Seedance 2.0 / 2.0 mini** — Performance Anchor | accepts image + video + audio references simultaneously |
| Location or establishing shot with no performance | Soul Cinema plate → **Seedance 2.5** | no identity needed, cheap L2 asset |
| Same blockout, second visual style | **Seedance 2.5** with swapped L2 assets | the whole economic argument for keeping blockouts |
| Shot longer than 30 s | a sequence of ≤30 s shots, or `video_extension` | hard platform cap |

### ⚠ The two limits that decide the route — both measured on our account

**1. Genjutsu transfers motion and timing but NOT composition.** Given our blockout it applied the
camera arc smoothly and produced a production-grade image, but at the beat where the blockout is a
medium close-up of the subject it had the camera on the background wall with the subject half out of
frame. **It ignores the blockout's camera target** — the very instruction this pipeline calls its
most transferable trick. A frame-matched loop did not survive either. Use Genjutsu when the
*movement itself* is the shot's value; do not use it expecting a camera-path lock.

**2. Seedance 2.5 rejects a `build_blockout.py` previz video as `nsfw`.** Isolated by testing: a
bare video reference fails even with a prompt that explicitly disclaims people and text, so
**prompt wording is not a mitigation**. Genjutsu accepts the identical file. Full isolation matrix
in [`MODEL_NOTES.md`](../40-memory/MODEL_NOTES.md).

**Therefore the working route for narrative work is: Seedance 2.5 with image references only, and
the camera path written into the prompt in the house grammar** — which `make_prompt.py` generates
directly from `shot.json`. You give up per-frame camera fidelity relative to a video reference and
gain composition the model actually honours.

### Cost measured on our account

| Route | Resolution | Rate | 15 s cost |
|---|---|---|---|
| Seedance 2.5 | 480p | **2.5 cr/s** | **37.5 credits** (measured) |
| Seedance 2.5 | 720p | ~6.5 cr/s | ~97 credits |
| Genjutsu | 720p | ~6.6 cr/s | **98.46 credits** (measured) |

**480p costs one third of 720p.** That makes the calibration protocol in §2 genuinely cheap — run it
before committing a project to a route.

**Verified limits to respect:**
- **Seedance 2.5**: 4–30 s, 720p max for delivery, modes `t2v` / `omni_reference` / `video_edit` /
  `video_extension`. **`mode` defaults to `t2v`, which rejects ALL references — set
  `mode: "omni_reference"` explicitly or every reference call fails with a 422.**
- **Genjutsu**: 1 driving video of 4–30 s, up to 30 reference images, output ≤1080p. No
  aspect-ratio parameter — **the output inherits the driver's aspect**, so the blockout must
  be rendered at the delivery aspect.
- **Seedance 2.0**: std to 1080p/4K; mini capped at 720p.

---

## 2. Budget the shot before generating

Write the expected cost down **before** you spend, then reconcile after. An unforecast cost
cannot be managed, and cross-project comparison needs the forecast to be wrong *visibly*.

```
Shot: <SHOT_ID>
Route: <model>
Expected unit cost: <credits/sec × duration × variants>
Expected total: <credits>
Balance before: <credits>
Stop-loss: if total spend on this shot exceeds <2× expected>, halt and re-enter at Gate 2.
```

**Record `balance before` from the live MCP balance tool.** It is the only ground truth.

---

## 3. Generate a variant pair

Generate **two** takes: same prompt, different seed. Not one (no comparison), not five (no
discipline).

Why a pair rather than a single take: a single take gives you *a* result, not a *judgement*.
Seeing two versions of the same intent is what tells you which failures are prompt problems
and which are model variance — and that distinction is what makes the next shot cheaper.

**Reference pack assembly before you press generate:**
- `references.json` slot order must match the prompt's `<<<image_N>>>` / `<<<video_N>>>` order.
  Getting this wrong silently swaps identity and location.
- Feed the **clean** previz, never the annotated one. Burn-in text leaks into the render.
- Verify the driver's aspect matches the shot's aspect (Genjutsu inherits it).

---

## 4. Score the takes against the spec, not against taste

| Criterion | /5 | What to look for |
|---|---|---|
| **Camera fidelity** | | does the camera do what `shot.json` says, at the right times? |
| **Timing / beats** | | does each beat land on its frame? |
| **Identity hold** | | does the character stay the same person throughout? where did drift start? |
| **Spatial continuity** | | any occupancy break, any 180° violation, anything passing through anything? |
| **Artifacts** | | count and type — morphing, extra limbs, text, flicker |
| **Audio correctness** | | if applicable: does the track match the direction? |

**A rejected take with a reason is worth more than an accepted take without one.** The reason
is the product of the money you just spent; write it down while the take is in front of you.

---

## 5. Salvage before regenerating

Before spending on a fresh generation, check whether the take can be repaired. This is where
Genjutsu earns its place.

| Defect | Salvage route |
|---|---|
| Camera and motion are right, wardrobe/location wrong | **Object Swap** |
| One element wrong, everything else right | **Object Swap** |
| Good take, wrong aspect | **reframe** / outpaint |
| Good take, needs more resolution | **upscale** (ByteDance preset, or Topaz) |
| Right shot, wrong style throughout | re-run Seedance with the same blockout, different L2 assets |
| Right except for a single beat | recut the blockout for that beat, regenerate only that segment, extend |

**Rule:** a salvage costs a fraction of a regeneration and preserves everything that already
worked. Exhaust salvage before regenerate.

---

## 6. Cost accounting

Log against the shot, not the project. Per-shot cost is the only number that supports
comparison across shots and projects.

```
Shot: <SHOT_ID>
L1 structure      : <credits>  (local render ~0; 3D Jutsu = agent turns + export)
L2 identity/look  : <credits>
L3 realisation    : <credits>   (<model>, <duration>s, <n> takes)
Salvage           : <credits>
Finishing         : <credits>
TOTAL             : <credits>
Expected vs actual: <Δ>   → if > 2×, this is a LESSONS entry
Balance after     : <credits>
```

---

## 7. Delivery

- **Upscale** only if the delivery spec requires it. Know the target before spending on it.
- **Grade** to the project look — the model's colour is a starting point, not a finish.
- **Conform** against the audio; verify beat alignment rather than assuming it.
- **Archive** the selected take *with its prompt, spec and reference pack*, so the shot can be
  re-derived. A take without its inputs is an orphan.

---

## 8. Gate 4 — picture lock

- [ ] Every shot selects a take that was scored against its spec
- [ ] Every rejected take has a recorded reason
- [ ] Takes per shot average ≤ 2 (or the exception is documented)
- [ ] Cost log complete and reconciled against the live balance
- [ ] Selected takes archived with their inputs
- [ ] Any platform behaviour that contradicted documentation is logged in `MODEL_NOTES.md`

---

## 9. Wrap-up (mandatory)

Write `40-memory/PROJECT_LOG/<slug>.md` from
[`_TEMPLATE.md`](../40-memory/PROJECT_LOG/_TEMPLATE.md). Then distil:

- a **lesson** for anything that went wrong or surprisingly right → `LESSONS.md`
- a **pattern** if it held on a second project → `PATTERNS.md`
- a **platform fact** for anything measured → `MODEL_NOTES.md`
- a **library asset** for any environment or blockout worth reusing → `library/`

**A project without a wrap-up did not produce institutional value.** It produced a video.

---

## 10. Anti-patterns at this stage

| Anti-pattern | Cost | Correction |
|---|---|---|
| Generating variants until one looks right | unbounded | variant pair, then decide |
| Skipping the score and judging by feel | taste becomes unauditable, mistakes recur | score against the spec |
| Regenerating what Genjutsu could salvage | 3–10× per shot | check salvage first |
| Feeding the annotated previz | leaked burn-in text, full regeneration | clean previz only |
| Regenerating the environment per shot | the single largest avoidable cost | environments are capital |
| Not recording the balance | cost model based on guesswork forever | read it at start and end |
