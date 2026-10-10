# SOP-01 — Pipeline Setup & Preflight

**Stage:** S0 · **Run once per machine, then every session**

This SOP gets the machine ready and then proves it is ready. The verification step is not
optional: several of the failure modes below are **silent**, producing a build that reports
success while emitting nothing useful.

---

## 1. What must be present

| Component | Why | Verified in this workspace |
|---|---|---|
| Python 3.12+ (host) | runs the toolkit | `C:\Python312\python.exe` |
| Blender (portable or installed) | blockout and previz render | `tools/blender-5.2.1-windows-x64/blender.exe` |
| Blender 4.5.9 LTS *(second build)* | the Higgsfield add-on reports support for 4.2–5.1 | `tools/blender-4.5.9-windows-x64/blender.exe` |
| ffmpeg + ffprobe on PATH | previz encoding and duration verification | `WinGet\Links` |
| yt-dlp | ingesting tutorial/reference video | `%APPDATA%\Python\Python312\Scripts\yt-dlp.exe` |
| Higgsfield MCP credentials | generation, balance, media | connected, `ultra` plan |

**Why two Blender builds.** Blender is installed as a *portable* zip, not via a package
manager, because the pipeline must pin a version. Blender's Python API changes between minor
releases in ways that break code silently — this pipeline has already been broken once by
Blender 5.x moving F-Curves onto slotted actions. Pin the version; upgrade deliberately.

---

## 2. Set the Blender path

The toolkit never guesses. Either pass `--blender` explicitly or set the environment variable:

```powershell
$env:BLENDER_EXE = 'D:\App development\YouTube_Movie_Factory_v3\tools\blender-5.2.1-windows-x64\blender.exe'
```

Persist it per session, or add it to the project `.env`. If you use the add-on route, point
`BLENDER_EXE` at the **4.5.9 LTS** build instead, because the add-on's stated support window
is 4.2–5.1.

---

## 3. Preflight — run this before any production work

Three checks. Each one catches a different silent failure.

### 3.1 Blender is callable and reports the expected version

```powershell
& $env:BLENDER_EXE --version | Select-Object -First 1
```

Expect `Blender 5.2.1 LTS`. A different version is not automatically wrong, but the pinned
one is the version the toolkit's API assumptions were tested against.

### 3.2 The toolkit's contract tests pass

```powershell
& $env:BLENDER_EXE --background --factory-startup `
    --python 50-toolkit\tests\test_blockout.py
```

Expect `10 passed, 0 failed`. **Do not skip this.** These tests exist because each one
already caught a real, silent defect — materials rendering in default grey, flat shading
quietly becoming lit, role colours never reaching the render, and a loop seam that looked
fine in every individual frame. A failing test here means the blockout you are about to
build cannot be trusted, and you would not find out until after spending credits.

### 3.3 The Higgsfield connection and balance

- Balance is read live from the MCP `balance` tool. **Record it in the project log at the
  start and the end of every project.**
- Before any generation, confirm which billing path applies — see §5.

---

## 4. Spec validation before any build

```powershell
python 50-toolkit\build_blockout.py --spec <shot.json> --out <dir> --dry-run
```

`--dry-run` validates without building. It checks structure, frame arithmetic, that the
camera starts inside its own set, that beats are ordered, and — for a loop — that no cast
member travels and fails to return. Read the problem list; a spec problem found here costs
nothing, and the same problem found after generation costs a full regeneration.

---

## 5. Billing rules that change decisions

These are the cost facts that most often surprise people, and each one has already changed a
routing decision in this pipeline.

| Rule | Consequence |
|---|---|
| **3D Jutsu is billed per agent message, not per scene.** `Auto` is free; the model selector sets the price per turn (GPT 6 Astra is roughly 17 credits/turn, over 40× the cheapest paid option). | For planning-heavy or iterative 3D Jutsu work, select a cheap model; reserve Astra for turns that genuinely need it. |
| **Unlimited plans do NOT cover the Blender plugin, MCP, CLI, Canvas or Supercomputer.** Those always deduct credits regardless of plan. | An all-unlimited subscription does not make the plugin free. Budget for it. |
| **No published price for previz MP4, static frame, or GLB export.** | Measure on first use; log in `MODEL_NOTES.md`. |
| **Seedance 2.5 is roughly 6.5 credits per second at 720p** (~52 credits for 8 s). | A 30 s two-variant pair is the single largest line item in a shot's budget. |
| **Genjutsu: 15 s costs 40 / 104 / 144 credits at 480p / 720p / 1080p**, with 1 video of 4–30 s and up to 30 reference images. | Genjutsu is cheaper than a fresh Seedance generation *and* inherits motion exactly — check it first when a blockout already exists. |

**Correction on record:** a widely repeated community figure of "~200 credits for a 20 s
Seedance 2.5 render" is **refuted**. That number is Higgsfield's own figure for a *full
end-to-end Supercomputer production*, not a single render. The correct 20 s @ 720p figure is
approximately 130 credits.

---

## 6. Known silent failure modes

Read this list before debugging anything. Every entry produced a build that reported success.

| Symptom | Cause | Fix |
|---|---|---|
| Build "succeeds", no files written | Blender catches a script exception, prints a traceback, and exits **0** | the host wrapper now treats a traceback in the output as failure — never trust the exit code alone |
| Proxies render in Blender's default grey | materials assigned but the shader colour never set | `_role_material` sets both the node graph and `diffuse_color` |
| "Flat" shading looks lit | `NameError` inside a defensive `try/except` silently fell through to a lit render | shading mode is now recorded in the report as `shading_effective` |
| Cannot find the render engine you expect | `RenderSettings.engine` is a **dynamic** enum that lists only registered engines | probe by trying to set each candidate |
| Camera animates but nothing moves | Blender 5.x moved F-Curves onto slotted actions; `action.fcurves` no longer exists | `_iter_fcurves` handles both API shapes |
| Loop looks fine but seams on replay | travelling cast, or bezier ease at the path endpoints | loop-integrity check in the spec validator, drift pinned to zero on seam frames, endpoint handles set to VECTOR |

---

## 7. Directory conventions

```
3d_pipeline/                     the knowledge base and toolkit (this repo area)
  examples/<project>/            a worked example, kept as a reference
  projects/<project>/            live productions
    brief.md research.md concept.md
    shots/<SHOT_ID>/             one directory per shot — see PIPELINE_ARCHITECTURE §4.3
    wrapup.md
  library/environments/<slug>/   reusable environments, each with a used_by.md
50-toolkit/                      the code
tools/                           pinned Blender builds (not committed)
research/                        raw ingested sources
```

**Rule:** `examples/` is for worked references that demonstrate the method; `projects/` is for
live work. Never develop a new pattern inside a live project — prove it in `examples/` first,
then promote it into the toolkit.

---

## 8. Session start checklist

- [ ] `BLENDER_EXE` set and `--version` matches the pin
- [ ] Contract tests: 10 passed, 0 failed
- [ ] Higgsfield balance recorded
- [ ] Routing decision for this session made against §5 (which model, which billing path)
- [ ] Prior project searched in `40-memory/PROJECT_LOG/` for a reusable environment or blockout
- [ ] `MODEL_NOTES.md` re-read for anything that contradicts the docs
