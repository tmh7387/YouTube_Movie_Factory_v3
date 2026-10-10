import bpy
from pathlib import Path
from mathutils import Vector
out=Path('C:/Users/Admin/.codex/visualizations/2026/09/11/01a08fc7-2484-7c62-813b-c127140ea78d/boarding_geometry_review')
bpy.ops.wm.open_mainfile(filepath=str(out/'Original_Boarding_Review.blend'))
s=bpy.context.scene;s.frame_set(700)
for m in list(s.timeline_markers):s.timeline_markers.remove(m)
for root in list(s.objects):
 if root.name.startswith(('Boarding performer','Boarding luggage','Porter')):
  for o in [root]+list(root.children_recursive):o.animation_data_clear();o.hide_render=True
original=bpy.data.objects['DIRECTOR 7B | Interior arrival']
cam=bpy.data.objects.new('Step-down geometry review camera',original.data.copy());s.collection.objects.link(cam)
cam.location=original.matrix_world.translation.copy()
cam.rotation_euler=Vector((-1,0,0)).to_track_quat('-Z','Y').to_euler()
cam.data.lens=24;cam.data.shift_y=-0.28;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.cycles.device='CPU'
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath=str(out/'05_stepdown_frontal_reference.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Stepdown_Frontal_Review.blend'))
bpy.ops.render.render(write_still=True)
