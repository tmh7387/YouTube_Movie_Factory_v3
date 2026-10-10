import bpy,json
from pathlib import Path
from mathutils import Vector
out=Path('D:/App development/YouTube_Movie_Factory_v3/piazza_angles_review')
out.mkdir(exist_ok=True)
s=bpy.context.scene
s.render.engine='CYCLES'
s.cycles.samples=24
s.cycles.use_denoising=True
s.render.resolution_x=1280
s.render.resolution_y=720
s.render.resolution_percentage=100
views=[('01_original_master',(3.4,-4.5,1.8),(-.5,2.8,1.6),32),('02_center_frontal',(0,-7,1.7),(0,5,1.7),28),('03_cafe_side',(-3.8,-4,1.7),(1,5,1.7),28),('04_reverse',( -3,8,2.8),(0,-2,1.9),27),('05_elevated_overview',(0,-10,6.8),(0,3,1.3),25)]
for name,loc,target,lens in views:
 d=bpy.data.cameras.new(name);d.lens=lens
 c=bpy.data.objects.new(name,d);s.collection.objects.link(c)
 c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();s.camera=c
 s.render.filepath=str(out/(name+'.png'))
 bpy.ops.render.render(write_still=True)
(out/'camera_records.json').write_text(json.dumps(views,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Piazza_camera_review.blend'))
