from pathlib import Path
import shutil
root=Path('C:/Users/Admin/Dropbox/YTMF/Amara_2026/Press_On/Clip_Package_v2')
clip=root/'02_VERSE1/seg20_coat_on_corridor_performance'
prompt='''SECTION 1 — Film DNA + Performance Anchor
Consistent style guideline for all shots on Arri Alexa 65, Panavision C Series Anamorphic, T2.8; realistic cinematic footage @[Video 1](video_1) in a warm walnut and brass train corridor at blue hour, the train stationary; dominant warm amber, walnut brown and brass palette; soft practical corridor lighting with cool window spill camera-left; subtle organic film grain; 24fps motion cadence; 180-degree shutter; blockbuster production value. Music and lyrics to lip-sync exactly @[Audio 1](audio_1)
SECTION 2 — Setup
@[Amara_Houston_2](1acc7f87-dfe9-4e2c-a6db-dcc48b5d2651) Amara stands on the corridor axis of @[Train_vestibule_Amara_outfit.](ec2e51e5-6d86-49e9-8f04-9a144d6ce222), facing camera. The handbag hangs from her right hand at thigh height, on screen-left. Her left hand stays low. Corridor verticals run behind her.
SECTION 3 — Action (5s)
Amara sings directly to camera throughout the entire shot — her mouth is always forming the lyrics. She walks forward while singing.
00.0s–01.0s: Singing "But the woman," she steps forward on the beat and raises both eyebrows, then lowers them. Eyes locked on camera. 01.0s–03.0s: Singing "getting on this train," she continues stepping forward. Chin level, head facing camera. 03.0s–05.0s: Singing "has never been this grown," she lifts her chin slightly on "never." On "grown," her cheeks and mouth corners lift into a knowing half-smile. She keeps walking to the final frame.
SECTION 4 — Camera
Medium shot, eye level, frontal — wide enough to include the handbag at thigh height, Amara center-frame.
The camera tracks backward at her walking speed for the whole shot. Focal length, camera-to-face distance and face position in frame hold constant. Corridor verticals stay upright. Face and mouth always clear and sharp.
SECTION 5 — SFX / Physical Detail
Her coat hem and sleeves move with each step. The handbag swings in a short arc from her wrist. Her shoulders rise and fall with her steps. Brass fittings catch small highlights as she passes. The train and corridor stay stationary.
SECTION 6 — Vocal / Lyric / Lip-Sync
Vocal / lyric / lip-sync: "But the woman getting on this train has never been this grown"
Amara is singing, not speaking — all mouth shapes carry rhythmic energy and melodic phrasing. The line is a quiet claim, certain and unhurried.
Lip-sync must match @[Audio 1](audio_1) exactly — every syllable, consonant hit, vowel opening, breath attack, jaw pressure and vocal emphasis.
On "But" — FULL BILABIAL CLOSURE, lips press completely shut on the B, visible lip contact, then release into a short UH. "the" — tongue tip visible between the teeth on TH. "woman" — lips round forward on the WO, then a second BILABIAL CLOSURE on the M. "getting" — hard G at the back of the throat, two crisp T taps. "this train" — TH tongue tip visible, then a sharp TR onset. "never" — N with tongue to the roof, open EH. "been" — BILABIAL CLOSURE on the B, sustained EE with wide lateral lip stretch, closing N. "grown" — GR onset, lips round forward and hold on the OWN, closing N.
Avoid AI smoothing; preserve raw skin texture and realistic micro-movements.
SECTION 7 — Constraints
ONE CONTINUOUS SHOT ONLY. NO CUTS EVER. The singer's face and mouth must remain visible and in sharp focus throughout the entire shot. Prioritize flawless lip-sync and continuous singing performance above all — her mouth must be visibly forming lyrics at every moment. The walk must flow WITH the singing, never replacing it.
'''
archive=clip/'previous_drafts/before_user_validated_standard_20260912'
archive.mkdir(parents=True,exist_ok=True)
for file in [clip/'prompt.md',clip/'prompt_ui.txt',root/'SINGING_PROMPT_SOP.md']:
    if not (archive/file.name).exists(): shutil.copy2(file,archive/file.name)
for file in [root/'LIP_SYNC_APPROVED_BASELINE.md',clip/'prompt.md',clip/'prompt_ui.txt']: file.write_text(prompt,encoding='utf-8')
sop=root/'SINGING_PROMPT_SOP.md'
old=sop.read_text(encoding='utf-8')
audio=old.split('## Audio preparation — matched whole-second durations')[1].split('## Prompt structure')[0]
text='''# Press On — singing prompt SOP v1.3

Effective 2026-09-12. The authoritative standard is [LIP_SYNC_APPROVED_BASELINE.md](LIP_SYNC_APPROVED_BASELINE.md), supplied and approved by the user after a successful Seedance 2.5 run. Preserve its wording for this shot. Element-name Markdown escapes have been normalized to literal underscores. This standard supersedes conflicting v1.2 prompt rules, archived with the previous clip prompt.

## Mandatory prompt pattern

Preserve the seven sections and demonstrated language. Adapt only shot-specific references, setting, lyrics, duration, actions and camera. Do not invent a replacement framework or add a reference inventory to Section 1.

1. Film DNA + Performance Anchor: retain the demonstrated camera, lens, style, bound Video 1 and Audio 1 pattern. Scene-specific palette and lighting are allowed as demonstrated.
2. Setup: establish the performer using native locked Elements, position, orientation and hand continuity. Avoid invented appearance descriptions.
3. Action: primary lip-sync driver. State continuous direct-to-camera singing and lyric formation. Include timestamped exact sung phrases covering the full duration, with observable expression and motion cues. Movement supports singing. Preserve this approved example's 0–1, 1–3 and 3–5 second intervals; future shots use intervals appropriate to their recordings. Do not silently replace approved timings with ASR estimates.
4. Camera: specify framing, eye level/orientation, movement and stable sharp face/mouth visibility.
5. SFX / Physical Detail: concise clothing, prop and environment movement. Ordinary nouns for already established coat and handbag are permitted; do not force repeated Element mentions into every sentence.
6. Vocal / Lyric / Lip-Sync: primary lip-sync driver. Include full exact lyrics, singing versus speaking, rhythmic/melodic delivery, exact bound Audio 1 matching, and lyric-specific consonant closures/releases, vowel shapes/holds, breaths, jaw and emphasis. Preserve this successful example verbatim. For new lyrics, adapt articulation cues to the actual words; do not copy unrelated phonemes.
7. Constraints: preserve continuous shot, visible sharp face/mouth and continuous singing priorities. Walking supports the vocal performance.

The approved example takes precedence over earlier blanket restrictions on negatives, repeated lyrics, emotional phrasing and descriptive Section 1 text. Do not edit out its successful instructions to satisfy those older rules. Each prompt remains standalone, uses actual bound references and keeps asset inventories outside the prompt. Image approval and final prompt/settings review before authorized generation remain in force. Seedance 2.5 remains the singing model.

## Current corridor reference and incident record

Use @Train_vestibule_Amara_outfit. (ec2e51e5-6d86-49e9-8f04-9a144d6ce222), as supplied in the successful prompt. Identity remains @Amara_Houston_2 (1acc7f87-dfe9-4e2c-a6db-dcc48b5d2651). Platform_outfit-Sheet remains retired.

The user confirmed the upscaled corridor image caused the failure and reports success after replacing it and slightly adjusting the prompt. Previous master: 10,880 × 6,144 pixels, 97,522,808 bytes. Preserve it for archival/finishing use; use the replacement Element for generation. This incident does not establish a universal Seedance 2.5 upload limit. Completed Element processing did not guarantee generation acceptance.

The replacement source file/media ID and successful render ID have not yet been captured locally. Older scene_ref.png and draft manifests are historical inputs, not evidence of the successful replacement. Reconcile those before loading a new generation. No generation was submitted while saving this standard. Success is user-reported; independent render inspection is not claimed.

## Audio preparation — matched whole-second durations
'''+audio+'''
## Review and learning

Verify actual native references, approved images, equal whole-second WAV/MP4/action/render durations and model/settings before submission. Preserve exact successful prompt snapshots. Record input media IDs, render ID and user assessment when available. Check current official model requirements when constraints change; distinguish documented requirements from project observations.

## Change log

- v1.3: Locked the user-tested successful prompt, particularly Sections 3 and 6; adopted replacement corridor Element; recorded upscaled-image failure. Retained matched whole-second audio preparation. Previous SOP archived.
'''
sop.write_text(text,encoding='utf-8')
assert (root/'LIP_SYNC_APPROVED_BASELINE.md').read_text(encoding='utf-8')==(clip/'prompt.md').read_text(encoding='utf-8')==(clip/'prompt_ui.txt').read_text(encoding='utf-8')
print('Saved and verified identical baseline and active prompt copies; updated SOP v1.3; archived prior versions.')
