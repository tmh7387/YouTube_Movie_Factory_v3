# 50-toolkit — The Executable Half of the Pipeline

The SOPs describe the method. This directory *performs* it. Everything here is plain Python
(stdlib only) plus Blender's bundled interpreter.

---

## Why this exists

The conversational route (an agent building in Blender via the add-on or 3D Jutsu) is
excellent for **exploration** and poor for **production**, because it is non-deterministic:
the same request yields a different blockout every time. A blockout that cannot be
re-derived cannot be diffed, reviewed, or restyled with confidence.

This toolkit makes the blockout a **function of a spec**. Same spec in, same blockout out — on
any machine, forever. That is what turns a blockout into reusable capital
([`PATTERNS.md` P-02](../40-memory/PATTERNS.md)) rather than scratch work.

---

## The tools

### `shot_spec.py` — the data contract

Defines `shot.json`: duration, fps, aspect, optic, camera path, set volumes, cast proxies,
beats, constraints, and `exclude_from_realisation`. Validates hard enough that a malformed
spec fails **before** Blender starts, with an actionable message.

Also enforces the two rules that are invisible in any single frame:

- **Camera clearance** — samples the interpolated path and reports any point outside every
  set volume. "Did the camera ever leave the room" is the failure that ruins an otherwise good
  take.
- **Loop integrity** — a loop is a claim that the clip replays without a seam. If a cast
  member travels and never returns, the claim is false, and nothing else in the pipeline
  notices. The validator refuses it.

### `build_blockout.py` — the builder

Reads a `shot.json`, builds the blockout in Blender, and emits the Blockout Kit:

| Output | Purpose |
|---|---|
| `shot.v<N>.blend` | editable blockout, versioned |
| `shot.v<N>.glb` | portable geometry for other tools |
| `previz_<ID>.mp4` | **clean** previz — the model-facing motion reference |
| `previz_<ID>_annot.mp4` | annotated previz — human review only |
| `blockout_report.json` | machine-checkable record of what was built and what was measured |

It also *measures its own output*, because the failure modes here are silent:

- **Readability** — mean luminance across sampled frames. A previz nobody can see cannot be
  reviewed, and "it looked fine on my machine" is not a check.
- **Colour map verification** — confirms every cast role's colour actually reached the
  rendered pixels. A proxy rendering in Blender's default grey destroys the colour-coded cast
  map while looking like a lighting problem.
- **Loop seam** — pixel-difference between the first and last rendered frames. The one claim a
  loop makes that nothing else verifies.

```
python build_blockout.py --spec shot.json --out out/ [--render] [--shading flat|lit]
                         [--frames beats] [--dry-run]
```

### `make_prompt.py` — spec → final prompt

Generates the L3 generation prompt in Higgsfield's published house grammar, deriving the
camera language, frame maps and timeline from the spec's own geometry. This is the mechanical
half of the "vision pass" described in the architecture: because the spec already contains the
beat table and keyframes, the scaffold is generated from *data* and a vision pass over the
previz is used to refine and verify rather than to invent.

Shape and distance are turned into directions deterministically (`pushes in`, `looking north,
tilted down`, `1.8 m from its target`), so **the same spec always yields the same wording** —
and a difference between prompt and blockout becomes a diffable discrepancy instead of a
judgement call.

Every section is always emitted. Where the spec is thin the generator writes an explicit
`TODO` marker rather than plausible filler, so the gap is visible in review:

```
python make_prompt.py --spec shot.json [--references references.json] [--out prompt.txt]
                      [--strict]
```

`--strict` exits non-zero if any `TODO` remains — use it in automation to prevent an
under-specified prompt from reaching a paid generation.

### `tests/test_blockout.py` — the contract tests

Ten tests that run inside Blender. **Each one exists because it already caught a real, silent
defect.**

```
blender --background --factory-startup --python tests/test_blockout.py
```

Expect `10 passed, 0 failed`. A failing test means the blockout cannot be trusted, and you
would not otherwise find out until after spending credits.

---

## Usage

```powershell
$env:BLENDER_EXE = 'D:\App development\YouTube_Movie_Factory_v3\tools\blender-5.2.1-windows-x64\blender.exe'

# 1. validate the spec
python 50-toolkit\build_blockout.py --spec <shot.json> --out <dir> --dry-run

# 2. fast look — the beat frames only, seconds not minutes
python 50-toolkit\build_blockout.py --spec <shot.json> --out <dir> --render --frames beats

# 3. full previz once the look is right
python 50-toolkit\build_blockout.py --spec <shot.json> --out <dir> --render

# 4. generate the final prompt
python 50-toolkit\make_prompt.py --spec <shot.json> --references <references.json> --out <dir>\prompt.txt

# 5. before any production work
& $env:BLENDER_EXE --background --factory-startup --python 50-toolkit\tests\test_blockout.py
```

Worked example: [`../examples/demo-infinite-loop/`](../examples/demo-infinite-loop/) — a
15-second seamless loop, fully built and verified, with its report and generated prompt.

---

## Hard-won platform findings

These were discovered the slow way. Each is now guarded by code or by a test.

### Blender 5.x moved F-Curves onto slotted actions

`action.fcurves` no longer exists in Blender 5.x. An `AttributeError` raised inside Blender's
interpreter does **not** change the process exit code — Blender catches it, prints a traceback,
and exits **0**. The first version of this toolkit therefore reported a successful build that
produced no files.

Two fixes, both necessary: `_iter_fcurves()` handles both API shapes, and the host wrapper
treats a traceback in Blender's output as failure rather than trusting the exit code.

### `RenderSettings.engine` is a dynamic enum

It lists only engines whose add-ons are currently registered, so introspecting it is
unreliable — Workbench is present and settable in this build yet **absent** from the RNA enum.
Probe by *trying to set* each candidate. The enum-based test silently concluded "no Workbench"
and fell back to a different render path while still reporting the requested shading mode.

### Materials must be set in two places

A Blender material has a node graph and a separate viewport display colour
(`diffuse_color`). Different render paths read different ones. Set both, or a proxy renders in
Blender's default grey.

### Emission, not diffuse, for a flat blockout

The flat pass uses **unlit emission materials**. Workbench's flat-light mode renders a
pure-emission proxy near-black and washes its backing world to a light grey that is
chromatically identical to the light-grey "crowd" role — which destroys the cast map. Emission
under EEVEE renders the exact specified colour and makes the backdrop fully controllable.

### sRGB, not linear, comes out of a PNG

Spec colours are **linear** shader inputs; a PNG on disk holds **sRGB**-encoded values. A lead
red specified as `0.90, 0.13, 0.13` arrives from the PNG as roughly `0.95, 0.39, 0.39`.
Comparing the two directly made the colour verifier report "role colours missing" for a render
that plainly showed them. Every colour comparison converts first.

### Bezier ease breaks a loop seam

`AUTO_CLAMPED` handles ease in and out of every keyframe, which is correct along a path and
wrong at its ends: an eased endpoint stalls exactly where the seam is. Path endpoints are set
to `VECTOR`, and handheld drift is pinned to exactly zero on both seam frames with harmonics
that complete whole cycles across the shot.

### Geometry must never be trusted to read as intended

The set volumes are drawn from wireframe cube primitives, which have no real surface. A
`reveal` volume is a larger *enclosing* box and must be hidden from render or it hides the
entire scene. Visibility is decided by the volume's declared **role**, not left to chance.

---

## Design principles

1. **Fail loudly, and measure what you claim.** Every silent failure listed above produced a
   build that reported success. The response is not vigilance — it is a check that fails.
2. **A TODO beats plausible filler.** An under-specified prompt that says so is worth more
   than one that reads well and omits a required section.
3. **Determinism is the product.** Prose drifts; a spec does not. The same spec must yield the
   same blockout, the same prompt, and the same report on any machine.
4. **Stdlib only, no exceptions.** This code runs in Blender's bundled interpreter, which has
   no third-party packages. A dependency here would mean the tests could not run in the one
   environment where the bugs actually live.
5. **Every defect becomes a test.** The population of `tests/` is the project's memory of what
   has already gone wrong.
