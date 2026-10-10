# PROMPT_TEMPLATES — The Working Vault

Sibling to [`RECOVERED-PROMPTS.md`](RECOVERED-PROMPTS.md). That file preserves **evidence**; this
file holds **instruments** — templates meant to be copied, filled and run.

Every template carries: what it is for, when not to use it, and the failure it prevents.

---

## T1 — Blockout prompt (3D Jutsu agent, or Blender via conversational agent)

**Use for:** any shot where you need a previz the final model can follow.
**Do not use for:** a shot you are building from code (`shot.json` + `build_blockout.py` is more
reliable and free).

```
<DURATION>s, <ASPECT>. <ONE SENTENCE: who is in the scene and what they are doing.>
<COLOUR-CODED CAST MAP — one line per role, using the pipeline colour standard.>

FRAMING: <shot size> throughout: <exactly what is in frame>. <What is deliberately OUT of frame.>
An invisible camera target is placed separately from the subject so <SUBJECT> stays framed as the
camera moves.

CAMERA = <RIG NAME>. <One sentence: the move, start to end, in plain geometry.>
Speed: <constant / accelerating / easing>.
Constraints: the camera never stops, never reverses, never zooms.
The camera passes through nothing — no wall, no floor, no ceiling, no prop. Nothing passes through
the camera.

<SUBJECT>: <what the subject does for the whole shot, as a continuous state, not a pose.>

<SET>: <volumes described as architecture, with materials, and an explicit occupancy statement.>

Clean sharp image, no motion blur smear, no film grain, no vignette, no lens flare, no readable text
or logos, no neon, no <KNOWN COLOUR CAST TO AVOID>.
```

**Failure it prevents:** the model "helping" by widening the shot, adding limbs, decorating with
grain and flare, and letting geometry interpenetrate.

**Colour standard (pipeline-wide — keep it consistent so blockouts read at a glance):**

| Role | Proxy | Colour |
|---|---|---|
| Lead / hero | capsule or distinctly-shaped solid | **red** |
| Supporting cast | box | **blue** |
| Crowd / extras | uniform boxes | **grey** |
| Camera path | curve + empty target | yellow |
| Set volumes | cubes | desaturated |

---

## T2 — Final generation prompt (Seedance 2.5 / Genjutsu / Cinema Studio)

**Use for:** the single expensive generation. Fill every section; do not skip sections because they
"seem obvious" — the official grammar includes them because models need them.

```
SCENE CONTEXT
<One dense paragraph. Format and duration. Who. Where. What the camera does. The mood in two
adjectives. End with the exclusivity sentence: "X is the only <voice/sound/moving element>.">

ACTIVE REFERENCES
<<<image_1>>>: <ROLE IN CAPS>. <Identity in one sentence — age, build, distinguishing feature.
Wardrobe enumerated item by item, materials and colours stated.>
"His/her face and full outfit stay identical for the whole shot. Closely matches the reference."

<<<video_1>>>: THE CAMERA PATH AND THE FIGURE'S BEHAVIOUR. Reference controls two things:
(1) the camera move: <the move described in the same words used in the blockout prompt>
(2) the figure's behaviour: <body rules, head rules, where the body stays>
"Nothing else from the previz (its grey materials, proxy geometry or lighting) is inherited."

LOCATION MAP
<The set as a real place: materials, surfaces, fixtures, what is on the walls. Then an explicit
occupancy statement: "The room is EMPTY except <who>.">

FIRST FRAME AND SPATIAL BLOCKING
"The first visible frame is already <the shot size> on <subject>; no establishing wide."
Frame map at 0.0s: <subject occupancy as x%/y%>; <other elements and their x%>
Frame map at <t>: ...
Frame map at <t>: ...
Frame map at <END>s: <the final composition>

FORMAT MODE
"ONE SINGLE UNBROKEN SHOT for the entire <DURATION> seconds, <ASPECT>. One continuous
motion-control take with absolutely no cuts, no edits, no transitions, no dissolves, no wipes and no
flash frames. Real time throughout; no speed ramps, no slow motion, no freeze frames."

OPTICS
"<N>° diagonal field of view held for the entire shot, <lens character>, camera <distance> from
<subject> <what the distance does over time>, natural proportions, no distortion."
Focus: <what is sharp, what is soft, and how focus moves>.
Exposure: <what holds>. "Clean lens, no flares."

CAMERA
<Rig named. Per-second breakdown:>
0.0s to <t>s: <what the camera does>
<t>s to <t>s: ...
<t>s to <END>s: ...
"The rig is never visible."

THE PERFORMANCE (critical, mirroring the previz figure)
BODY: <rooted or travelling; what is forbidden — never steps, never shifts feet>
HEAD: <tracking rules>
EYES: <where the gaze lives and when it may break>
HANDS: <each gesture ONCE, tied to the line or beat it lands on>

ACTION TIMING
0.0s to <t>s: <beat label>. <What happens, where the camera is, what the hands do.>
<t>s to <t>s: ...
<t>s to <END>s: ...
```

**Failure it prevents:** camera drift, subject identity drift, mid-shot costume changes, unrequested
cuts, motion blur smear, and the model inheriting the blockout's grey look.

---

## T3 — Blockout → prompt (the vision pass)

**Use for:** generating a timestamped final prompt from a previz render.
**Note:** the toolkit generates a scaffold from `shot.json` automatically
(`50-toolkit/make_prompt.py`). Use this template when you need the vision pass as well — i.e. when
the previz contains behaviour that the spec does not fully describe.

```
Read the attached previz clip frame by frame. It is a grey blockout; its materials and lighting
are NOT the intended look and must not be described.

Write a <DURATION>-second <MODEL> prompt for this shot, broken down second by second, matching the
camera motion in the clip exactly. Use the section order from the house grammar:
SCENE CONTEXT / ACTIVE REFERENCES / LOCATION MAP / FIRST FRAME AND SPATIAL BLOCKING / FORMAT MODE /
OPTICS / CAMERA / THE PERFORMANCE / ACTION TIMING.

For each second, state: where the camera is, what it is doing, where the subject sits in frame as a
percentage, and what the subject is doing.

Subject identity comes from the attached character reference. The location comes from the attached
location plate. The previz controls ONLY the camera path and the figure's behaviour.
```

---

## T4 — 3D Jutsu scene generation from a reference image

**Use for:** starting a browser scene from a mood/reference image.

```
Generate a 3D scene based on this image. Spend lots of time on details — especially <THE TWO THINGS
THAT MUST BE GOOD>. Include <NAMED SUBJECTS AND THEIR ACTION>. After that, animate a camera that
<CAMERA MOVE, START TO END>.
```

**Rule from the source:** front-load detail in the *first* prompt. `Spend lots of time on details` is
an effective instruction. Naming what must be good beats a generic quality adjective.

---

## T5 — Two-render request (native 3D + model-generated, one round trip)

**Use for:** every 3D Jutsu scene where you want a genuine A/B for one spend.
**Why:** it costs one round trip and produces a native render *and* a Seedance 2.5 render from the
exact same camera — the cleanest possible comparison of "3D render" vs "AI realisation".

```
Great. Render this out with high-quality textures and cinematic lighting so it looks like a
professional 3D artist did it.

Render one version using the actual 3D objects and the camera, and then one version with
<Seedance 2.5 / Cinema Studio> using the exact positioning and motion from the camera.

Keep the camera movement exactly as it is.
```

---

## T6 — Environment reuse / restyle

**Use for:** the economic engine of the pipeline — many shots from one environment.

```
Keep the environment and the camera move exactly as they are.

<ADD / REMOVE / REPLACE: specific objects, with positions relative to existing ones.>

Re-render. Nothing else changes.
```

**Never** regenerate the environment to change one prop. Objects are swapped; the environment is
capital.

---

## T7 — Ripple edit (change once, propagate)

**Use for:** a note that applies to more than one shot — a wardrobe change, a palette shift, a
location variant.

```
Apply this change across every shot that contains <SCOPE>:
<THE CHANGE, stated as a diff against the current state — from X to Y>

Hold everything else constant: camera moves, timing, framing and lighting are unchanged.
Update the affected reference pack entries and list which shots were modified.
```

**Discipline:** a ripple edit is a *versioned* change. Bump the project version and record which
shots were regenerated, or continuity across the project becomes unprovable.

---

## T8 — Shot-spec authoring (code route)

**Use for:** any shot that is one of many, must be reproducible, or will be restyled later.

Not a prose prompt — a filled `shot.json`. See
[`../../00-overview/PIPELINE_ARCHITECTURE.md`](../../00-overview/PIPELINE_ARCHITECTURE.md) §4.1 for
the schema and `../../50-toolkit/` for the builder.

**Rule:** if the camera move can be expressed as coordinates, it should be. Prose is for intent;
coordinates are for geometry.

---

## T9 — Take scoring / selection record

**Use for:** every selection decision. Makes taste auditable and gives `LESSONS.md` something real.

```
Shot: <SHOT_ID>   Take: <A|B|...>   Seed: <n>   Credits: <n>

Camera fidelity to spec   /5   <what matched, what drifted>
Timing / beats            /5   <which beats landed>
Identity hold             /5   <where drift started, if at all>
Spatial continuity        /5   <any geometry or occupancy break>
Artifacts                 /5   <count and type>
Audio correctness         /5   <if applicable>

VERDICT: SELECT | REJECT
REASON (one sentence, specific enough to become a LESSONS entry):
REUSABLE? <can this take be salvaged with an Object Swap / extension / reframe?>
```

**Rule:** a rejection with no reason is a wasted generation. The reason is the product of the spend.
