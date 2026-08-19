---
title: Seedance 2.5 (Dreamina)
type: tool
domain: [ai-video]
tags: [seedance, bytedance, byteplus, video-generation, #current]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes], [YT_GenAIwithKeera_1min_AI_Film_2_Prompts]]
---

# Seedance 2.5 (Dreamina)

ByteDance's video generation model, served through BytePlus ModelArk as
`dreamina-seedance-2-5-260628`, and resold through platforms including
Higgsfield and CometAPI.

## What changed from 2.0

| | 2.0 | 2.5 |
|---|---|---|
| Timestamps | ignored — shot numbers only | integer-second timestamps honoured |
| Max duration | ~15s | 30s |
| Reference assets | a handful | up to 50 (≤30 images, ≤10 videos, ≤10 audio) |
| Aspect ratios | six fixed | any ratio in [0.4, 2.5] |
| Multi-view subject refs | discouraged | supported |
| Editing / extension | — | instruction editing, forward/backward extension |
| Output | up to 4K | 1080p at time of the videos above |

Positioned by BytePlus as a production-workflow upgrade rather than a
generational leap — the 2.0→2.5 step is smaller than 1.5→2.0.

## Capabilities beyond straight generation

3D clay-model reference (render a grey-box animatic into finished style),
multi-panel storyboard reference, strict keyframe reference, instruction-based
video editing, video extension, seamless transition between two clips, and
one-click assembly from a set of stills.

## Practical notes from the field

- Strict copyright moderation on reference images — see
  [[BP_Working_Around_Model_Content_Filters]].
- Locked-parameter rules: editing pins both ratio and duration; first-frame and
  extension tasks pin ratio. Get these wrong and the request is rejected.
- Background music can appear uninvited; front-loading a negative audio
  instruction is the suggested fix — see [[Technique_Prompt_Top_Loading]].
- Pricing observed via Higgsfield: ~250 credits per generation at ~$0.04/credit,
  with an unlimited-but-serialised promo available at the time.

## In this platform

Registry id `dreamina-seedance-2-5`, transport BytePlus ModelArk. See
`docs/VIDEO_MODEL_SELECTION.md` and
`skills/general/seedance2-director-v2/references/seedance2-5-capabilities.md`.

## Related Pages

- [[Technique_Extend_Video_Continuation]]
- [[Technique_Prompt_Top_Loading]]
- [[BP_Anti_Plastic_Realism]]
