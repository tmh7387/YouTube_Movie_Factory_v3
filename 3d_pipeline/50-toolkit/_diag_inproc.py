"""Diagnostic: run the real builder in-process, then render and inspect immediately.

Removes every intervening step (file save/load, subprocess, separate script) so that if the
materials and the render disagree, the cause must be inside the build itself.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

spec_path = HERE.parent / "examples" / "demo-infinite-loop" / "shots" / "SH010" / "shot.json"
out_dir = HERE / "_diag_out" / "inproc"
out_dir.mkdir(parents=True, exist_ok=True)

# Load the builder module
spec = importlib.util.spec_from_file_location("bb", HERE / "build_blockout.py")
bb = importlib.util.module_from_spec(spec)
sys.modules["bb"] = bb
spec.loader.exec_module(bb)

shot = bb.ShotSpec.load(spec_path)

import bpy

report = bb._build_in_blender(shot, out_dir, render=False, frames=None, shading="flat")
print("ENGINE:", report.get("render_engine"))
print("SHADING_REQ:", report.get("shading_requested"), "EFF:", report.get("shading_effective"))
print("WARNINGS:", report.get("warnings"))
print("MODULE_FILE:", bb.__file__)
scene = bpy.context.scene
sh = scene.display.shading
print("COLOR_TYPE:", getattr(sh, "color_type", "n/a"))
print("LIGHT:", getattr(sh, "light", "n/a"))
print("WORLD_BG:", [round(c, 3) for c in scene.world.node_tree.nodes["Background"].inputs[0].default_value])
print("VIEW_TRANSFORM:", scene.view_settings.view_transform)
print("ENGINE_ENUM_HAS_WORKBENCH:",
      "BLENDER_WORKBENCH" in {
          i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
      })

for obj in sorted(scene.objects, key=lambda o: o.name):
    if obj.type != "MESH":
        continue
    slots = [s.material.name if s.material else None for s in obj.material_slots]
    diffs = [
        [round(c, 3) for c in s.material.diffuse_color] if s.material else None
        for s in obj.material_slots
    ]
    print(f"OBJ {obj.name:<24} hide={obj.hide_render!s:<6} slots={slots} diffuse={diffs}")

# Render frame 1 in-process
scene.frame_set(1)
scene.render.filepath = str(out_dir / "inproc_frame")
scene.render.resolution_x = 320
scene.render.resolution_y = 180
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(str(out_dir / "inproc_frame.png"), check_existing=False)
px = list(img.pixels)
n = len(px) // 4
counts = {}
for k in range(0, n, 5):
    r, g, b = px[4 * k], px[4 * k + 1], px[4 * k + 2]
    key = f"{round(r,1)},{round(g,1)},{round(b,1)}"
    counts[key] = counts.get(key, 0) + 1
print("TOP_COLOURS:")
for k, v in sorted(counts.items(), key=lambda kv: -kv[1])[:8]:
    print(f"   {k}  {v/(n/5):.3f}")
print("RENDER_ENGINE_AFTER:", scene.render.engine)
