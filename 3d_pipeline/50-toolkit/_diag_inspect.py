"""Diagnostic: inspect the built blockout. Which objects carry which material?

Opens the .blend produced by build_blockout.py and reports, per object: the material slots,
each material's diffuse_color and node setup, and the object's effective display colour.
Then renders frame 181 with the project's own settings so the visual can be compared.
"""
import bpy
import json
import sys
from pathlib import Path

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
blend = Path(args[0])
out = Path(args[1])
out.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(blend))
scene = bpy.context.scene

report = {
    "engine": scene.render.engine,
    "color_type": getattr(scene.display.shading, "color_type", "n/a"),
    "light": getattr(scene.display.shading, "light", "n/a"),
    "view_transform": scene.view_settings.view_transform,
    "objects": [],
}

for obj in sorted(scene.objects, key=lambda o: o.name):
    if obj.type not in {"MESH", "CURVE"}:
        continue
    entry = {
        "name": obj.name,
        "hide_render": obj.hide_render,
        "display_type": obj.display_type,
        "slots": len(obj.material_slots),
        "materials": [],
    }
    for slot in obj.material_slots:
        mat = slot.material
        if mat is None:
            entry["materials"].append(None)
            continue
        nodes = [n.type for n in mat.node_tree.nodes] if mat.use_nodes else []
        has_emission = any(n.type == "EMISSION" for n in mat.node_tree.nodes) if mat.use_nodes else False
        entry["materials"].append(
            {
                "name": mat.name,
                "diffuse_color": [round(c, 3) for c in mat.diffuse_color],
                "use_nodes": mat.use_nodes,
                "nodes": nodes,
                "has_emission": has_emission,
            }
        )
    report["objects"].append(entry)

# Render the frame with the worst colour miss (181 by earlier measurement)
scene.frame_set(int(args[2]) if len(args) > 2 else 181)
scene.render.filepath = str(out / "inspect_frame")
bpy.ops.render.render(write_still=True)

# Sample the render
img = bpy.data.images.load(str(out / "inspect_frame.png"), check_existing=False)
px = list(img.pixels)
n = len(px) // 4
w, h = img.size
colours: dict[str, int] = {}
for k in range(0, n, 11):
    r, g, b = px[4 * k], px[4 * k + 1], px[4 * k + 2]
    key = f"{round(r, 1)},{round(g, 1)},{round(b, 1)}"
    colours[key] = colours.get(key, 0) + 1
top = sorted(colours.items(), key=lambda kv: -kv[1])[:10]
report["render_size"] = [w, h]
report["top_colours"] = [{"rgb": k, "share": round(v / (n / 11), 4)} for k, v in top]

print("INSPECT_JSON=" + json.dumps(report, indent=1))
(out / "inspect_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
