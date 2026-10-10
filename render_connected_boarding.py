import bpy,json
from pathlib import Path
from mathutils import Vector
out=Path('C:/Users/Admin/.codex/visualizations/2026/09/11/01a08fc7-2484-7c62-813b-c127140ea78d/connected_boarding');out.mkdir(exist_ok=True)
s=bpy.context.scene;s.frame_set(40)
for o in s.objects:
 if any(t in o.name.lower() for t in ['amara','stand-in','clearance']):o.hide_render=True
for m in list(s.timeline_markers):s.timeline_markers.remove(m)
source='C:/Users/Admin/Dropbox/YTMF/Amara_2026/Press_On/14_Station_Asset/PressOn_Platform9_Director_Cut_v13.blend'
names=['01_Platforms_Tracks','02_Station_Facades','03_Roof_Glass_Iron','06_Platform_Furniture','08_Lighting']
with bpy.data.libraries.load(source,link=False) as (a,b):b.collections=[n for n in names if n in a.collections]
objects=set()
for col in b.collections:s.collection.children.link(col);objects.update(col.all_objects)
env=bpy.data.objects.new('Station registration',None);s.collection.objects.link(env);env.location=(0,-68.1,0)
for o in objects:
 if o.parent not in objects:o.parent=env
 if o.type=='FONT':o.hide_render=True
cam=bpy.data.objects.new('Connected boarding review',bpy.data.cameras.new('Connected boarding lens'));s.collection.objects.link(cam);s.camera=cam
cam.location=(1.15,.78,3.02);cam.rotation_euler=(Vector((-1.45,-.35,2.40))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=16
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.cycles.device='CPU'
s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(out/'Connected_Boarding_Guide.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Connected_Boarding_Guide.blend'))
bpy.ops.render.render(write_still=True)
