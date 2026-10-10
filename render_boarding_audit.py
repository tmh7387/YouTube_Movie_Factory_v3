import bpy,json
from pathlib import Path
from mathutils import Vector
out=Path('C:/Users/Admin/.codex/visualizations/2026/09/11/01a08fc7-2484-7c62-813b-c127140ea78d/boarding_geometry_review')
s=bpy.context.scene;s.frame_set(700)
for m in list(s.timeline_markers):s.timeline_markers.remove(m)
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.cycles.device='CPU';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
original=bpy.data.objects['DIRECTOR 7B | Interior arrival'];s.camera=original
s.render.filepath=str(out/'01_original_camera_scale.png');bpy.ops.render.render(write_still=True)
actor=bpy.data.objects['Boarding performer'];actor_parts=[actor]+list(actor.children_recursive)
dg=bpy.context.evaluated_depsgraph_get();actor_copies=[]
for o in actor_parts:
 if o.type=='MESH':
  e=o.evaluated_get(dg);c=bpy.data.objects.new('Scale check '+o.name,bpy.data.meshes.new_from_object(e));c.matrix_world=e.matrix_world.copy();actor_copies.append(c)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Original_Boarding_Review.blend'))
hidden=[]
roots=[o for o in s.objects if o.name.startswith(('Boarding performer','Boarding luggage','Porter'))]
targets=set(roots)
for o in roots:targets.update(o.children_recursive)
for o in targets:
 hidden.append((o,o.hide_render));o.animation_data_clear();o.hide_render=True
s.render.filepath=str(out/'02_original_camera_empty.png');bpy.ops.render.render(write_still=True)
# Review camera: same X/Y and lens as source, explicitly level at adult eye height.
cam=bpy.data.objects.new('REVIEW ONLY level eye-height camera',bpy.data.cameras.new('Review lens'));s.collection.objects.link(cam)
cam.location=(original.location.x,8.5,3.06);cam.rotation_euler=(Vector((-5,8.5,3.06))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=35;s.camera=cam
s.render.filepath=str(out/'03_level_frontal_review.png');bpy.ops.render.render(write_still=True)
section=bpy.data.scenes.new('Measured side cutaway');bpy.context.window.scene=section
def box(name,center,dims,color):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.dimensions=dims
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);o.data.materials.append(m)
box('Original platform slab cropped',(-2.55,8.5,.75),(1.9,1.1,.5),(.3,.4,.5))
box('Original platform coping',(-1.62,8.5,1.05),(.28,1.1,.1),(.65,.7,.75))
box('Original tread',(-1.97,8.5,1.17),(.72,1.1,.104),(.8,.5,.15))
box('Original threshold',(-1.36,8.5,1.41),(.4,1.1,.1),(.9,.75,.35))
box('Original carriage floor cropped',(0,8.5,1.35),(2.85,1.1,.15),(.45,.28,.16))
for c in actor_copies:section.collection.objects.link(c)
c=bpy.data.objects.new('Side orthographic',bpy.data.cameras.new('Section camera'));section.collection.objects.link(c);c.location=(-.7,2,1.8);c.rotation_euler=(Vector((-.7,8.5,1.8))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=5.8;section.camera=c
section.render.engine='BLENDER_WORKBENCH';section.display.shading.light='STUDIO';section.display.shading.color_type='MATERIAL';section.display.shading.show_shadows=True;section.display.shading.show_cavity=True
section.render.resolution_x=1280;section.render.resolution_y=720;section.render.resolution_percentage=100;section.render.image_settings.file_format='PNG';section.render.filepath=str(out/'04_measured_scale_section.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Boarding_Section_Review.blend'))
