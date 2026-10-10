"""Diagnostic: why does the loop seam not close?

Evaluates the scene at the first and last frame and reports the world-space camera position
and aim target, plus the local values of every animated object, so the disagreement can be
attributed to a specific channel rather than guessed at.
"""
import bpy
import json
import sys
from pathlib import Path

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(Path(args[0])))
scene = bpy.context.scene

def snapshot(frame: int) -> dict:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    cam = scene.camera
    target = None
    for c in cam.constraints:
        if c.type == "TRACK_TO" and c.target:
            target = c.target
            break
    data = {
        "frame": frame,
        "cam_matrix_translation": [round(v, 6) for v in cam.matrix_world.translation],
        "cam_local_location": [round(v, 6) for v in cam.location],
        "cam_world_rotation": [round(v, 6) for v in cam.matrix_world.to_euler()],
        "cam_parent": cam.parent.name if cam.parent else None,
    }
    if cam.parent:
        data["cam_parent_local"] = [round(v, 6) for v in cam.parent.location]
        data["cam_parent_matrix_translation"] = [
            round(v, 6) for v in cam.parent.matrix_world.translation
        ]
    if target:
        data["target_name"] = target.name
        data["target_world"] = [round(v, 6) for v in target.matrix_world.translation]
    data["objects"] = []
    for obj in scene.objects:
        if obj.type not in {"MESH", "EMPTY"}:
            continue
        if obj.name.startswith("SET_") and obj.name != "SET_floor_reference":
            continue
        data["objects"].append(
            {
                "name": obj.name,
                "world": [round(v, 5) for v in obj.matrix_world.translation],
            }
        )
    return data


first = snapshot(1)
last = snapshot(scene.frame_end)
print("SEAM_JSON=" + json.dumps({"first": first, "last": last}, indent=1))

print("DELTAS")
for key in ("cam_matrix_translation", "cam_local_location", "cam_world_rotation"):
    a, b = first.get(key), last.get(key)
    if a and b:
        print(f"  {key}: {[round(b[i]-a[i], 6) for i in range(len(a))]}")
if "cam_parent_local" in first and "cam_parent_local" in last:
    print("  cam_parent_local first:", first["cam_parent_local"])
    print("  cam_parent_local last :", last["cam_parent_local"])
fa = {o["name"]: o["world"] for o in first["objects"]}
la = {o["name"]: o["world"] for o in last["objects"]}
for name in sorted(set(fa) | set(la)):
    d = [round(la[name][i] - fa[name][i], 5) for i in range(3)] if name in fa and name in la else "n/a"
    print(f"  obj {name:<24} delta {d}")
