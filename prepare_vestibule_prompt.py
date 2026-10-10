from pathlib import Path
import shutil,json
p=Path('C:/Users/Admin/Dropbox/YTMF/Amara_2026/Press_On/Clip_Package_v2/02_VERSE1/seg17_vestibule_performance')
archive=p/'previous_drafts/before_approved_baseline_adaptation';archive.mkdir(parents=True,exist_ok=True)
for n in ['prompt.md','prompt_ui.txt']:
 if not (archive/n).exists():shutil.copy2(p/n,archive/n)
baseline=(p.parents[1]/'LIP_SYNC_APPROVED_BASELINE.md').read_text(encoding='utf-8')
section1=baseline.split('SECTION 2')[0].replace('train corridor','train vestibule').replace('corridor lighting','vestibule lighting')
prompt=section1+'''SECTION 2 — Setup
@[Amara_Houston_2](1acc7f87-dfe9-4e2c-a6db-dcc48b5d2651) Amara stands inside the vestibule of @[Train_vestibule_Amara_outfit.](ec2e51e5-6d86-49e9-8f04-9a144d6ce222), facing camera. The handbag hangs from her right hand at thigh height, below frame. Her left hand stays low. Her feet remain planted.
SECTION 3 — Action (5s)
Amara sings directly to camera throughout the entire shot — her mouth is always forming the lyrics. She remains standing while singing.
00.0s–01.7s: Singing "Left my heavy heart," she holds eye contact with the lens. On "heart," her chin lifts slightly while her mouth holds the recorded vowel.
01.7s–03.6s: Singing "with every heavy thing," she lowers her shoulders slightly. On "thing," her eyebrows lift briefly, then settle. Her head stays facing camera.
03.6s–05.0s: She follows the recorded vowel release, breath and pickup into "Departure" in @[Audio 1](audio_1), maintaining eye contact through the final frame.
SECTION 4 — Camera
Medium close-up, eye level, frontal — framed from mid-chest to above her hair, Amara center-frame.
The camera holds still for the whole shot. Focal length, camera-to-face distance and face position in frame hold constant. Vestibule verticals stay upright. Face and mouth always clear and sharp.
SECTION 5 — SFX / Physical Detail
Her shoulders rise and fall slightly with sung breaths. The handbag stays low in her right hand. The train and vestibule stay stationary.
SECTION 6 — Vocal / Lyric / Lip-Sync
Vocal / lyric / lip-sync: "Left my heavy heart with every heavy thing"; continue the recorded pickup into "Departure" at the end of the excerpt.
Amara is singing, not speaking — all mouth shapes carry rhythmic energy and melodic phrasing.
Lip-sync must match @[Audio 1](audio_1) exactly — every syllable, consonant hit, vowel opening, breath attack, jaw pressure and vocal emphasis.
On "Left" — tongue tip rises behind the upper teeth on L, jaw opens into EH; upper teeth touch the lower lip on F, then release into the recorded T. "my" — FULL BILABIAL CLOSURE, lips press completely shut on M, visible lip contact, then open into the held MY vowel. "heavy" — open EH, upper teeth touch the lower lip on V, then release into EE. "heart" — jaw opens into the sustained vowel, releasing with the recording. "with" — lips round forward on W, then open; tongue tip approaches the teeth on TH. "every" — jaw opens into EH; upper teeth touch the lower lip on V before releasing into the final vowel. Repeat the recorded mouth shapes for the second "heavy." "thing" — tongue tip visible between the teeth on TH, then retracts into the sustained IH vowel, ending with NG. Follow the recorded opening of "Departure" through the final frame.
Avoid AI smoothing; preserve raw skin texture and realistic micro-movements.
SECTION 7 — Constraints
ONE CONTINUOUS SHOT ONLY. NO CUTS EVER. The singer's face and mouth must remain visible and in sharp focus throughout the entire shot. Prioritize flawless lip-sync and continuous singing performance above all — her mouth must be visibly forming lyrics at every moment. Body movements must flow WITH the singing, never replacing it.
'''
for n in ['prompt.md','prompt_ui.txt']: (p/n).write_text(prompt,encoding='utf-8')
(p/'NEXT_TAKE_REVIEW.md').write_text('''# PO-V05-017 — vestibule singing review

Lyric: Left my heavy heart with every heavy thing.

Proposed reference: @Train_vestibule_Amara_outfit. (ec2e51e5-6d86-49e9-8f04-9a144d6ce222), the successful non-upscaled replacement used for the corridor. Proposed framing: stationary frontal eye-level medium close-up, hands below frame. This image/setup awaits shot-specific review under the user instruction to review images before generation.

WAV verified 5.000 seconds, 44.1 kHz source audio. MP4 container, video and audio streams verified 5.000 seconds, 120 video frames. No audio re-export performed. Source range 24.833333–29.833333; edit in/out 0.2–4.166667. Existing five-second package retained. Future 48 kHz normalization is not needed to change the measured duration.

Phrase intervals are machine-estimated, checked against canonical lyrics; automatic transcription misheard Left as That's. Canonical lyric retained. End contains a partial pickup into Departure, retained for trimming in the edit. No independent listening verification claimed.

Target settings: Seedance 2.5, 5 seconds, 16:9, 1080p, audio on. No video submitted during preparation.

Full adapted prompt: [prompt.md](prompt.md).
''',encoding='utf-8')
print(prompt)
