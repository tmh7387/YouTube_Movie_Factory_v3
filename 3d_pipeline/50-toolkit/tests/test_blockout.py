"""Regression tests for the blockout builder — run them inside Blender.

    blender --background --factory-startup --python 50-toolkit/tests/test_blockout.py

These are *contract* tests, not smoke tests. Each one asserts a property that has already
been broken once by a real, silent defect:

  * `test_flat_materials_are_unlit_emission` — guards the fix for materials rendering in
    Blender's default grey.
  * `test_flat_pass_has_no_lights` — guards against the flat pass quietly becoming a lit one.
  * `test_role_colours_reach_the_render` — guards the end-to-end colour path, measuring
    pixels rather than trusting the material list. This is the test that would have caught
    the "flat was silently EEVEE-lit" bug immediately.
  * `test_camera_tracks_an_independent_target` — guards the framing mechanism the whole
    method depends on (camera never drives its own rotation).
  * `test_engine_selection_is_dynamic` — guards against enum introspection, which wrongly
    reported Workbench as missing.

Run with no arguments. Exit code is non-zero if any test fails.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLKIT = HERE.parent
PIPELINE = TOOLKIT.parent
sys.path.insert(0, str(TOOLKIT))

# ---------------------------------------------------------------------------------------
# Minimal assertion harness. Deliberately not pytest: this runs inside Blender's bundled
# interpreter, which has no third-party packages, and adding a dependency here would mean
# the tests could not run in the one environment where the bugs actually live.
# ---------------------------------------------------------------------------------------

_RESULTS: list[tuple[str, bool, str]] = []


class Failure(AssertionError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise Failure(message)


def test(name: str):
    def decorator(fn):
        _RESULTS.append((name, None, fn))  # type: ignore[arg-type]
        return fn

    return decorator


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


bb = _load("build_blockout", TOOLKIT / "build_blockout.py")
shot_spec = bb.shot_spec

DEMO_SPEC = PIPELINE / "examples" / "demo-infinite-loop" / "shots" / "SH010" / "shot.json"
OUT = TOOLKIT / "_test_out"


def _build(shading: str = "flat", render: bool = False):
    import bpy

    OUT.mkdir(parents=True, exist_ok=True)
    spec = bb.ShotSpec.load(DEMO_SPEC)
    report = bb._build_in_blender(spec, OUT, render=render, frames=None, shading=shading)
    return bpy, spec, report


def _render_frame(bpy, path: Path, frame: int = 1, width: int = 240, height: int = 135):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path.with_suffix(".png")


def _pixel_stats(png: Path):
    import bpy

    img = bpy.data.images.load(str(png), check_existing=False)
    px = list(img.pixels)
    bpy.data.images.remove(img)
    n = len(px) // 4
    return px, n


def _srgb_to_linear(c: float) -> float:
    """Undo the sRGB transfer function.

    A PNG holds sRGB-encoded values; a spec colour is a LINEAR shader input. Comparing them
    without converting is the mistake that made this test report "role colours missing" for a
    render that plainly showed them: lead red specified as 0.90, 0.13, 0.13 arrives from the
    PNG as approximately 0.95, 0.39, 0.39.
    """
    c = max(0.0, min(1.0, c))
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _to_linear(rgb):
    return tuple(_srgb_to_linear(v) for v in rgb)


def _chroma(rgb):
    """Normalised chroma of a LINEAR colour — hue identity without brightness."""
    peak = max(rgb)
    if peak <= 1e-6:
        return (0.0, 0.0, 0.0)
    return (rgb[0] / peak, rgb[1] / peak, rgb[2] / peak)


# ---------------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------------


@test("spec loads and validates cleanly")
def test_spec_validates():
    spec = bb.ShotSpec.load(DEMO_SPEC)
    problems = spec.validate()
    check(problems == [], f"demo spec should validate, got: {problems}")
    check(spec.total_frames == 360, f"expected 360 frames, got {spec.total_frames}")
    check(spec.frame_end == 360, f"expected frame_end 360, got {spec.frame_end}")
    check(spec.is_loop, "demo spec should be detected as a loop")
    check(spec.frame_for_time(0.0) == 1, "t=0 must map to frame 1")
    check(spec.frame_for_time(15.0) == 360, "t=duration must map to the last frame")


@test("flat materials are unlit emission")
def test_flat_materials_are_unlit_emission():
    import bpy

    _build("flat")
    cast = [o for o in bpy.context.scene.objects if o.name.startswith("CAST_")]
    check(bool(cast), "no CAST_ proxies were built")
    for obj in cast:
        mat = obj.material_slots[0].material if obj.material_slots else None
        check(mat is not None, f"{obj.name} has no material")
        node_types = {n.type for n in mat.node_tree.nodes}
        check(
            "EMISSION" in node_types,
            f"{obj.name} material {mat.name} is not unlit emission (has {node_types})",
        )
        check(
            "BSDF_PRINCIPLED" not in node_types,
            f"{obj.name} still carries a Principled BSDF in flat mode",
        )


@test("flat pass has no lights")
def test_flat_pass_has_no_lights():
    import bpy

    _build("flat")
    lights = [o.name for o in bpy.context.scene.objects if o.type == "LIGHT"]
    check(not lights, f"flat pass must be unlit but found lights: {lights}")


@test("lit pass does have lights and Principled materials")
def test_lit_pass_has_lights():
    import bpy

    _build("lit")
    lights = [o.name for o in bpy.context.scene.objects if o.type == "LIGHT"]
    check(bool(lights), "lit pass should create sun lights")
    cast = [o for o in bpy.context.scene.objects if o.name.startswith("CAST_")]
    mat = cast[0].material_slots[0].material
    node_types = {n.type for n in mat.node_tree.nodes}
    check("BSDF_PRINCIPLED" in node_types, "lit pass should use Principled materials")


@test("role colours reach the render")
def test_role_colours_reach_the_render():
    import bpy

    _build("flat")
    png = _render_frame(bpy, OUT / "colour_probe")
    px, n = _pixel_stats(png)

    wanted = {
        "lead": _chroma((0.90, 0.13, 0.13)),
        "prop": _chroma((0.20, 0.80, 0.45)),
        "crowd": _chroma((0.62, 0.62, 0.65)),
    }
    found = {role: 0 for role in wanted}
    best = {role: (9.0, None) for role in wanted}
    for k in range(0, n, 2):
        rgb = (px[4 * k], px[4 * k + 1], px[4 * k + 2])
        lin = _to_linear(rgb)
        if max(lin) < 0.02:
            continue
        c = _chroma(lin)
        for role, target in wanted.items():
            d = sum(abs(c[i] - target[i]) for i in range(3))
            if d < best[role][0]:
                best[role] = (d, tuple(round(v, 3) for v in rgb))
            if d < 0.20:
                found[role] += 1

    diagnostics = "; ".join(
        f"{role}: closest {best[role][1]} at chroma-distance {best[role][0]:.3f}, "
        f"{found[role]} px"
        for role in wanted
    )
    for role in ("lead", "prop"):
        check(
            found[role] > 0,
            f"role '{role}' never appeared in the rendered frame — its material is not "
            f"reaching the render. [{diagnostics}]",
        )


@test("set surround does not collide with a cast role colour")
def test_background_is_separable():
    """The worst colour collision in a blockout is a room whose walls match the crowd role.

    This spec's camera sits inside a set volume, so the top-left corner of the frame is the
    *set* material, not the world background — and a mid-grey set at the same chroma as the
    light-grey crowd role makes the cast map unreadable. Guards the fix that darkened the
    set role.
    """
    import bpy

    _build("flat")
    png = _render_frame(bpy, OUT / "bg_probe")
    px, n = _pixel_stats(png)
    corner = _to_linear((px[0], px[1], px[2]))
    crowd = _chroma((0.62, 0.62, 0.65))
    distance = sum(abs(_chroma(corner)[i] - crowd[i]) for i in range(3))
    check(
        distance > 0.10,
        f"the set surround as rendered {tuple(round(c, 3) for c in corner)} (linear) is "
        "chromatically indistinguishable from the 'crowd' role — the cast map will not read",
    )
    # It must also be clearly darker than the crowd, so luminance separates them too.
    check(
        max(corner) < 0.5,
        f"set surround luminance {max(corner):.3f} is too close to the crowd proxies — "
        "make the set role darker",
    )


@test("camera tracks an independent target")
def test_camera_tracks_an_independent_target():
    import bpy

    _build("flat")
    scene = bpy.context.scene
    cam = scene.camera
    check(cam is not None, "no scene camera")
    constraints = [c for c in cam.constraints if c.type == "TRACK_TO"]
    check(
        bool(constraints),
        "camera has no TRACK_TO constraint — framing will not survive path edits",
    )
    target = constraints[0].target
    check(target is not None, "camera TRACK_TO constraint has no target")
    check(
        target.name == "CAM_target",
        f"camera should track CAM_target, tracks {target.name}",
    )
    # The camera itself must carry position keyframes only, never rotation.
    paths = {fcu.data_path for fcu in bb._iter_fcurves(cam)}
    check(
        not any("rotation" in p for p in paths),
        f"camera should not animate its own rotation, found {sorted(paths)}",
    )
    check(
        any("location" in p for p in paths),
        f"camera has no location animation, found {sorted(paths)}",
    )


@test("beat markers are placed at the spec frame numbers")
def test_beat_markers():
    import bpy

    spec = bb.ShotSpec.load(DEMO_SPEC)
    _build("flat")
    markers = {m.name: m.frame for m in bpy.context.scene.timeline_markers}
    for beat in spec.beats:
        expected = spec.frame_for_time(beat.t)
        check(
            markers.get(beat.label) == expected,
            f"marker '{beat.label}' at {markers.get(beat.label)}, expected {expected}",
        )


@test("camera path clearance is reported")
def test_clearance_reported():
    spec = bb.ShotSpec.load(DEMO_SPEC)
    issues = spec.check_camera_clearance()
    check(issues == [], f"demo camera path leaves the set: {issues}")


@test("engine selection probes dynamically")
def test_engine_selection_is_dynamic():
    import bpy

    _build("flat")
    engine = bpy.context.scene.render.engine
    check(
        engine in {"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"},
        f"flat pass should use EEVEE (unlit emission), got {engine}",
    )


# ---------------------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------------------


def main() -> int:
    print("=" * 78)
    print("BLOCKOUT BUILDER — CONTRACT TESTS")
    print("=" * 78)
    passed = failed = 0
    for name, _, fn in _RESULTS:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}")
            print(f"        {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"  ok    {name}")
    print("-" * 78)
    print(f"  {passed} passed, {failed} failed, {len(_RESULTS)} total")
    print("=" * 78)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
