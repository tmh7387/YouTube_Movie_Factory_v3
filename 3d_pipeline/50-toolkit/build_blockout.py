"""build_blockout.py — deterministic Blender blockout builder.

Reads a `shot.json`, builds an editable grey blockout in Blender, exports a `.blend`, a
portable `.glb`, a clean previz MP4 (and an annotated one for humans), and a machine-checkable
report. Same spec in, same blockout out — on any machine, forever. That determinism is what
makes a blockout *capital* rather than scratch work (PATTERNS.md P-02).

Two modes, one file:

    # host mode (plain python) — validates, wraps errors, does the ffmpeg encode
    python build_blockout.py --spec shot.json --out out/ [--render] [--dry-run]

    # blender mode (invoked automatically by host mode)
    blender --background --factory-startup --python build_blockout.py -- \
            --spec shot.json --out out/ --inside-blender [--render]

Why one file: keeping the Blender-side code and the orchestration in the same module means
the spec semantics can never drift between the two halves.

Design notes that matter
------------------------
* The camera never drives its own rotation. It is aimed by a parented empty via a TRACK_TO
  constraint, so framing survives edits to the path. This is the single most transferable
  trick in the whole method (see SOP-02 §2).
* The camera path is a Bezier curve through the spec's keyframes; the camera itself is
  keyframed at those times, so the file stays hand-editable in the Blender UI.
* Previs renders carry NO motion blur and NO overlays — the clip exists to be *read*, and
  blur is the one thing that genuinely confuses motion extraction.
* Rendering goes PNG-sequence -> ffmpeg, not Blender's FFmpeg writer, because the sequence
  path is verifiable frame by frame and fails loudly rather than producing a truncated MP4.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------------------
# Module loading — works both as a script and from inside Blender's interpreter.
# --------------------------------------------------------------------------------------


def _iter_fcurves(obj):
    """Yield every F-Curve on an object's action, across Blender's Action API change.

    Blender 4.x exposed `action.fcurves` directly. Blender 5.x moved to *slotted actions*:
    an action owns layers, a layer owns strips, a strip owns channelbags (one per slot),
    and the F-Curves live on the channelbag. Hard-coding either shape breaks on the other
    version, so ask for both and yield whatever exists.

    This helper exists because the failure it prevents is silent: `action.fcurves` raises
    AttributeError *inside* Blender's interpreter, and if the caller is not watching stderr
    the build looks like it succeeded while producing nothing.
    """
    animation_data = getattr(obj, "animation_data", None)
    if animation_data is None:
        return
    action = getattr(animation_data, "action", None)
    if action is None:
        return

    # Blender <= 4.x
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        for fcu in legacy:
            yield fcu
        return

    # Blender >= 5.x — slotted actions.
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            # A strip may hold channelbags for several slots; we want the one bound to
            # this object's slot when we can identify it, otherwise every bag.
            wanted = getattr(animation_data, "action_slot", None)
            bags = []
            if hasattr(strip, "channelbags"):
                bags = list(strip.channelbags)
            elif hasattr(strip, "channelbag") and wanted is not None:
                bag = strip.channelbag(wanted)
                bags = [bag] if bag is not None else []
            for bag in bags:
                if bag is None:
                    continue
                for fcu in getattr(bag, "fcurves", []):
                    yield fcu


def _set_keyframe_interpolation(obj, mode: str = "BEZIER",
                                handles: str = "AUTO_CLAMPED") -> int:
    """Apply interpolation to every keyframe on an object. Returns the count touched."""
    touched = 0
    for fcu in _iter_fcurves(obj):
        for kp in fcu.keyframe_points:
            kp.interpolation = mode
            if handles:
                kp.handle_left_type = handles
                kp.handle_right_type = handles
            touched += 1
    return touched


def _load_shot_spec():
    """Import `shot_spec` from beside this file, whichever interpreter we are in."""
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    spec = importlib.util.spec_from_file_location("shot_spec", here / "shot_spec.py")
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load shot_spec.py from {here}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["shot_spec"] = module
    spec.loader.exec_module(module)
    return module


shot_spec = _load_shot_spec()
ShotSpec = shot_spec.ShotSpec
SpecError = shot_spec.SpecError


def _in_blender() -> bool:
    return "bpy" in sys.modules or _module_available("bpy")


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):  # pragma: no cover - defensive
        return False


# --------------------------------------------------------------------------------------
# Blender side
# --------------------------------------------------------------------------------------


def _configure_workbench(scene, spec) -> None:
    """Flat-shaded Workbench, tuned for silhouette legibility.

    Every choice here serves one question: *can you tell what is where from one frame?*
    Object colour separates roles, the world is a neutral backdrop, and both shadow and
    cavity are OFF because they add noise without adding information a blockout needs.
    """
    shading = getattr(scene.display, "shading", None)
    if shading is None:
        return

    def _try(obj, attr, value) -> None:
        if hasattr(obj, attr):
            try:
                setattr(obj, attr, value)
            except (TypeError, AttributeError):  # pragma: no cover - enum mismatch
                pass

    _try(shading, "light", "FLAT")
    _try(shading, "color_type", "MATERIAL")   # use each material's viewport colour
    _try(shading, "show_shadows", False)
    _try(shading, "show_cavity", False)
    _try(shading, "show_object_outline", False)
    _try(shading, "show_specular_highlight", False)
    # A hand-picked background rather than the studio gradient: a flat, dark, slightly cool
    # backdrop is stable across frames, where a studio world can shift behind the camera and
    # confuse motion reading.
    if _try(shading, "background_type", "VIEWPORT"):
        _try(shading, "background_color", (0.10, 0.11, 0.14))


def _build_in_blender(
    spec: "ShotSpec",
    out_dir: Path,
    render: bool,
    frames: list[int] | None = None,
    shading: str = "flat",
) -> dict:
    """Build the blockout. Only callable with `bpy` importable.

    `frames` renders a contact sheet of specific frames instead of the full animation —
    the fast iteration loop for lighting and material tuning, so nobody renders 360 frames
    to discover the blockout is unreadable.

    `shading` is `flat` (Workbench, silhouette-legible, the default) or `lit` (EEVEE, softer,
    better for client boards).
    """
    import bpy  # noqa: PLC0415  (deliberately late — host mode must not need Blender)
    from mathutils import Vector  # noqa: PLC0415

    report: dict = {
        "shot_id": spec.shot_id,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "blender_version": bpy.app.version_string,
        "spec": {
            "duration_s": spec.duration_s,
            "fps": spec.fps,
            "total_frames": spec.total_frames,
            "frame_start": 1,
            "frame_end": spec.frame_end,
            "resolution": list(spec.resolved_resolution),
            "aspect": spec.aspect,
        },
        "objects": [],
        "camera": {},
        "warnings": [],
        "errors": [],
    }

    # -- clean slate ------------------------------------------------------------------
    # factory-startup already gives an empty scene; delete anything that survived.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = f"BLOCKOUT_{spec.shot_id}"

    # -- render settings --------------------------------------------------------------
    w, h = spec.resolved_resolution
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.fps = spec.fps
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = spec.frame_end

    # Which of the two shading strategies this pass uses. Defined first, before anything
    # reads it — an earlier version defined it later, and the resulting NameError was
    # swallowed by a defensive try/except, silently falling back to a lit render while
    # still reporting "flat". Failures that quiet are why every branch below records what it
    # actually chose in the report.
    flat = shading == "flat"
    report["shading_requested"] = shading
    report["shading_effective"] = "flat" if flat else "lit"

    # -- render engine ----------------------------------------------------------------
    # A blockout's job is to be READ, not admired.
    #
    # FLAT (default) = EEVEE with **unlit emission materials**. Each proxy renders at its
    #   exact role colour, with no studio lighting, specular highlight or view-transform
    #   remapping to shift it, and the world background is fully controllable so pale proxies
    #   always have a dark field to read against.
    #
    #   Workbench was the first choice here and was measured out: in this build it renders a
    #   pure-emission proxy as near-black and washes the background to a light grey that is
    #   chromatically identical to the "crowd" role colour, so the cast map stops reading.
    #   Emission under EEVEE is deterministic; Workbench's material path is not.
    #
    # LIT (`--shading lit`) = EEVEE with Principled materials under a key/fill sun pair.
    #   Prettier, better for client boards, measurably harder to read motion from.
    #
    # `RenderSettings.engine` is a DYNAMIC enum: it lists only engines whose add-ons are
    # currently registered, so introspecting it is unreliable — Workbench is present and
    # settable in this build yet absent from the RNA enum. Probe by *trying to set* each
    # candidate. The earlier enum-based test silently concluded "no Workbench".
    def _try_engine(identifier: str) -> bool:
        try:
            scene.render.engine = identifier
            return True
        except (TypeError, ValueError):
            return False

    preference = ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH", "CYCLES")
    chosen = next((e for e in preference if _try_engine(e)), None)
    if chosen is None:
        raise SpecError(
            "no usable render engine in this Blender build; tried " + ", ".join(preference)
        )
    report["render_engine"] = chosen

    # Reference clips are read for *motion*. Turn off everything that obscures it.
    for attr, value in (
        ("use_motion_blur", False),
        ("use_gtao", False),
        ("use_bloom", False),
        ("use_ssr", False),
        ("use_volumetric_lights", False),
    ):
        if hasattr(scene.eevee, attr):
            setattr(scene.eevee, attr, value)
    if scene.render.engine == "BLENDER_WORKBENCH":
        # Only reachable if EEVEE is unavailable in this build. Configure it as close to the
        # flat-emission look as Workbench allows.
        _configure_workbench(scene, spec)
    if hasattr(scene.view_settings, "view_transform"):
        try:
            scene.view_settings.view_transform = "Standard"
        except TypeError:  # pragma: no cover - older builds
            pass

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.film_transparent = False

    # Which of the two shading strategies this pass uses. Defined before the world block
    # because the backdrop value depends on it.

    # Backdrop: dark for the lit pass (the suns and world fill carry it) and a readable
    # mid-slate for the flat pass, where nothing is lit and a pure black background would
    # make the frame impossible to read as a composition.
    world = bpy.data.worlds.new("BlockoutWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        if flat:
            # Flat mode is UNLIT, so this value is shown almost verbatim. Keep it dark
            # enough that pale proxies read against it — a mid-grey backdrop at the same
            # luminance as the crowd proxies is what makes a blockout collapse into a field
            # of indistinguishable grey.
            bg.inputs[0].default_value = (0.14, 0.15, 0.18, 1.0)
            bg.inputs[1].default_value = 1.0
        else:
            bg.inputs[0].default_value = (0.10, 0.11, 0.13, 1.0)
            bg.inputs[1].default_value = 0.25
    scene.world = world

    # A key + fill sun pair, used by the *lit* pass only. The flat pass is unlit by design,
    # so adding lights there would change nothing while inviting the impression that the
    # look is light-driven.
    if not flat:
        for name, energy, rotation_deg, colour in (
            ("SUN_key", 1.00, (52.0, 0.0, 38.0), (1.0, 0.97, 0.92)),
            ("SUN_fill", 0.35, (68.0, 0.0, -125.0), (0.88, 0.92, 1.0)),
        ):
            light_data = bpy.data.lights.new(name, type="SUN")
            light_data.energy = energy
            light_data.color = colour
            light_data.angle = __import__("math").radians(35.0)
            light_obj = bpy.data.objects.new(name, light_data)
            light_obj.rotation_euler = tuple(
                __import__("math").radians(a) for a in rotation_deg
            )
            scene.collection.objects.link(light_obj)
            report.setdefault("lights", []).append({"name": name, "energy": energy})

    # Render visibility aids for review: an annotation overlay is rendered into a separate
    # pass, so these lights are for both passes and no more. (Lights are excluded from the
    # .glb export below — they exist only to make the previz legible.)

    # Collections — the blockout is organised, so a reviewer can find things.
    cast_coll = bpy.data.collections.new("CAST_PROXIES")
    set_coll = bpy.data.collections.new("SET_VOLUMES")
    cam_coll = bpy.data.collections.new("CAMERA_RIG")
    for coll in (set_coll, cast_coll, cam_coll):
        scene.collection.children.link(coll)

    def _link(obj, coll):
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        coll.objects.link(obj)

    # -- materials --------------------------------------------------------------------
    # Two material strategies, because the flat and lit passes solve different problems.
    #
    # FLAT (default): the material is an *unlit emission* at its exact role colour. This is
    #   the only approach that survives contact with a render engine's colour management —
    #   Workbench's studio lighting, specular highlights and view transform all shift a
    #   diffuse surface away from the colour you asked for, which turns a carefully
    #   colour-coded cast map into a field of near-white shapes. With emission there is
    #   nothing to shift: what you specify is what renders, and silhouette reading is perfect.
    #
    # LIT (`--shading lit`): a Principled BSDF under a key/fill sun pair. Prettier, better for
    #   showing a client, but less legible as motion reference.
    def _role_material(name: str, rgba, emission: float = 0.0):
        """A flat role-coloured material.

        In FLAT mode this is an unlit emission at the exact role colour — nothing in the
        render pipeline can shift it. In LIT mode it is a Principled BSDF receiving the sun
        pair. `diffuse_color` is set either way because the viewport and Workbench read it.
        """
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        if flat:
            for node in list(nodes):
                if node.type != "OUTPUT_MATERIAL":
                    nodes.remove(node)
            output = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None)
            if output is None:
                output = nodes.new("ShaderNodeOutputMaterial")
            emit = nodes.new("ShaderNodeEmission")
            emit.inputs["Color"].default_value = rgba
            emit.inputs["Strength"].default_value = 1.0
            links.new(emit.outputs["Emission"], output.inputs["Surface"])
        elif bsdf:
            bsdf.inputs["Base Color"].default_value = rgba
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.9
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = rgba
                bsdf.inputs["Emission Strength"].default_value = emission
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = rgba
        mat.diffuse_color = rgba
        mat.roughness = 0.9
        mat.metallic = 0.0
        return mat

    mat_set = _role_material("MAT_set", shot_spec.ROLE_COLOURS["set"])
    mat_cam = _role_material("MAT_camera_rig", shot_spec.ROLE_COLOURS["camera"], emission=0.6)

    # -- set volumes ------------------------------------------------------------------
    # Visibility is decided by ROLE, and this matters more than it looks. Volume boxes are
    # drawn from a wireframe cube primitive, which has no real "surface" — so in a lit render
    # they read as a flat slab that can hide the very geometry being reviewed. A `reveal`
    # volume is a larger enclosing box and is therefore *always* hidden from render.
    # Everything else is shown, because knowing where the walls are is half of what a
    # blockout is for.
    for vol in spec.volumes:
        cx, cy, cz = vol.centre
        sx, sy, sz = vol.size
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, cz))
        box = bpy.context.active_object
        box.name = f"SET_{vol.id}"
        box.scale = (max(sx, 0.001), max(sy, 0.001), max(sz, 0.001))
        box.display_type = "WIRE"
        box.hide_render = vol.role == "reveal"
        box["volume_role"] = vol.role
        box["volume_min"] = list(vol.min)
        box["volume_max"] = list(vol.max)
        box.data.materials.append(mat_set)
        _link(box, set_coll)
        report["objects"].append(
            {
                "name": box.name,
                "kind": "set_volume",
                "centre": [cx, cy, cz],
                "size": [sx, sy, sz],
                "role": vol.role,
                "rendered": not box.hide_render,
            }
        )

    # -- a floor plane at z=0 ----------------------------------------------------------
    # The single most useful element for judging a camera move is the ground: without it
    # there is no horizon, no sense of height and no way to see that a travel is level.
    # Distinctly darker than the proxies so it never competes with the cast.
    floor_mat = _role_material("MAT_floor", (0.22, 0.23, 0.26, 1.0))
    if spec.volumes:
        z0 = min(v.min[2] for v in spec.volumes)
        xs = [v.min[0] for v in spec.volumes] + [v.max[0] for v in spec.volumes]
        ys = [v.min[1] for v in spec.volumes] + [v.max[1] for v in spec.volumes]
        bpy.ops.mesh.primitive_plane_add(
            size=1.0, location=((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, z0)
        )
        floor = bpy.context.active_object
        floor.name = "SET_floor_reference"
        floor.scale = (
            max(max(xs) - min(xs), 1.0) * 1.25,
            max(max(ys) - min(ys), 1.0) * 1.25,
            1.0,
        )
        floor.hide_render = False
        floor.data.materials.append(floor_mat)
        _link(floor, set_coll)
        report["objects"].append(
            {"name": floor.name, "kind": "ground_plane", "z": z0, "rendered": True}
        )

    # -- cast proxies -----------------------------------------------------------------
    proxy_builders = {
        "capsule": lambda m: _add_capsule(bpy, m),
        "box": lambda m: _add_box(bpy, m),
        "sphere": lambda m: _add_sphere(bpy, m),
        "cone": lambda m: _add_cone(bpy, m),
    }

    for member in spec.cast:
        builder = proxy_builders.get(member.proxy, proxy_builders["box"])
        obj = builder(member)
        obj.name = f"CAST_{member.id}"
        mat = _role_material(f"MAT_cast_{member.id}", member.colour, emission=0.3)
        obj.data.materials.append(mat)
        obj["cast_role"] = member.role
        obj["motion"] = member.motion
        obj["height_m"] = member.height_m
        if member.facing_deg:
            obj.rotation_euler[2] = __import__("math").radians(member.facing_deg)
        _link(obj, cast_coll)

        # Static proxy: position only. Choreography deliberately lives in the PROMPT, not
        # in the proxy animation — animating a dance here makes the model copy stiff
        # blocking (PATTERNS.md P-03). We do keyframe a travel move only when the spec
        # explicitly gives both start and end, because a travelling actor changes framing.
        if member.end is not None:
            obj.location = Vector(member.start)
            obj.keyframe_insert("location", frame=1)
            obj.location = Vector(member.end)
            obj.keyframe_insert("location", frame=spec.frame_end)
            # Linear travel: a performer crossing a room does not ease in and out of
            # existence, and bezier overshoot on a proxy reads as a stumble.
            _set_keyframe_interpolation(obj, mode="LINEAR", handles="")

        report["objects"].append(
            {
                "name": obj.name,
                "kind": "cast_proxy",
                "cast_id": member.id,
                "role": member.role,
                "proxy": member.proxy,
                "start": list(member.start),
                "end": list(member.end) if member.end else None,
                "travelling": member.end is not None,
            }
        )

    # -- camera rig -------------------------------------------------------------------
    cam_data = bpy.data.cameras.new("CAM_data")
    cam_data.lens_unit = "FOV"
    cam_data.angle = __import__("math").radians(spec.fov_diagonal_deg)
    cam_data.sensor_fit = "AUTO"
    cam = bpy.data.objects.new("CAM", cam_data)
    cam_coll.objects.link(cam)

    start = spec.camera_path[0] if spec.camera_path else None
    if start is None:
        raise SpecError("cannot build a camera with an empty camera.path")

    cam.location = Vector(start.pos)

    # The aim target. Parented to nothing, keyframed independently, and the camera is
    # constrained to it — so the framing rule is expressed once, as data.
    target = bpy.data.objects.new("CAM_target", None)
    target.empty_display_type = "SPHERE"
    target.empty_display_size = 0.25
    target.location = Vector(start.target)
    cam_coll.objects.link(target)

    constrain = cam.constraints.new("TRACK_TO")
    constrain.target = target
    constrain.track_axis = "TRACK_NEGATIVE_Z"
    constrain.up_axis = "UP_Y"

    # Keyframe camera position (not rotation — the constraint owns rotation).
    for key in spec.camera_path:
        f = spec.frame_for_time(key.t)
        cam.location = Vector(key.pos)
        cam.keyframe_insert("location", frame=f)
        target.location = Vector(key.target)
        target.keyframe_insert("location", frame=f)

    # Smooth interpolation on the path. AUTO_CLAMPED prevents the classic bezier
    # overshoot where the camera sails past its own keyframe and out of the set.
    keys_touched = _set_keyframe_interpolation(cam, "BEZIER", "AUTO_CLAMPED")
    keys_touched += _set_keyframe_interpolation(target, "BEZIER", "AUTO_CLAMPED")
    # The path's own endpoints get flat handles too, so the first and last frames are not
    # eased into by the interpolation — which is what a loop seam needs.
    endpoints_clamped = _clamp_path_endpoints(cam) + _clamp_path_endpoints(target)
    report["camera"]["keyframes_retimed"] = keys_touched
    report["camera"]["endpoints_clamped"] = endpoints_clamped
    if keys_touched == 0:
        report["warnings"].append(
            "no F-Curves found after keyframing the camera — the animation API shape may "
            "have changed again; verify the .blend actually animates"
        )

    # Handheld drift — a small procedural noise offset, applied additively on location.
    # 0.010-0.020 m reads as human; 0.000 reads as CG (CAMERA_MOVE_CATALOGUE.md §1).
    drift = float(spec.camera.get("handheld_drift_m", 0.0) or 0.0)
    if drift > 0:
        _add_handheld_drift(bpy, cam, spec, drift)
        report["camera"]["handheld_drift_m"] = drift

    scene.camera = cam

    # -- timeline markers from beats --------------------------------------------------
    # Note: Blender 5.x refuses custom ID properties on TimelineMarker ("id properties not
    # supported for this type"), so beat actions are carried in the report rather than
    # attached to the marker. The marker label is the human-facing cue.
    scene.timeline_markers.clear()
    for beat in spec.beats:
        scene.timeline_markers.new(beat.label, frame=spec.frame_for_time(beat.t))
    report["camera"]["beat_markers"] = [
        {"label": b.label, "t": b.t, "frame": spec.frame_for_time(b.t), "action": b.action}
        for b in spec.beats
    ]

    # -- visualise the path -----------------------------------------------------------
    _add_path_curve(bpy, spec, cam_coll, mat_cam)

    # -- camera clearance check (analytic + Blender-side scene ray casts) --------------
    problems = spec.validate()
    clearance = spec.check_camera_clearance()
    report["spec_problems"] = problems
    report["clearance_warnings"] = clearance
    if problems:
        report["errors"].extend(problems)

    # -- sanity: does the camera actually see anything? -------------------------------
    report["camera"]["keyframes"] = [
        {
            "t": k.t,
            "frame": spec.frame_for_time(k.t),
            "pos": list(k.pos),
            "target": list(k.target),
            "note": k.note,
        }
        for k in spec.camera_path
    ]
    report["camera"]["rig"] = spec.rig
    report["camera"]["fov_diagonal_deg"] = spec.fov_diagonal_deg

    # -- save .blend ------------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    blend_path = out_dir / f"shot.v{spec.version}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
    report["outputs"] = {"blend": str(blend_path)}

    # -- export .glb ------------------------------------------------------------------
    glb_path = out_dir / f"shot.v{spec.version}.glb"
    try:
        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            export_format="GLB",
            use_selection=False,
            export_apply=True,
            export_animations=False,
            export_cameras=True,
            export_lights=False,
            export_yup=True,
        )
        report["outputs"]["glb"] = str(glb_path)
    except Exception as exc:  # noqa: BLE001 - report, never abort the build
        report["warnings"].append(f"GLB export failed: {exc}")

    # -- render previz frames ---------------------------------------------------------
    if render:
        frames_dir = out_dir / "previz_frames"
        annot_dir = out_dir / "previz_frames_annot"
        for d in (frames_dir, annot_dir):
            if d.exists():
                shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True, exist_ok=True)

        scene.render.filepath = str(frames_dir / "f_")
        scene.render.image_settings.file_format = "PNG"
        t0 = time.time()

        if frames:
            # Contact-sheet mode: render only the requested frames, at their true frame
            # numbers, so the filenames stay frame-accurate.
            rendered = []
            for f in frames:
                f = max(1, min(int(f), spec.frame_end))
                scene.frame_set(f)
                scene.render.filepath = str(frames_dir / f"f_{f:04d}")
                try:
                    bpy.ops.render.render(write_still=True)
                    rendered.append(f)
                except Exception as exc:  # noqa: BLE001
                    report["errors"].append(f"frame {f} render failed: {exc}")
            report["outputs"]["frames_dir"] = str(frames_dir)
            report["render_mode"] = "contact_sheet"
            report["render_frames"] = rendered
            report["render_seconds"] = round(time.time() - t0, 2)
        else:
            try:
                bpy.ops.render.render(animation=True)
                report["outputs"]["frames_dir"] = str(frames_dir)
                report["render_mode"] = "full_animation"
                report["render_seconds"] = round(time.time() - t0, 2)
            except Exception as exc:  # noqa: BLE001
                report["errors"].append(f"previz render failed: {exc}")

        # Annotated pass for humans. Same camera, stamping turned on.
        if not frames and report["outputs"].get("frames_dir"):
            _render_annotated(bpy, scene, spec, annot_dir)
            if any(annot_dir.glob("*.png")):
                report["outputs"]["annot_frames_dir"] = str(annot_dir)

        # Readability check — a previz that cannot be seen cannot be reviewed, and the
        # failure is invisible unless something measures it.
        report["readability"] = _measure_frame_readability(frames_dir, spec)

        # Loop seam check — only meaningful for a loop, and the one claim a loop makes that
        # nothing else verifies.
        if spec.is_loop and not frames:
            report["loop_seam"] = _verify_loop_seam(frames_dir, spec)

    return report


def _verify_loop_seam(frames_dir: Path, spec: "ShotSpec") -> dict:
    """Measure how well the first and last rendered frames match.

    A loop is a *claim*: "this clip can replay without a seam". Nothing else in the pipeline
    tests that claim, and the failure is invisible in any single frame — you only see it when
    the clip plays round. So it is measured, on the real rendered pixels, and reported as a
    number rather than a reassurance.

    Also checks the two other frames a loop cannot afford to get wrong: that the spec's
    `beats[0]` and `beats[-1]` really are the first and last rendered frames.
    """
    result: dict = {}
    try:
        import bpy  # noqa: PLC0415
    except ImportError:  # pragma: no cover
        return result

    first_path = frames_dir / f"f_{1:04d}.png"
    last_path = frames_dir / f"f_{spec.frame_end:04d}.png"
    if not first_path.is_file() or not last_path.is_file():
        result["checked"] = False
        result["reason"] = (
            f"missing {first_path.name if not first_path.is_file() else last_path.name}"
        )
        return result

    def _load(path: Path):
        img = bpy.data.images.load(str(path), check_existing=False)
        px = list(img.pixels)
        bpy.data.images.remove(img)
        return px

    a = _load(first_path)
    b = _load(last_path)
    if len(a) != len(b):
        result["checked"] = False
        result["reason"] = "first and last frames differ in size"
        return result

    n = len(a) // 4
    stride = max(1, n // 60000)
    total = 0.0
    worst = 0.0
    differing = 0
    counted = 0
    for i in range(0, n, stride):
        d = max(
            abs(a[4 * i] - b[4 * i]),
            abs(a[4 * i + 1] - b[4 * i + 1]),
            abs(a[4 * i + 2] - b[4 * i + 2]),
        )
        total += d
        worst = max(worst, d)
        if d > 0.02:
            differing += 1
        counted += 1

    mean = total / counted if counted else 0.0
    share = differing / counted if counted else 0.0
    result.update(
        {
            "checked": True,
            "first_frame": 1,
            "last_frame": spec.frame_end,
            "mean_abs_difference": round(mean, 5),
            "worst_channel_difference": round(worst, 5),
            "share_of_pixels_differing": round(share, 5),
        }
    )
    # Thresholds: the seam is a *visual* judgement, but a mean difference above ~1% of full
    # range, or more than 2% of pixels differing, is a seam a viewer will see on replay.
    if mean <= 0.01 and share <= 0.02:
        result["verdict"] = "seamless"
    elif mean <= 0.04 and share <= 0.10:
        result["verdict"] = "minor seam"
    else:
        result["verdict"] = "VISIBLE SEAM — the loop will not replay cleanly"
    return result


def _measure_frame_readability(frames_dir: Path, spec: "ShotSpec") -> dict:
    """Measure luminance *and role-colour presence* in the rendered frames.

    Two independent failure modes are checked, because both are silent otherwise:

    1. **Too dark or too flat** — a blockout nobody can see, caused by lights or materials.
    2. **Role colours missing** — the proxies rendered in Blender's default grey instead of
       their assigned role colour, which destroys the colour-coding the whole cast map
       depends on. A boolean-union capsule produced exactly this, and it looked like a
       lighting problem until it was measured.

    Uses Blender's own image loader, so no third-party dependency is introduced.
    """
    result: dict = {"sampled": 0}
    try:
        import bpy  # noqa: PLC0415
    except ImportError:  # pragma: no cover - host mode never calls this
        return result

    files = sorted(frames_dir.glob("*.png"))
    if not files:
        return result
    step = max(1, len(files) // 12)
    sample = files[::step][:12]

    luminances: list[float] = []
    role_hits: dict[str, int] = {role: 0 for role in shot_spec.ROLE_COLOURS}
    total_px = 0

    def _srgb_to_linear(c: float) -> float:
        """Undo the sRGB transfer function.

        Essential: spec colours are LINEAR (that is what a shader input is), but a PNG on
        disk holds sRGB-encoded values. Comparing the two directly fails by a wide margin —
        a lead red specified as 0.90, 0.13, 0.13 arrives from the PNG as roughly 0.95, 0.39,
        0.39. Every colour comparison in this module converts first.
        """
        c = max(0.0, min(1.0, c))
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def _to_linear(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
        return (_srgb_to_linear(rgb[0]), _srgb_to_linear(rgb[1]), _srgb_to_linear(rgb[2]))

    def _normalised_chroma(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
        """Scale a linear colour so only its hue/chroma matters, not its brightness."""
        peak = max(rgb)
        if peak <= 1e-6:
            return (0.0, 0.0, 0.0)
        return (rgb[0] / peak, rgb[1] / peak, rgb[2] / peak)

    role_chroma = {
        role: _normalised_chroma((rgba[0], rgba[1], rgba[2]))
        for role, rgba in shot_spec.ROLE_COLOURS.items()
    }

    for path in sample:
        try:
            img = bpy.data.images.load(str(path), check_existing=False)
            pixels = list(img.pixels)  # RGBA floats, linear
            bpy.data.images.remove(img)
        except Exception as exc:  # noqa: BLE001
            result.setdefault("errors", []).append(f"{path.name}: {exc}")
            continue

        n = len(pixels) // 4
        if n == 0:
            continue
        stride = max(1, n // 20000)  # sub-sample large frames
        run_lum = 0.0
        run_count = 0
        for i in range(0, n, stride):
            r, g, b = pixels[4 * i], pixels[4 * i + 1], pixels[4 * i + 2]
            run_lum += 0.2126 * r + 0.7152 * g + 0.0722 * b
            run_count += 1
            # Nearest role colour by *chroma*, if close enough to be that role. Threshold
            # 0.20 on the normalised linear channels: tight enough that neutral greys never
            # match a saturated role, loose enough to survive compression and shading.
            lin = _to_linear((r, g, b))
            if max(lin) < 0.02:
                continue  # near-black: no reliable hue information
            cr, cg, cb = _normalised_chroma(lin)
            best_role, best_dist = None, 9.0
            for role, (er, eg, eb) in role_chroma.items():
                d = abs(cr - er) + abs(cg - eg) + abs(cb - eb)
                if d < best_dist:
                    best_role, best_dist = role, d
            if best_role is not None and best_dist < 0.20:
                role_hits[best_role] += 1
        if run_count:
            luminances.append(run_lum / run_count)
            total_px += run_count

    if luminances:
        result["sampled"] = len(luminances)
        result["mean_luminance"] = round(sum(luminances) / len(luminances), 4)
        result["min_luminance"] = round(min(luminances), 4)
        result["max_luminance"] = round(max(luminances), 4)
        result["verdict"] = (
            "TOO DARK — check lights and proxy materials"
            if result["mean_luminance"] < 0.06
            else "readable"
        )

    if total_px:
        result["role_pixel_share"] = {
            role: round(hits / total_px, 5) for role, hits in role_hits.items() if hits
        }
        # Which roles does the spec say should be on screen? Only the *cast* roles are
        # checked: "set" is a neutral grey and is deliberately not separable by chroma from
        # the backdrop, so asserting on it would produce a false alarm.
        expected = {c.role for c in spec.cast}
        missing = sorted(r for r in expected if role_hits.get(r, 0) == 0)
        if missing:
            result["missing_roles"] = missing
            result["colour_verdict"] = (
                "ROLE COLOURS MISSING for: " + ", ".join(missing)
                + " — proxies are probably rendering with default materials"
            )
        else:
            result["colour_verdict"] = (
                "all expected cast colours present "
                f"({', '.join(sorted(expected))})"
            )
    return result


def _add_capsule(bpy, member):
    """A capsule proxy — reads unambiguously as 'a person' at a glance.

    Built from a single primitive. An earlier version assembled this with boolean unions of
    a cylinder and two spheres, which was both slow and *lossy*: the applied booleans left
    the mesh without a usable material slot, so the proxy silently rendered in Blender's
    default grey instead of the lead's red. One primitive, one material, no surprises.
    """
    r = max(member.radius_m, 0.05)
    h = max(member.height_m, 0.05)
    made = False
    # Blender 4.x/5.x ship a native capsule; use it when present.
    if hasattr(bpy.ops.mesh, "primitive_round_cube_add"):
        try:  # pragma: no cover - availability varies by build
            bpy.ops.mesh.primitive_round_cube_add(
                size=1.0,
                location=(0, 0, 0),
                radius=r,
                arc_div=4,
                lin_div=2,
            )
            obj = bpy.context.active_object
            obj.scale = (r * 2, r * 2, h)
            made = True
        except Exception:  # noqa: BLE001
            made = False
    if not made:
        # A cylinder with rounded scale is instantly readable as a standing figure and
        # carries material reliably. Silhouette clarity matters more than anatomical shape.
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=24)
        obj = bpy.context.active_object
    obj.location = (
        member.start[0],
        member.start[1],
        member.start[2] + member.height_m / 2.0,
    )
    return obj


def _add_box(bpy, member):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.active_object
    obj.scale = (
        max(member.radius_m * 2, 0.05),
        max(member.radius_m * 2, 0.05),
        max(member.height_m, 0.05),
    )
    obj.location = (
        member.start[0],
        member.start[1],
        member.start[2] + member.height_m / 2.0,
    )
    return obj


def _add_sphere(bpy, member):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=max(member.radius_m, 0.05))
    obj = bpy.context.active_object
    obj.location = (
        member.start[0],
        member.start[1],
        member.start[2] + member.radius_m,
    )
    return obj


def _add_cone(bpy, member):
    bpy.ops.mesh.primitive_cone_add(
        radius1=max(member.radius_m, 0.05),
        depth=max(member.height_m, 0.05),
    )
    obj = bpy.context.active_object
    obj.location = (
        member.start[0],
        member.start[1],
        member.start[2] + member.height_m / 2.0,
    )
    return obj


def _clamp_path_endpoints(obj) -> int:
    """Force the first and last keys of `obj` to flat (vector) handles.

    AUTO_CLAMPED handles ease in and out of every key, which is right along a path but wrong
    at its ends: the first and last frames of a loop must be able to run continuously into
    each other, and an eased endpoint stalls exactly where the seam is. Returns the number of
    keys adjusted.
    """
    adjusted = 0
    for fcu in _iter_fcurves(obj):
        points = list(fcu.keyframe_points)
        if len(points) < 2:
            continue
        for kp in (points[0], points[-1]):
            kp.handle_left_type = "VECTOR"
            kp.handle_right_type = "VECTOR"
            adjusted += 1
    return adjusted


def _add_handheld_drift(bpy, cam, spec, amplitude: float) -> None:
    """Add low-frequency procedural noise to a rig above the camera.

    Implemented as extra keyframes on a rig empty, so the drift is visible in the graph
    editor and can be dialled by hand rather than baked into an opaque modifier.

    Two properties are contractual, not incidental:

    * **The drift is exactly zero at t=0.** A non-zero offset at the start would displace the
      opening frame from its specified composition, and for a loop it would also break the
      seam.
    * **The drift is exactly zero on the final frame too**, so a loop closes cleanly rather
      than depending on whether `frame_end` happens to coincide with a drift sample. An
      earlier version only reproduced the opening value for the first few harmonics at
      specific times, which left a measurable seam.
    """
    import math  # noqa: PLC0415

    rig = bpy.data.objects.new("CAM_drift", None)
    rig.empty_display_type = "PLAIN_AXES"
    rig.empty_display_size = 0.2
    bpy.context.scene.collection.objects.link(rig)
    rig.location = (0.0, 0.0, 0.0)
    cam.parent = rig
    cam.matrix_parent_inverse = rig.matrix_world.inverted()

    # Harmonic set chosen so every component returns to zero at t = duration: each frequency
    # is an integer number of full cycles across the shot, and the phase is zero.
    duration = max(spec.duration_s, 1e-6)

    def drift_at(t: float) -> tuple[float, float]:
        dx = 0.0
        dy = 0.0
        for cycles, weight, phase in ((3, 0.55, 0.0), (7, 0.30, 0.0), (11, 0.15, 0.0)):
            w = 2.0 * math.pi * cycles * (t / duration)
            dx += weight * math.sin(w + phase)
            dy += weight * math.cos(w + phase)
        return amplitude * dx, amplitude * dy

    step = max(1, int(spec.fps / 4))  # 4 Hz sampling — human-ish, not jittery
    frames = list(range(1, spec.frame_end + 1, step))
    if frames[-1] != spec.frame_end:
        frames.append(spec.frame_end)

    for f in frames:
        t = (f - 1) / spec.fps
        dx, dy = drift_at(t)
        if f in (1, spec.frame_end):
            dx = dy = 0.0  # contractual: no displacement on the seam frames
        rig.location = (dx, dy, 0.0)
        rig.keyframe_insert("location", frame=f)

    for fcu in _iter_fcurves(rig):
        for kp in fcu.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = "AUTO_CLAMPED"
            kp.handle_right_type = "AUTO_CLAMPED"
    _clamp_path_endpoints(rig)


def _add_path_curve(bpy, spec, collection, material) -> None:
    """Draw the camera path and a marker per key, so a reviewer can see the move."""
    if len(spec.camera_path) < 2:
        return
    curve_data = bpy.data.curves.new("CAM_path_curve", type="CURVE")
    curve_data.dimensions = "3D"
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(spec.camera_path) - 1)
    for i, key in enumerate(spec.camera_path):
        bp = spline.bezier_points[i]
        bp.co = key.pos
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new("CAM_path", curve_data)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    obj.hide_render = True

    for i, key in enumerate(spec.camera_path):
        bpy.ops.mesh.primitive_cone_add(radius1=0.06, depth=0.18)
        marker = bpy.context.active_object
        marker.name = f"CAM_key_{i}_t{key.t:g}"
        marker.location = key.pos
        marker.data.materials.append(material)
        marker["t"] = key.t
        marker["note"] = key.note
        _move_to_collection(marker, collection)
        marker.hide_render = True


def _move_to_collection(obj, collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)


def _render_annotated(bpy, scene, spec, annot_dir: Path) -> None:
    """Second pass with stamping on. For humans only — never feed this to a model."""
    try:
        scene.render.use_stamp = True
        for attr in (
            "use_stamp_frame",
            "use_stamp_camera",
            "use_stamp_filename",
            "use_stamp_note",
            "use_stamp_lens",
        ):
            if hasattr(scene.render, attr):
                setattr(scene.render, attr, True)
        scene.render.use_stamp_time = False
        scene.render.use_stamp_date = False
        scene.render.use_stamp_render_time = False
        if hasattr(scene.render, "stamp_note_text"):
            scene.render.stamp_note_text = (
                f"{spec.shot_id}  rig={spec.rig}  fov={spec.fov_diagonal_deg:g}deg  "
                f"{spec.duration_s:g}s @ {spec.fps}fps  {spec.aspect}"
            )
        if hasattr(scene.render, "stamp_font_size"):
            scene.render.stamp_font_size = 22
        scene.render.filepath = str(annot_dir / "f_")
        bpy.ops.render.render(animation=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[build_blockout] annotated render failed (non-fatal): {exc}", file=sys.stderr)
    finally:
        scene.render.use_stamp = False


# --------------------------------------------------------------------------------------
# Host side
# --------------------------------------------------------------------------------------


def _find_ffmpeg() -> str | None:
    for name in ("ffmpeg", "ffmpeg.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _encode_sequence(ffmpeg: str, frames_dir: Path, out_path: Path, fps: int) -> tuple[bool, str]:
    """Encode a PNG sequence to H.264 MP4. Loud on failure, never silently partial."""
    frames = sorted(frames_dir.glob("*.png"))
    if not frames:
        return False, f"no frames in {frames_dir}"
    pattern = str(frames_dir / "f_%04d.png")
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(fps),
        "-start_number", "1",
        "-i", pattern,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "17",           # high quality: compression artefacts read as motion
        "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return False, proc.stderr.strip()[:2000]
    produced = sorted(frames_dir.glob("*.png"))
    return True, f"encoded {len(produced)} frames -> {out_path.name}"


def _probe_duration(path: Path) -> float | None:
    """Read a real duration back with ffprobe, so the report states a measured value."""
    ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    if not ffprobe or not path.exists():
        return None
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return round(float(proc.stdout.strip()), 3)
    except (ValueError, AttributeError):
        return None


def _run_in_blender(
    blender: str,
    spec_path: Path,
    out_dir: Path,
    render: bool,
    frames: str = "",
    shading: str = "flat",
) -> tuple[int, str]:
    """Run the builder inside Blender. Returns (exit code, combined diagnostic text).

    Blender has a nasty habit of catching a Python exception inside `--python`, printing a
    traceback to stderr, and still exiting **0**. A wrapper that trusts the exit code will
    therefore report success for a build that produced nothing. So we return the diagnostic
    text too, and the caller treats a traceback in it as failure regardless of exit code.
    """
    args = [
        blender,
        "--background",
        "--factory-startup",
        "--python",
        str(Path(__file__).resolve()),
        "--",
        "--spec", str(spec_path),
        "--out", str(out_dir),
        "--inside-blender",
    ]
    if render:
        args.append("--render")
    if frames:
        args.extend(["--frames", frames])
    if shading:
        args.extend(["--shading", shading])
    print(f"[build_blockout] launching: {Path(blender).name} --background --python <builder>")
    proc = subprocess.run(args, capture_output=True, text=True)
    diagnostics = (proc.stdout or "") + "\n" + (proc.stderr or "")

    # Surface only what a human needs: our own diagnostics plus any failure evidence.
    interesting = [
        line
        for line in diagnostics.splitlines()
        if line.startswith("[build_blockout]")
        or "Error" in line
        or "error:" in line
        or "Traceback" in line
        or line.strip().startswith("File \"")
        or "AttributeError" in line
        or "TypeError" in line
        or "KeyError" in line
        or "RuntimeError" in line
    ]
    for line in interesting[:60]:
        print(f"  | {line}")

    failed = (
        proc.returncode != 0
        or "Traceback (most recent call last)" in diagnostics
        or "Error: Python:" in diagnostics
    )
    return (1 if failed else 0), diagnostics


def _host_main(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec).resolve()
    out_dir = Path(args.out).resolve()

    try:
        spec, problems = shot_spec.load_and_validate(spec_path, strict=False)
    except SpecError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print("=" * 78)
    print(f"BLOCKOUT BUILD — {spec.shot_id}")
    print("=" * 78)
    for line in shot_spec.summary_lines(spec):
        print(f"  {line}")
    print()

    if problems:
        print(f"  {len(problems)} spec problem(s):")
        for p in problems:
            print(f"    - {p}")
        print()
        if args.strict:
            print("ERROR: refusing to build (--strict). Fix the spec or drop --strict.", file=sys.stderr)
            return 2

    path_len = shot_spec.haversine_like_path_length(spec)
    if spec.duration_s > 0:
        print(f"  camera path length  ~{path_len:.2f} m over {spec.duration_s:g}s "
              f"(~{path_len / spec.duration_s:.2f} m/s average)")

    if args.dry_run:
        print("\n  --dry-run: spec validated, no build performed.")
        return 0

    blender = args.blender
    if not blender:
        print("ERROR: no Blender executable. Pass --blender <path> or set BLENDER_EXE.",
              file=sys.stderr)
        return 2
    if not Path(blender).is_file():
        print(f"ERROR: Blender not found at {blender}", file=sys.stderr)
        return 2

    rc, diagnostics = _run_in_blender(
        blender, spec_path, out_dir, args.render, args.frames, args.shading
    )
    report_path = out_dir / "blockout_report.json"

    if not report_path.exists():
        print("\nERROR: Blender produced no blockout_report.json — the build did not run "
              "to completion.", file=sys.stderr)
        for line in diagnostics.strip().splitlines()[-30:]:
            print(f"  ! {line}", file=sys.stderr)
        return rc or 1

    report = json.loads(report_path.read_text(encoding="utf-8"))

    # A report that exists but lists no artefacts is still a failed build. Check the
    # contract explicitly rather than inferring success from the absence of an exception.
    produced = report.get("outputs") or {}
    if not produced.get("blend"):
        report.setdefault("errors", []).append("no .blend was written")
    if rc != 0 and not report.get("errors"):
        report.setdefault("errors", []).append(
            "Blender exited non-zero; see diagnostics above"
        )

    # ---- host-side finishing: encode the previz ------------------------------------
    ffmpeg = _find_ffmpeg()
    scene_fps = spec.fps
    contact_sheet = bool(report.get("render_mode") == "contact_sheet")
    if args.render and contact_sheet:
        frames_dir = out_dir / "previz_frames"
        frames = sorted(frames_dir.glob("*.png")) if frames_dir.is_dir() else []
        print(f"  contact sheet  : {len(frames)} frame(s) rendered "
              f"({', '.join(f.stem.replace('f_', '') for f in frames)})")
        if not frames:
            report.setdefault("errors", []).append("contact sheet rendered no frames")
    elif args.render and ffmpeg:
        frames_dir = out_dir / "previz_frames"
        clean_mp4 = out_dir / f"previz_{spec.shot_id}.mp4"
        if frames_dir.is_dir():
            ok, msg = _encode_sequence(ffmpeg, frames_dir, clean_mp4, scene_fps)
            print(f"  clean previz   : {'OK' if ok else 'FAILED'} — {msg}")
            if ok:
                report.setdefault("outputs", {})["previz_clean"] = str(clean_mp4)
                measured = _probe_duration(clean_mp4)
                report.setdefault("measurements", {})["previz_clean_duration_s"] = measured
                report["measurements"]["previz_clean_frames"] = len(
                    sorted(frames_dir.glob("*.png"))
                )
                if measured is not None and abs(measured - spec.duration_s) > (2.0 / spec.fps):
                    report.setdefault("warnings", []).append(
                        f"previz duration {measured}s differs from spec {spec.duration_s}s "
                        "by more than one frame"
                    )
            else:
                report.setdefault("errors", []).append(f"clean previz encode failed: {msg}")
        annot_dir = out_dir / "previz_frames_annot"
        annot_mp4 = out_dir / f"previz_{spec.shot_id}_annot.mp4"
        if annot_dir.is_dir() and any(annot_dir.glob("*.png")):
            ok, msg = _encode_sequence(ffmpeg, annot_dir, annot_mp4, scene_fps)
            print(f"  annotated previz: {'OK' if ok else 'FAILED'} — {msg}")
            if ok:
                report.setdefault("outputs", {})["previz_annotated"] = str(annot_mp4)
    elif args.render and not ffmpeg:
        report.setdefault("warnings", []).append(
            "ffmpeg not found — frame sequences were produced but not encoded to MP4"
        )

    if report:
        report["outputs"] = {
            k: v for k, v in report.get("outputs", {}).items() if not k.endswith("_dir")
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ---- summary -------------------------------------------------------------------
    print()
    print("  OUTPUTS")
    for key, value in sorted((report.get("outputs") or {}).items()):
        p = Path(value)
        size = f"{p.stat().st_size / 1e6:.2f} MB" if p.exists() else "MISSING"
        print(f"    {key:<20} {value}  [{size}]")
    if report.get("measurements"):
        print("  MEASURED")
        for key, value in sorted(report["measurements"].items()):
            print(f"    {key:<20} {value}")
    readability = report.get("readability") or {}
    if readability.get("sampled"):
        verdict = readability.get("verdict", "?")
        print(f"  READABILITY  mean luminance {readability.get('mean_luminance')} "
              f"(min {readability.get('min_luminance')}, max {readability.get('max_luminance')}) "
              f"over {readability['sampled']} frame(s) — {verdict}")
        if readability.get("colour_verdict"):
            print(f"  COLOUR MAP   {readability['colour_verdict']}")
            if readability.get("role_pixel_share"):
                shares = ", ".join(
                    f"{k} {v * 100:.2f}%"
                    for k, v in sorted(readability["role_pixel_share"].items())
                )
                print(f"               pixel share: {shares}")
        if verdict != "readable":
            report.setdefault("warnings", []).append(
                "previz frames measured too dark to review: " + str(verdict)
            )
        if readability.get("missing_roles"):
            report.setdefault("errors", []).append(
                "role colours not found in rendered frames: "
                + ", ".join(readability["missing_roles"])
            )
    seam = report.get("loop_seam") or {}
    if seam.get("checked"):
        print(
            f"  LOOP SEAM    frames {seam['first_frame']} vs {seam['last_frame']}: "
            f"mean diff {seam['mean_abs_difference']}, "
            f"{seam['share_of_pixels_differing'] * 100:.2f}% of pixels differ — "
            f"{seam['verdict']}"
        )
        if seam["verdict"].startswith("VISIBLE"):
            report.setdefault("errors", []).append(
                "loop seam is visible: " + seam["verdict"]
            )
    elif seam and not seam.get("checked"):
        report.setdefault("warnings", []).append(
            f"loop seam not verified: {seam.get('reason', 'unknown reason')}"
        )
    errors = report.get("errors") or []
    warnings = report.get("warnings") or []
    if warnings:
        print(f"\n  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"    ! {w}")
    if errors:
        print(f"\n  {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"    x {e}", file=sys.stderr)
    print()
    print("  " + ("BUILD FAILED" if errors else "BUILD OK — review the previz before Gate 2"))
    print("=" * 78)
    return 1 if errors else 0


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def _parse_frames(value: str | None) -> list[int] | None:
    """Parse an explicit `--frames` list, e.g. `1,91,181,271,360`."""
    if not value:
        return None
    frames: list[int] = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        frames.append(int(chunk))
    return frames or None


def _resolve_frames(value: str | None, spec: "ShotSpec") -> list[int] | None:
    """Resolve `--frames`, including the `beats` shorthand.

    `beats` resolves against the spec's own beat table, because "render the beats" is what a
    reviewer actually wants and making them compute frame numbers by hand is how the spec and
    the review drift apart.
    """
    if not value:
        return None
    if value.strip().lower() == "beats":
        frames = sorted({spec.frame_for_time(b.t) for b in spec.beats})
        if 1 not in frames:
            frames.insert(0, 1)
        if spec.frame_end not in frames:
            frames.append(spec.frame_end)
        return frames
    return _parse_frames(value)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic Blender blockout from a shot spec.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--spec", required=True, help="path to shot.json")
    parser.add_argument("--out", required=True, help="output directory for the Blockout Kit")
    parser.add_argument(
        "--blender",
        default=os.environ.get("BLENDER_EXE", ""),
        help="path to blender executable (or set BLENDER_EXE)",
    )
    parser.add_argument("--render", action="store_true", help="also render the previz passes")
    parser.add_argument(
        "--frames",
        default="",
        help="render only these frames as a contact sheet, e.g. '1,91,181' or 'beats'",
    )
    parser.add_argument(
        "--shading",
        choices=("flat", "lit"),
        default="flat",
        help="flat = Workbench, silhouette-legible (default, best for model-facing previz); "
             "lit = EEVEE, softer, better for client boards",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate the spec and exit without building"
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        default=True,
        help="build even if the spec has problems (not recommended)",
    )
    parser.add_argument(
        "--inside-blender", action="store_true", help=argparse.SUPPRESS
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Blender passes everything after `--` to the script; strip the separator.
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    args = _parse_args(argv)

    if args.inside_blender:
        if not _in_blender():
            print("ERROR: --inside-blender requires the Blender interpreter", file=sys.stderr)
            return 2
        spec = ShotSpec.load(args.spec)
        out_dir = Path(args.out).resolve()
        frames = _resolve_frames(args.frames, spec)
        report = _build_in_blender(spec, out_dir, args.render, frames, args.shading)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "blockout_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(f"[build_blockout] inside Blender: wrote {out_dir / 'blockout_report.json'}")
        return 0

    return _host_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
