# MODEL_NOTES.md — Platform Reliability Log

Lives at: YouTube_Movie_Factory_v3/.agent/music-video-director/memory/
This file OVERRIDES the default routing table in the skill when evidence
accumulates. Newest findings at the top of each section.

## Seedance 2.0 (Higgsfield MCP)
- 2026-08-14 [VERIFIED]: std mode supports 1080p/4K; fast mode 480/720p only.
  Accepts image_references + video_references + audio_references
  simultaneously — the Performance Anchor method runs natively.
- (populate: reference limits hit in practice, timestamp-timeline vs
  labeled-shot success rate, SFX tag overuse symptoms)

## Seedance 2.0 Mini (Higgsfield MCP)
- 2026-08-14 [VERIFIED]: same reference roles as 2.0 including
  audio_references, 720p cap. Correct budget tier for identity/audio work.
- (populate: quality delta vs 2.0 fast at same resolution)

## Seedance 2.5 (Higgsfield MCP)
- 2026-08-14 [VERIFIED]: 4–30s, modes t2v / omni_reference / video_edit /
  video_extension. 720p max. video_edit is billed by reference video length.
- (populate: extension seam quality, edit-mode fidelity)

## MiniMax Hailuo (Higgsfield MCP)
- 2026-08-14 [VERIFIED]: 2.3 generation, NOT H3. Start/end frame only, no
  audio input, no multi-reference. 6s or 10s only. Route only pure-physics
  B-roll here.
- H3 (editing mode, native audio, 9-image cap) = MiniMax direct platform
  only. Revisit if Higgsfield adds it.

## Higgsfield Lipsync Studio
- 2026-08-14 [VERIFIED]: not exposed via MCP (no model, no app). Web UI only.
  MCP lip-sync path = Performance Anchor on seedance_2_0.

## Higgsfield Soul ID / Character Reference Sheets
- Tier 1 (3-panel front/back/face) is the fast default for Soul ID training,
  per Higgsfield Academy's Blockbuster 4K and Santiago Cinematic courses.
- Soul ID training wants the 3-panel sheet PLUS 20+ reference generations at
  varied angles/lighting — the 3-panel alone is a turnaround, not the set.
- Once trained, stop re-describing appearance in prompts.
- Watch: profile-heavy characters may need Tier 2 (adds 3/4 turn + hands) —
  log here if Tier 1 alone proves insufficient.

## Higgsfield Terms of Service / Account Notes
- Training-on-content is default-on (§4.4 as of Aug 2026) — confirm opt-out
  status per project before commercial delivery. ToS changed in July 2026;
  recheck periodically.
- 2026-08-14: account on Ultra plan, ~6,430 credits.
