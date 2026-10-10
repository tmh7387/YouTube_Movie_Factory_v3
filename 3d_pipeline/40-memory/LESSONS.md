# LESSONS.md — Accumulated 3D Pipeline Wisdom

**Lives at:** `3d_pipeline/40-memory/LESSONS.md`
**Format per entry:** date · project · what happened · root cause · rule extracted
**Discipline:** newest at top. Keep entries under ~120 words. When a lesson holds across 2+ projects,
promote it to [`PATTERNS.md`](PATTERNS.md) and mark it `[PROMOTED]` here.

A lesson that cannot be turned into a rule is not yet understood. Rewrite it until it can.

---

## 2026-09-13 — demo-infinite-loop (L3 realisation, first paid run)

**What happened:** the full L1→L3 handoff was executed for the first time, then the failures were
diagnosed to root cause. Three results, and the diagnosis matters more than the first take did.

1. **The blockout drove real characters and locations.** A grey Blender previz, handed to Genjutsu
   Motion Transfer with a character plate and a location plate, produced a genuinely
   production-grade shot with correct identity, wardrobe and set — for **98.46 credits**, measured.
2. **Genjutsu lost the framing.** At the blockout's medium close-up beat, the generated shot had the
   camera on the background wall with the subject half out of frame. The frame-matched loop did not
   survive either.
3. **Seedance 2.5 refused the blockout video entirely** with `nsfw`, and **no prompt wording changed
   that** — a bare video reference with a prompt that explicitly disclaimed people and text failed
   identically to the full production prompt. The same file passed Genjutsu without objection.

**Root cause, established by isolation rather than inference:** Genjutsu transfers **motion and
timing**; it does not transfer **composition** — it re-frames to its own judgement and ignores the
blockout's camera target, which is the one instruction this pipeline calls its most transferable
trick. Separately, Seedance's classifier rejects the flat-shaded previz artefact itself, and that is
a property of the file, not of our prompt.

**Rules extracted:**
1. **Route on fidelity, not price.** Genjutsu at 98.46 credits and Seedance 2.5 at ~98 credits cost
   the same. Genjutsu is for shots whose value *is* the movement (recasting, object swaps,
   motion-driven sequences). Narrative coverage needs a model that honours framing.
2. **Match the route to what the model actually accepts.** A blockout video is a valid reference for
   Genjutsu and an instant rejection for Seedance. The pipeline's reference pack cannot be
   model-agnostic; the manifest must be built per route.
3. **Prompt wording cannot fix a classifier.** When a reference is rejected, change the *input*, not
   the prose. Two rounds of prompt rewriting were wasted before the isolation test made this obvious.
   Test the reference alone first — it costs one cheap run and settles the question.
4. **480p is one third the price of 720p** (2.5 vs 6.5 cr/s, measured). Calibration takes at 480p are
   the cheapest insurance in the pipeline.
5. **Measurement must gate the first spend, not follow it.** The blockout was verified to 0.00% loop
   seam error and still did not survive realisation. **Verification of the free layer says nothing
   about the paid layer.** Budget one calibration take per route per project, and score it before
   designing the remaining shots around that route.
6. **Reference slot order decides identity.** With two character plates in the pack, the
   *first-uploaded* one won and the generated man wore the wrong wardrobe.

---

## 2026-09-13 — Phase 1 knowledge-base construction (pre-production baseline)

**What happened:** Reconnaissance of the Astra → Higgsfield → Blender / 3D Jutsu stack found the
capability documented across official and third-party sources, but nothing in this repository
encoded it. There was an established memory pattern for the music-video domain
(`.agent/music-video-director/memory/`) and nothing equivalent for 3D, so every 3D project would
have re-derived its method from scratch and repeated its mistakes.

**Root cause:** no domain knowledge base, and therefore no feedback loop. Knowledge lived in
tutorials rather than in the repository. The pipeline had skills for *prompting* models but no
doctrine for *solving space in 3D first*, which is the step the sources agree carries the value.

**Rules extracted:**
1. **Block in 3D before spending a generation credit.** Independently reached by every source
   reviewed. The blockout is a *measurement* of the shot; a prose prompt is a *guess* at it.
2. **Position belongs in the blockout; choreography belongs in the prompt.** Animating a dance in
   the blockout produces a dance that looks like a blockout.
3. **The structural layer of a blockout is style-agnostic capital.** One blockout, many visual
   styles, frame-for-frame matching. Archive blockouts as assets, never as scratch.
4. **Environments are capital; shots are consumables.** One environment yields 6–8 clips. Group
   shots by location before generating anything.
5. **Documentation is a cache; measurement is the evidence.** Every platform limit and cost in this
   knowledge base is tagged with a confidence level, and `MODEL_NOTES.md` overrides all of it when
   observed behaviour disagrees.
6. **A project that does not write its wrap-up produced no institutional value.**

**Open risks logged at the same time:** the Blender add-on's reported support window (4.2–5.1)
excludes the Blender build installed here (5.2.1) — both LTS builds are therefore installed; the
add-on's bridge URL has not yet been captured, so the conversational Blender route is documented
but unverified in this workspace; and no 3D Jutsu or Genjutsu credit cost has been measured on this
account, so the L3 budget model is currently based on third-party figures only.

---

<!-- Template for new entries — copy this block to the top of the list:

## YYYY-MM-DD — <project slug> (<stage>)
**What happened:** <observable outcome>
**Root cause:** <the actual cause, not the symptom>
**Rules extracted:** <numbered, actionable, testable>
-->
