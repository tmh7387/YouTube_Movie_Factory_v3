import bpy, json
from pathlib import Path
from mathutils import Vector
out=Path('C:/Users/Admin/.codex/visualizations/2026/09/11/01a08fc7-2484-7c62-813b-c127140ea78d/empty_boarding_20260917')
out.mkdir(exist_ok=True)
s=bpy.context.scene
cam=s.camera
cam.location=(0,1.95,1.70)
cam.rotation_euler=(Vector((0,-3,1.70))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens=16
cam.data.sensor_width=36
cam.data.dof.use_dof=False
cam.name='Empty vestibule looking outward perpendicular'
s.render.resolution_x=1920
s.render.resolution_y=1080
s.render.resolution_percentage=100
s.render.engine='BLENDER_EEVEE'
s.render.image_settings.file_format='PNG'
s.render.filepath=str(out/'Empty_Boarding_Reverse_Guide.png')
s['reference_roles']='3D aperture and camera geometry; Train-door supplies door design; station photographs supply architecture and lighting.'
s['wardrobe_authority']='Not applicable: empty environment, no characters.'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Empty_Boarding_Reverse.blend'))
report={'source':'Boarding_Door_Geometry_v01.blend','camera':list(cam.location),'lens_mm':cam.data.lens,'opening_width_m':1.10,'opening_height_m':2.20,'threshold_m':0.55,'note':'Design dimensions from existing boarding test, not measured physical dimensions. Original older pilot used a different sill height.','objects':[{'name':o.name,'location':list(o.location),'dimensions':list(o.dimensions)} for o in s.objects if o.type=='MESH']}
(out/'geometry.json').write_text(json.dumps(report,indent=2))
bpy.ops.render.render(write_still=True)
