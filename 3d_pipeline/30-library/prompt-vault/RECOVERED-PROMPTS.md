# RECOVERED-PROMPTS — Prompts Reconstructed From Primary Sources

**Purpose:** these are not invented templates. Each is a prompt or prompt fragment **recovered from a
primary Higgsfield source**, preserved with its provenance so it can be studied, adapted and
A/B-tested. Written prompts are the highest-value artefacts in this domain because they encode
hard-won platform behaviour.

**Rules for this file**
1. Never paraphrase a recovered prompt when its *wording* is the point — reproduce it verbatim.
2. Always record the source and whether it is verbatim / reconstructed from speech.
3. Speech-derived prompts (from a tutorial's audio) are marked **[RECONSTRUCTED]** — the gist is
   reliable, the exact wording is not.
4. A prompt here is evidence, not gospel. If it fails on our account, patch it and log the change in
   [`../../40-memory/MODEL_NOTES.md`](../../40-memory/MODEL_NOTES.md).

---

## P1 — Official 3D Jutsu blockout prompt (grey-proxy previz)

**Source:** [Higgsfield, 3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu), Step 1
**Type:** **VERBATIM** — published in full by Higgsfield
**Target:** 3D Jutsu agent (blockout stage)
**Why it is the single most valuable prompt we have:** it encodes the entire house style for
directing a 3D scene agent — explicit negatives, separate camera target, named rig, bidirectional
collision rules, performance direction and look negatives, all in one pass.

```
8 seconds, 16:9. A character stands in a subway car and raps. The character has NO arms and NO
hands: none rendered, nothing at the shoulders.

FRAMING: medium close-up throughout: head, shoulders and upper torso only, no legs, no waist. An
invisible camera target is placed separately from the head so the head is always in frame as the
camera moves.

CAMERA = robo-arm. One continuous, perfectly smooth 360-degree orbit around the character's head and
shoulders at chest height, with a slight upward angle: starting front-left, sweeping around behind,
continuing around the far side and returning to the front. Constant unhurried speed, near-constant
radius that closes slightly on the back half. The camera never stops, never reverses, never zooms,
and stays inside the subway car. Nothing passes through the camera and the camera passes through
nothing: no walls, no floor, no ceiling, no poles, no seats.

CHARACTER: keeps rapping the whole time, and his head continuously turns to follow the camera through
the orbit, face toward the lens the whole way, including a look over the shoulder as the camera
passes behind.

Clean sharp digital image, no motion blur smear, no film grain, no vignette, no lens flare, no
readable text or logos in the car, no neon, no yellow cast.
```

**Anatomy — extract these moves into every blockout prompt:**

| Move | Instance | Why it works |
|---|---|---|
| Hard negative in caps | `NO arms and NO hands: none rendered` | removes ambiguity a model would otherwise resolve by adding the thing |
| Explicit framing with exclusions | `no legs, no waist` | prevents the model widening the shot to "help" |
| **Decoupled camera target** | *"an invisible camera target is placed separately from the head"* | the single most transferable trick — framing survives the camera move |
| Named rig | `CAMERA = robo-arm` | a named rig imports a whole movement grammar in two words |
| Bidirectional collision | *"nothing passes through the camera and the camera passes through nothing"* | catches both occlusion failures in one line |
| Performance continuity | *"keeps rapping the whole time"* | tells the agent the subject is *active*, not posed |
| Look negatives as a tail | no grain/vignette/flare/neon/yellow cast | stops the model decorating |

---

## P2 — Official reference-slot **final** prompt architecture

**Source:** [Higgsfield, 3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu), Step 4
**Type:** **VERBATIM structure, abridged content** — the published prompt is ~1,500 words; the
section skeleton and the load-bearing sentences are reproduced exactly.
**Target:** Seedance 2.5 / Genjutsu-style video generation
**This is the house grammar.** Every final prompt we write should use these section headers in this
order.

```
SCENE CONTEXT
  <one dense paragraph: format, duration, subject, what the camera does, the mood.
   Ends with the exclusivity line: "His rap is the only voice.">

ACTIVE REFERENCES
  <<<image_1>>>: THE RAPPER. <identity, age, distinguishing features, then wardrobe
                enumerated item by item>
                "His face and full layered outfit stay identical for the whole shot;
                 the hood stays up. Closely matches the reference."
  <<<video_1>>>: THE CAMERA PATH AND THE FIGURE'S BEHAVIOUR. Reference controls two things:
                (1) the camera move: <describe the move in the same words as the previz prompt>
                (2) the figure's behavior: <describe the body/head rules>
                "Nothing else from the previz (its grey materials, proxy geometry or
                 lighting) is inherited."

LOCATION MAP
  <the set described as a real place, with materials, and an explicit occupancy statement:
   "The car is EMPTY except him.">

FIRST FRAME AND SPATIAL BLOCKING
  "The first visible frame is already the tight head-and-shoulders on his face; no establishing wide."
  Frame map at 0.0s: <subject occupancy as x%/y%>; <what else is in frame and where>
  Frame map at 2.0s: ...
  Frame map at 4.0s: ...
  Frame map at 6.0s: ...
  Frame map at 8.0s: ...

FORMAT MODE
  "ONE SINGLE UNBROKEN SHOT for the entire 8.0 seconds, horizontal 16:9. One continuous
   motion-control take with absolutely no cuts, no edits, no transitions, no dissolves, no wipes
   and no flash frames. Real time throughout; no speed ramps, no slow motion, no freeze frames."

OPTICS
  "47° diagonal field of view held for the entire shot, standard normal lens character,
   camera 1.2 meters from his face closing to about 1.0 meter behind him and easing back to 1.2
   on the return, natural facial proportions, no distortion."
  + focus behaviour + exposure behaviour + "Clean lens, no flares."

CAMERA
  <rig named again, then per-second movement breakdown: "0.0s to 2.0s: ... 2.0s to 4.0s: ...">
  + "The rig is never visible."

THE PERFORMANCE (critical, mirroring the previz figure)
  BODY: <rooted / travelling, and exactly what is forbidden>
  HEAD: <tracking rules>
  EYES: <where the gaze lives>
  HANDS: <each gesture, once, enumerated with the line it lands on>

ACTION TIMING
  0.0s to 2.0s: LINE ONE. <what happens, where the camera is, what the hands do>
  ...
```

**The four sentences that carry the most weight** (reproduce them nearly verbatim in our prompts):

1. *"An invisible camera target is placed separately from the head so the head is always in frame as
   the camera moves."*
2. *"Nothing else from the previz (its grey materials, proxy geometry or lighting) is inherited."*
3. *"The first visible frame is already the tight head-and-shoulders on his face; no establishing
   wide."*
4. *"One continuous motion-control take with absolutely no cuts, no edits, no transitions, no
   dissolves, no wipes and no flash frames."*

---

## P3 — Official four-step workflow instruction (meta-prompt)

**Source:** [Higgsfield, 3D Jutsu guide](https://higgsfield.ai/blog/higgsfield-3d-jutsu), Step 4
**Type:** **VERBATIM (abridged)**
**Target:** the 3D Jutsu agent, at the combine step

> *"The character and the location drop into the same 3D Jutsu conversation next to the previz
> render, and one message asks the agent to put them together. The previz provides a reference for
> the intended camera path, framing, and character behavior, and grey proxies become the real
> location, wardrobe, and performance."*

**Operational rule extracted:** the previz render, the character reference and the location reference
must live in **the same conversation** as the final request. Splitting them across sessions loses the
agent's binding between reference and role.

---

## P4 — Conversation-route Blender setup instruction

**Source:** [Higgsfield AI, official tutorial](https://www.youtube.com/watch?v=vUYq38wC_xI) @ 01:40
**Type:** **[RECONSTRUCTED]** from speech
**Target:** the chat client (Claude / Astra), to wire Blender ↔ Higgsfield

```
add Higgsfield / use Blender
```

**Context from the source:** *"open the chat, click plugins on the left, and find Higgsfield. Then
enter 'add Higgsfield / use Blender' to connect Astra, Blender, and Higgsfield. And that's it."*

---

## P5 — Infinite-loop shot request

**Source:** [Higgsfield AI, official tutorial](https://www.youtube.com/watch?v=vUYq38wC_xI) @ 02:09
**Type:** **[RECONSTRUCTED]** from speech
**Target:** Blender via Astra (L1)

**Verbatim fragments from the source:**
- *"I give Astra the story and ask for an editable camera path with a bit of handheld drift."*
- *"I'm keeping the room and the opening camera move, then replacing the ending with a pull back into
  a larger copy."*
- *"I take the opening frame from the blocking and ask Astra to send it to Nano Banana as a layout
  reference."*
- *"I also export the blocking as a video, so I can use it as the motion reference."*
- *"I'm running Seedance 2.5, 30 seconds, 16 by 9 for the aspect ratio and one continuous shot. Also
  I'm going to generate two versions so I can choose the best one."*

**Distilled request shape:**

```
Keep the room and the opening camera move. Replace the ending: as the character runs for the
wardrobe, the camera pulls back to reveal our entire room sitting on a table inside a larger copy of
itself, dropping us back into the opening shot. The first and last frames must match exactly.

Give me an editable camera path with a bit of handheld drift.
```

**The loop technique, named:** the loop seam is solved *geometrically* — nesting a copy of the scene
so the pull-back lands on the opening frame. **Note the counter-intuitive detail from the source:**
*"the first and last frames match perfectly, even though the camera is in totally different spots
compared to the beginning."* Frame-matched loops do not require position-matched cameras.

---

## P6 — Impossible mirror shot request

**Source:** [Higgsfield AI, official tutorial](https://www.youtube.com/watch?v=vUYq38wC_xI) @ 05:39
**Type:** **[RECONSTRUCTED]** from speech
**Target:** Blender via Astra (L1) → Seedance 2.5 (L3)

**Verbatim fragments:**
- *"I ask Astra for a 15-second scene."*
- *"I asked for a mirrored copy of the room with both characters moving in sync. The mirror itself is
  just an opening. It looks like a reflection, but the camera can pass straight through."*
- *"The camera follows an editable curve, pulling back through the mirror."*
- *"I'm going to ask Astra to generate four detective character sheets through Higgsfield... I'm
  choosing the first one, and I'm going to attach it with the blocking and ask for two 15-second
  versions, each in one continuous shot."*

**Distilled request shape:**

```
15-second scene. A detective faces the camera; the camera moves backward and passes straight through
a mirror. There is no cut — one continuous shot.

Build a mirrored copy of the room with both characters moving in sync. The mirror itself is just an
opening: it reads as a reflection, but the camera can pass straight through it.
The camera must follow an editable curve.
```

**Mechanic to reuse:** impossible shots become possible by *building the illusion as geometry* rather
than asking the model to fake it. A mirror is a hole with a synced double behind it.

---

## P7 — 3D Jutsu multi-location continuous shot request

**Source:** [Higgsfield AI, official tutorial](https://www.youtube.com/watch?v=vUYq38wC_xI) @ 07:48
**Type:** **[RECONSTRUCTED]** from speech
**Target:** 3D Jutsu (L1)

**Verbatim fragments:**
- *"I ask for one continuous 30-second shot following the couple from the street down the stairs
  through the corridor and kitchen and into the casino."*
- *"I ask for separate paths for the camera and the characters so I can adjust them."*
- *"Let's give the opening a better hook. Start behind the car's window. The car pulls away when the
  camera follows the couple inside."*
- *"I can move things myself or ask for another change in the chat — change the color, change the
  assets or even add them here. The colors identify the roles. So black is man, white is woman and
  yellow marks the kitchen workers. Their paths show where they move through the scene."*
- *"I add character sheets for a couple plus reference images for the street and the gaming hall. I'm
  going to describe the other characters in the prompt — the cooks, the staff, and the guests."*
- *"So, let's send the blocking and all four images to Astra. Then ask it to build the CS2.5 prompt
  and generate the shot."*

**Two reusable conventions:**
1. **Colour-coded roles** — assign a distinct colour per cast role so both the operator and the agent
   can read occupancy at a glance. Adopt as a pipeline standard: **lead = one distinctly shaped proxy
   in a unique colour; crowd = uniform boxes.**
2. **Tiered cast treatment** — hero characters get reference sheets; background characters are
   *described in the prompt only*. Do not spend reference slots on extras.

---

## P8 — Concert: 1 singer + 66 dancers

**Source:** [Higgsfield AI, official tutorial](https://www.youtube.com/watch?v=vUYq38wC_xI) @ 10:39
**Type:** **[RECONSTRUCTED]** from speech
**Target:** Blender via Astra (L1) → Seedance 2.5 (L3)

**Verbatim fragments — this is the clearest statement of the position/choreography split:**
- *"I'm asking Astra for a 30-second sequence in Blender with the shots already cut together.
  Close-ups, wide shots, overheads, slow dolly moves, and quick pushes."*
- *"The singer stands at the center surrounded by three rings of dancers and 10 columns."*
- *"The dancers are boxes, and the singer has a different shape, so the roles are easy to
  distinguish."*
- *"10 in the inner circle, 20 in the middle, and 36 on the outside."*
- *"I like this move where the camera drops and then tilts up. I can check the framing in Blender
  before generating the final sequence. The boxes mark where the dancers stand and which way they're
  facing."*
- *"I'm going to handle the actual choreography in the prompt so the model keeps their movement fluid
  instead of copying the stiff blocking."*
- *"I'm also going to include the music and vocal directions in the same request, so the track is
  generated with the video."*

**THE RULE — write it on the wall:**

> **Position in the blockout. Choreography in the prompt.**
> A blockout that animates a dance produces a dance that looks like a blockout. The blockout's job in
> a crowd scene is *occupancy and orientation*: where each body stands and which way it faces.

**Also proven:** audio direction (music + vocal) goes in the *same* request as the picture, so the
track is generated with the video rather than married in post.

---

## P9 — One-take commercial with lens changes

**Source:** [Higgsfield AI, official tutorial](https://www.youtube.com/watch?v=vUYq38wC_xI) @ 12:54
**Type:** **[RECONSTRUCTED]** from speech
**Target:** Blender via Astra (L1) → Seedance 2.5 (L3)

**Verbatim fragments:**
- *"I asked Astra to block out a 30-second chase in Blender and laid out the concept. Our tiny hero
  flees from a vacuum, gets sucked straight through the hose, and lands inside the dust bin. Then the
  camera pulls back through the clear plastic wall to reveal the final product."*
- *"By shifting camera sizes and focal lenses on the fly, we got ultra crisp macro shots and
  impossible transitions between scenes."*
- *"I'm going to ask Astra to generate references for the hero, the woman, and the vacuum. Again, I'm
  going to use my photo for the hero's character sheet. For the woman, I'm defining her outfit,
  including the striped pajamas and slippers. And this is the vacuum reference with a transparent
  dust compartment we'll reveal at the end."*
- *"If the client needs changes, I've got the blocking right here, ready to revise."*

**Mechanics worth adopting:**
- **Scale is a camera problem.** A "tiny hero" is achieved by macro framing, not by asking the model
  to understand scale.
- **The product reveal is planned as a camera move** (pull back through the transparent wall), so the
  commercial ends on the product by construction.
- **Blocking is the revision surface.** Client notes are answered by recutting the blockout.

---

## P10 — Frame-by-frame prompt generation (the playblast handoff)

**Source:** [askNK](https://www.youtube.com/watch?v=BmkNqEYjQFA) @ 06:40
**Type:** **[RECONSTRUCTED]** from speech
**Target:** the vision-capable chat model, given the Blender playblast + object references

**Verbatim fragments:**
- *"Import our viewport playblast and the references of various stuff that we want to use to drive
  the key objects in our scene."*
- *"Tell Claude to write a 30-second Seedance prompt which is based on the video blocking that we
  have."*
- *"It should read the input video and write out the prompt second by second to match the camera
  motion in the clip."*
- *"Press enter and Claude is going to go through and read the entire clip frame by frame and write
  the prompt to match what the camera is actually doing."*
- On the generation side: *"reference individual objects. For example, might want to reference the
  police car by typing the add sign (@) and selecting the image that has to do with it."*

**Distilled instruction:**

```
Read the attached viewport playblast frame by frame. Write a <duration>-second <model> prompt for
this shot, broken down second by second, matching the camera motion in the clip exactly.

For each second, state: where the camera is, what it is doing, where the subject sits in frame, and
what the subject is doing.

Use these object references where relevant: <attached images>. Reference each by name.
Do not carry over the blockout's grey materials, proxy geometry or lighting.
```

---

## P11 — 3D Jutsu scene generation from a reference image

**Source:** [Zane Hoyer](https://www.youtube.com/watch?v=pJLPpB_zueg)
**Type:** **[RECONSTRUCTED]** from speech — but the *lesson* is quoted verbatim
**Target:** 3D Jutsu agent, model `GPT-6 Astra`, 16:9, 9 s duration

**Recovered request:**

```
Generate me a 3D scene based off this image. Spend lots of time on details. I want there to be a
little human holding a flashlight pointed at a big rock shaped like a skull. After that, I want you
to animate me a camera slowly panning through the trees and then zooming in on the human.
```

**Then the two-render request (this pattern is worth standardising):**

```
Great. I want you to render this out with cinematic lighting and add texture to all of the 3D objects
so that this looks like a professional 3D artist did it. Render me one version using the actual 3D
objects and the camera, and then one version with Seedance 2.5 using the exact positioning and motion
from the camera.
```

**Verbatim lesson from the source:** *"I put this sentence in here because if you just tell it to
generate you a 3D scene, it's usually pretty basic. So, I try and get all of that in the first prompt,
so I don't have to keep re-prompting it once it generates it."*

**Rule extracted:** front-load detail. `Spend lots of time on details` is a real, effective
instruction, not politeness. Ask for **both** render variants in one request — native 3D render and
model-generated — because they cost one round trip and give a genuine A/B.

---

## P12 — Client-revision request (blockout recut)

**Source:** [Gachoki Studios](https://gachoki.com/block-in-blender-finish-with-ai/) — reported
**Type:** **[RECONSTRUCTED]**
**Target:** Blender via agent (L1)

**Recovered request shape (the six-person dialogue scene):**

```
Build a round table with six characters around it. No faces and no bodies yet — grey placeholder
boxes only.

Camera: <an explicit shot list — specific rails, targets and cuts>, not "make it cinematic".
Add subtle handheld sway so the move doesn't read as artificial.
```

**Then:** *"Let Claude write the dialogue itself, using the camera setup it already built as
context, and generate the final video from that blocking plus the dialogue prompt."*

**Closing note from the source, worth internalising:** *"the craft being protected is
cinematography, not software."* The blockout route removes the labour of re-execution, not the need
for judgement.
