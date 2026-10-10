"""make_prompt.py — generate the final-generation prompt from a shot spec.

This is stage S7 of the pipeline and the mechanical half of the "vision pass": the spec
already contains the beat table, the camera keyframes and the constraints, so the
second-by-second scaffold can be derived from *data* rather than re-invented in prose. A
vision pass over the previz render can then refine and verify it.

Output uses Higgsfield's published house grammar, recovered verbatim during research. The
section order is not cosmetic — the Seedance 2.5 guide states plainly that *"skip a section
and the output tends to fail in a specific, predictable way."*

    SCENE CONTEXT
    ACTIVE REFERENCES          <<<image_1>>> ... <<<video_1>>>
    LOCATION MAP
    FIRST FRAME AND SPATIAL BLOCKING   (frame maps with x/y percentages)
    FORMAT MODE
    OPTICS
    CAMERA                     (time-segmented)
    THE PERFORMANCE
    ACTION TIMING              (time-segmented)
    PHYSICS
    LIGHTING
    AUDIO
    POSITIVE CONSTRAINTS

Every section is emitted even when the spec is thin, because a missing section is a
predictable failure rather than a saving of effort. Where the spec does not supply detail,
the generator emits an explicit `TODO` marker so the gap is visible in review instead of
being silently filled with plausible language.

Deliberately stdlib-only and Blender-free: prompt generation must be runnable anywhere.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Iterable

# --------------------------------------------------------------------------------------


def _load_shot_spec():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    spec = importlib.util.spec_from_file_location("shot_spec", here / "shot_spec.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["shot_spec"] = module
    spec.loader.exec_module(module)
    return module


shot_spec = _load_shot_spec()
ShotSpec = shot_spec.ShotSpec
SpecError = shot_spec.SpecError


# --------------------------------------------------------------------------------------
# Geometry -> language
#
# A model reads prose, so coordinates have to become directions. These helpers do that
# deterministically, which is the whole advantage of generating the prompt from the spec:
# the same spec always yields the same wording, and a discrepancy between prompt and
# blockout becomes a diffable difference rather than a judgement call.
# --------------------------------------------------------------------------------------

COMPASS = (
    "east", "north-east", "north", "north-west",
    "west", "south-west", "south", "south-east",
)


def _bearing(a: tuple[float, float, float], b: tuple[float, float, float]) -> str:
    """Compass direction FROM a TO b, in the project's own axis convention.

    The convention is the spec's, not a surveyor's: +X is east, +Y is north, +Z is up.
    Getting this wrong is not cosmetic — a prompt that says "looking east" when the blockout
    looks north produces a generated shot pointing 90° off, and the error is invisible until
    the credits are spent.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return "in place"
    angle = math.degrees(math.atan2(dy, dx)) % 360.0
    index = int(((angle + 22.5) % 360.0) // 45.0)
    return COMPASS[index]


def _height_phrase(delta_z: float) -> str:
    if delta_z > 0.15:
        return "rising"
    if delta_z < -0.15:
        return "descending"
    return "holding height"


def _motion_verb(a: tuple[float, float, float], b: tuple[float, float, float]) -> str:
    """Name the camera move from the geometry, not from the author's vocabulary.

    Judged against the *dominant* component so the label is always the move a camera
    operator would call it, which is what a generation model has seen described.
    """
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    horizontal = math.hypot(dx, dy)
    if horizontal < 0.02 and abs(dz) < 0.02:
        return "holds position"
    if abs(dz) > max(horizontal * 1.5, 0.05):
        return "cranes up" if dz > 0 else "cranes down"
    if horizontal < 1e-6:
        return "holds position"
    # Compare the axis components against the total horizontal travel.
    if abs(dx) > abs(dy) * 2.0:
        return "trucks right" if dx > 0 else "trucks left"
    if abs(dy) > abs(dx) * 2.0:
        return "pushes in" if dy > 0 else "pulls back"
    # Genuinely diagonal: name it by the dominant half and call it an arc.
    if abs(dy) >= abs(dx):
        return "arcing push" if dy > 0 else "arcing pull-back"
    return "arcing truck right" if dx > 0 else "arcing truck left"


def _closing(a: tuple[float, float, float], b: tuple[float, float, float]) -> bool:
    """True when the camera is getting closer to the origin-side of the set."""
    return math.hypot(b[0], b[1]) < math.hypot(a[0], a[1])


def _target_height_phrase(cam_z: float, target_z: float) -> str:
    """Describe the camera's tilt as a *look* direction, not as camera altitude.

    An earlier version reported `descending` whenever the target sat below the camera, which
    is true of almost every eye-level shot and reads as if the camera were sinking. Tilt and
    altitude are different claims about the shot and must not be conflated in a prompt.
    """
    delta = target_z - cam_z
    if delta > 0.20:
        return "tilted up"
    if delta < -0.20:
        return "tilted down"
    return "level"


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.dist(a, b)


def _fmt_time(t: float) -> str:
    return f"{t:.1f}s"


# --------------------------------------------------------------------------------------
# Section builders
# --------------------------------------------------------------------------------------


def section_scene_context(spec: ShotSpec) -> str:
    lines = [f"{spec.duration_s:g} seconds, {spec.aspect}."]
    if spec.intent:
        lines.append(spec.intent.rstrip(".") + ".")
    else:
        lines.append("TODO — no intent recorded in the spec.")
    if spec.format_mode:
        lines.append(f"{spec.format_mode}.")
    cast_desc = ", ".join(f"{c.id} ({c.role})" for c in spec.cast) or "no cast"
    lines.append(f"On screen: {cast_desc}.")
    return "SCENE CONTEXT\n" + "\n".join(lines)


def section_active_references(spec: ShotSpec, refs: dict | None) -> str:
    """Emit the reference slots, with the exclusion clause that must never be omitted."""
    lines: list[str] = []
    slots = (refs or {}).get("slots", {}) if refs else {}
    if not slots:
        lines.append(
            "TODO — no reference pack manifest supplied. Run again with "
            "--references references.json, or the identity and location will be invented "
            "by the model."
        )
    for slot_name in sorted(slots):
        entry = slots[slot_name] or {}
        role = str(entry.get("role", "")).upper() or "UNNAMED ROLE"
        job = entry.get("job", "")
        file = entry.get("file", "")
        lines.append(f"{slot_name.replace('image_', '<<<image_').replace('video_', '<<<video_')}>>>: {role}.")
        if job:
            lines.append(f"  Carries: {job}.")
        if file:
            lines.append(f"  File: {file}")
        controls = entry.get("controls")
        if controls:
            lines.append("  Controls ONLY: " + "; ".join(str(c) for c in controls) + ".")
        not_controls = entry.get("does_not_control")
        if not_controls:
            lines.append(
                "  Does NOT carry over: " + "; ".join(str(c) for c in not_controls) + "."
            )
    # The exclusion clause is required by the published grammar and its absence is the
    # known cause of a model trying to preserve the blockout's grey materials.
    lines.append(
        "Nothing else from the previz is inherited — not its "
        + "; ".join(spec.exclude_from_realisation)
        + "."
    )
    return "ACTIVE REFERENCES\n" + "\n".join(lines)


def section_location_map(spec: ShotSpec) -> str:
    lines: list[str] = []
    description = str(spec.set.get("description", "")).strip()
    lines.append(description or "TODO — no set description in the spec.")
    for vol in spec.volumes:
        sx, sy, sz = vol.size
        lines.append(
            f"{vol.id} ({vol.role}): {sx:.1f} m x {sy:.1f} m x {sz:.1f} m, "
            f"floor at z={vol.min[2]:.2f} m, ceiling at z={vol.max[2]:.2f} m."
        )
    # Occupancy statement — the published grammar always states what is NOT in the space.
    bodies = [c for c in spec.cast if c.role != "prop"]
    if bodies:
        lines.append(
            f"The space contains only: {', '.join(c.id for c in bodies)}. "
            "No other people, no crowd, no background extras."
        )
    else:
        lines.append("The space is EMPTY of people.")
    return "LOCATION MAP\n" + "\n".join(lines)


def section_first_frame(spec: ShotSpec) -> str:
    lines: list[str] = []
    lines.append(
        'The first visible frame is already the intended framing; no establishing wide.'
    )
    if not spec.camera_path:
        lines.append("TODO — no camera path in the spec, so no frame map can be generated.")
        return "FIRST FRAME AND SPATIAL BLOCKING\n" + "\n".join(lines)

    # Frame maps are derived from the spec's beat table, which is the same source that drove
    # the blockout's own markers — so prompt and previz cannot drift apart.
    for beat in spec.beats or []:
        cam = spec.sample_camera_position(beat.t)
        target = spec.sample_camera_target(beat.t)
        dist = _distance(cam, target)
        lines.append(
            f"Frame map at {_fmt_time(beat.t)} ({beat.label}): camera {dist:.1f} m from its "
            f"target, looking {_bearing(cam, target)}, {_target_height_phrase(cam[2], target[2])}. "
            f"{beat.action or 'TODO — no action recorded for this beat.'}"
        )
    lines.append(
        "TODO — x/y percentage occupancy per beat must be added from a previz review. The "
        "spec supplies geometry; only a frame read supplies percentages."
    )
    return "FIRST FRAME AND SPATIAL BLOCKING\n" + "\n".join(lines)


def section_format_mode(spec: ShotSpec) -> str:
    if "UNBROKEN" in spec.format_mode.upper() or "SINGLE" in spec.format_mode.upper():
        body = (
            f"ONE SINGLE UNBROKEN SHOT for the entire {spec.duration_s:g} seconds, "
            f"{spec.aspect}. One continuous take with absolutely no cuts, no edits, no "
            "transitions, no dissolves, no wipes and no flash frames. Real time throughout; "
            "no speed ramps, no slow motion, no freeze frames."
        )
    else:
        body = (
            f"{spec.format_mode}. {spec.duration_s:g} seconds, {spec.aspect}. "
            "TODO — enumerate the cuts explicitly; a cut list in prose is a predictable "
            "failure point."
        )
    return "FORMAT MODE\n" + body


def section_optics(spec: ShotSpec) -> str:
    lines = [
        f"{spec.fov_diagonal_deg:g}° diagonal field of view held for the entire shot.",
        str(spec.optic.get("character", "standard normal lens character, natural proportions, no distortion")),
    ]
    if spec.optic.get("dof"):
        lines.append(f"Focus: {spec.optic['dof']}.")
    if spec.camera_path:
        start_d = _distance(spec.camera_path[0].pos, spec.camera_path[0].target)
        end_d = _distance(spec.camera_path[-1].pos, spec.camera_path[-1].target)
        closest = min(
            _distance(k.pos, k.target) for k in spec.camera_path
        )
        lines.append(
            f"Camera starts {start_d:.1f} m from its target, closes to {closest:.1f} m at the "
            f"nearest point, and finishes {end_d:.1f} m away."
        )
    lines.append("Clean lens, no flares.")
    return "OPTICS\n" + "\n".join(lines)


def section_camera(spec: ShotSpec) -> str:
    lines = [f"CAMERA = {spec.rig}."]
    height = spec.camera.get("height_m")
    if height:
        lines.append(f"Camera height: {float(height):.2f} m.")
    drift = float(spec.camera.get("handheld_drift_m", 0.0) or 0.0)
    if drift > 0:
        lines.append(
            f"Handheld drift amplitude {drift * 100:.1f} cm — living frame, not a locked-off "
            "tripod, but no jitter."
        )
    for a, b in zip(spec.camera_path, spec.camera_path[1:]):
        verb = _motion_verb(a.pos, b.pos)
        bearing = _bearing(a.pos, b.pos)
        moved = _distance(a.pos, b.pos)
        lines.append(
            f"{_fmt_time(a.t)} to {_fmt_time(b.t)}: the camera {verb} ({bearing}, "
            f"{moved:.2f} m travelled). {b.note or ''}".rstrip()
        )
    for constraint in spec.constraints:
        lines.append(f"Constraint: {constraint}.")
    lines.append("The rig is never visible.")
    return "CAMERA\n" + "\n".join(lines)


def section_performance(spec: ShotSpec) -> str:
    lines: list[str] = []
    for member in spec.cast:
        if member.role == "prop":
            continue
        lines.append(f"{member.id.upper()} ({member.role}):")
        if member.motion:
            lines.append(f"  {member.motion}")
        if member.end is not None:
            travelled = _distance(
                (member.start[0], member.start[1], 0.0),
                (member.end[0], member.end[1], 0.0),
            )
            lines.append(
                f"  Travels {travelled:.2f} m, {_bearing(member.start, member.end)}. "
                f"Starts at ({member.start[0]:.2f}, {member.start[1]:.2f}), ends at "
                f"({member.end[0]:.2f}, {member.end[1]:.2f})."
            )
        else:
            lines.append("  Rooted — does not travel.")
        lines.append(
            "  TODO — performance detail (body, head, eyes, hands) must be authored per "
            "project. The blockout holds position and orientation only."
        )
    if not lines:
        lines.append("TODO — no performers in the spec.")
    return "THE PERFORMANCE\n" + "\n".join(lines)


def section_action_timing(spec: ShotSpec) -> str:
    lines: list[str] = []
    for beat in spec.beats or []:
        cam = spec.sample_camera_position(beat.t)
        target = spec.sample_camera_target(beat.t)
        lines.append(
            f"{_fmt_time(beat.t)} ({beat.label}): {beat.action or 'TODO — no action recorded.'} "
            f"Camera at ({cam[0]:.2f}, {cam[1]:.2f}, {cam[2]:.2f}) looking {_bearing(cam, target)}."
        )
    if not lines:
        lines.append("TODO — the spec has no beat table; the timeline cannot be generated.")
    return "ACTION TIMING\n" + "\n".join(lines)


def section_physics(spec: ShotSpec) -> str:
    body = (
        "TODO — describe how fabric, hair, smoke, dust and liquid should move. This section "
        "is skipped most often and its absence is a predictable failure: garments and hair "
        "go rigid or drift unnaturally."
    )
    return "PHYSICS\n" + body


def section_lighting(spec: ShotSpec) -> str:
    body = (
        "TODO — state where the light is motivated from, its direction, and how it falls on "
        "faces. The previz lighting is NOT inherited."
    )
    return "LIGHTING\n" + body


def section_audio(spec: ShotSpec) -> str:
    audio = spec.audio or {}
    mode = str(audio.get("mode", "")).strip()
    notes = str(audio.get("notes", "")).strip()
    if not mode or mode == "silent":
        body = "No music track, no beat, no score, no discernible dialogue."
    else:
        body = f"Audio mode: {mode}."
        if notes:
            body += f" {notes}"
        else:
            body += " TODO — add the specific audio direction; this section is not optional."
    return "AUDIO\n" + body


def section_positive_constraints(spec: ShotSpec) -> str:
    """Restate the must-holds as affirmatives, per the published house style.

    The grammar calls these POSITIVE CONSTRAINTS rather than negatives: the same rules are
    asserted twice, once as prohibitions and once as affirmative guarantees.
    """
    lines = [
        f"The finished shot holds {spec.fov_diagonal_deg:g}° diagonal field of view throughout.",
        f"The shot runs {spec.duration_s:g} seconds at {spec.aspect} in real time.",
        "Every performer keeps their specified position and orientation.",
        "The camera path is exactly as described above.",
    ]
    if "UNBROKEN" in spec.format_mode.upper():
        lines.append("The result is one continuous take with no cuts of any kind.")
    if spec.is_loop:
        lines.append(
            "The closing frame matches the opening frame so the clip can loop without a seam."
        )
    lines.append(
        "The look of the finished shot comes entirely from the supplied references, never "
        "from the blockout."
    )
    return "POSITIVE CONSTRAINTS\n" + "\n".join(f"- {line}" for line in lines)


# --------------------------------------------------------------------------------------


SECTION_ORDER = (
    section_scene_context,
    section_active_references,
    section_location_map,
    section_first_frame,
    section_format_mode,
    section_optics,
    section_camera,
    section_performance,
    section_action_timing,
    section_physics,
    section_lighting,
    section_audio,
    section_positive_constraints,
)


def build_prompt(spec: ShotSpec, refs: dict | None = None) -> str:
    blocks: list[str] = []
    for builder in SECTION_ORDER:
        if builder is section_active_references:
            blocks.append(builder(spec, refs))  # type: ignore[call-arg]
        else:
            blocks.append(builder(spec))  # type: ignore[call-arg]
    header = (
        f"# FINAL GENERATION PROMPT — {spec.shot_id}\n"
        f"# project: {spec.project}  ·  spec v{spec.version}\n"
        f"# generated from shot.json by make_prompt.py — regenerate, do not hand-edit\n"
        f"# sections: {len(blocks)} (the house grammar requires all of them; a missing\n"
        f"# section fails in a specific, predictable way)\n"
    )
    incomplete = [
        line
        for block in blocks
        for line in block.splitlines()
        if line.strip().startswith("TODO")
    ]
    footer = (
        "\n" + "-" * 78 + "\n"
        f"# REVIEW: {len(incomplete)} TODO marker(s) remain. Each one is a section the spec\n"
        "# does not yet supply detail for. Resolve them from a previz review before spending\n"
        "# credits — that is cheaper than discovering the gap in a generated take.\n"
    )
    return header + "\n\n" + "\n\n".join(blocks) + footer


# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a final-generation prompt from a shot spec.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--spec", required=True, help="path to shot.json")
    parser.add_argument(
        "--references", default="", help="path to references.json (the reference pack manifest)"
    )
    parser.add_argument("--out", default="", help="write the prompt here (default: stdout)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any TODO markers remain (use in automation)",
    )
    args = parser.parse_args(argv)

    try:
        spec = ShotSpec.load(args.spec)
    except SpecError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    refs = None
    if args.references:
        try:
            refs = json.loads(Path(args.references).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: cannot read references manifest: {exc}", file=sys.stderr)
            return 2

    prompt = build_prompt(spec, refs)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        todos = prompt.count("TODO")
        print(f"wrote {out}  ({len(prompt.split())} words, {todos} TODO marker(s))")
    else:
        print(prompt)

    if args.strict and "TODO" in prompt:
        print(
            f"ERROR: {prompt.count('TODO')} TODO marker(s) remain (--strict)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
