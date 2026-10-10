import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('C:/Users/Admin/Dropbox/YTMF/Amara_2026/Press_On')
out=Path('C:/Users/Admin/.codex/visualizations/2026/09/11/01a08fc7-2484-7c62-813b-c127140ea78d/boarding_geometry_review');out.mkdir(exist_ok=True)
result={}
for label,path,frame in [('original',root/'14_Station_Asset/PressOn_Platform9_Director_Cut_v13.blend',700),('interior',root/'15_Train_Interior_Asset/PressOn_Interior_Refined_v03.blend',40),('pilot',root/'Clip_Package_v2/02_VERSE1/seg15_boarding_threshold/tests/boarding_production_test_02/blender/Boarding_Door_Geometry_v01.blend',1)]:
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;s.frame_set(frame);items=[]
 for o in s.objects:
  if any(t in o.name.lower() for t in ['threshold','tread','platform','vestibule','carriage floor','car 1 floor','partition','director 7b','director 7c','boarding performer','internal glass']):
   if o.type=='MESH':
    pts=[o.matrix_world@Vector(p) for p in o.bound_box];bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]
   else:bounds=None
   items.append(dict(name=o.name,type=o.type,location=list(o.matrix_world.translation),dimensions=list(o.dimensions),bounds=bounds,lens=o.data.lens if o.type=='CAMERA' else None))
 result[label]=dict(source=str(path),frame=frame,objects=items)
(out/'source_audit.json').write_text(json.dumps(result,indent=2))
