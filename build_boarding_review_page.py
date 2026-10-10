from pathlib import Path
import json,html
P=Path('C:/Users/Admin/.codex/visualizations/2026/09/11/01a08fc7-2484-7c62-813b-c127140ea78d/boarding_geometry_review')
def svg_start(title):return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#111b28"/><text x="30" y="40" fill="white" font-size="24">{title}</text>'
def rect(x,y,w,h,c):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" stroke="#abc"/>'
def text(x,y,t,c='white',size=18):return f'<text x="{x}" y="{y}" fill="{c}" font-size="{size}">{html.escape(t)}</text>'
# Side section uses measured object bounds, not generated-image perspective.
a=json.loads((P/'source_audit.json').read_text())
o={x['name']:x for x in a['original']['objects']}
S=svg_start('SIDE SECTION — measured original scene, metres')
X=lambda v:100+(v+3.5)*160
Z=lambda v:470-(v-.8)*450
for name,col in [('PLATFORM_9 | entire 124m substrate','#63738b'),('Platform coping edge','#a7b2c2'),('REV_Boarding step anti-slip tread','#e2a84d'),('Door threshold','#e2cd80'),('Car 1 floor','#956c48')]:
 b=o[name]['bounds'];x0=max(-3.5,b[0][0]);x1=min(1.5,b[0][1]);z0=max(.8,b[2][0]);z1=b[2][1]
 S+=rect(X(x0),Z(z1),max(1,X(x1)-X(x0)),max(3,Z(z0)-Z(z1)),col)
for z,label in [(1,'Platform slab 1.000'),(1.1,'Coping 1.100'),(1.222,'Tread 1.222'),(1.425,'Car floor 1.425'),(1.46,'Threshold 1.460')]:
 S+=f'<path d="M90 {Z(z)} H920" stroke="#8b9bb0" stroke-dasharray="4 6"/>'+text(700,Z(z)-7,label,size=16)
S+=text(80,535,'Boarding direction: platform → tread → threshold → carriage floor')+text(80,567,'Rise: 22.2 cm + 23.8 cm; threshold stands 3.5 cm above original car floor.',size=17)+'</svg>'
(P/'side_section.svg').write_text(S,encoding='utf8')
def plan(interior):
 S=svg_start('TOP VIEW — '+('separate connected interior (local coordinates)' if interior else 'original boarding scene (door at station Y8.5)'))
 # X increases right; -Y forward in train runs upwards. Camera looks toward -X.
 px=lambda x:580+x*110
 py=lambda y:300+y*95
 S+=rect(70,100,345,350,'#344456')+text(85,125,'STATION / PLATFORM')
 S+=rect(px(-1.45),85,319,405,'#493d32')
 # train wall with 1.10m aperture
 S+=rect(px(-1.48),85,8,py(-.55)-85,'#b7a276')+rect(px(-1.48),py(.55),8,490-py(.55),'#b7a276')
 S+=rect(px(-2.33),py(-.55),.72*110,1.1*95,'#e2a84d')
 S+=f'<path d="M150 80 V490 M{px(-1.48)} 80 V490" stroke="#a7d9ff" stroke-dasharray="8 6"/>'
 S+=text(80,525,'Station façade, platform edge and train all run along Y (parallel).',size=17)
 S+=f'<path d="M{px(.724)} 300 H{px(-3.4)}" stroke="#69e2e9" stroke-width="4"/>'+text(px(.724)+5,295,'CAMERA',size=16)
 S+=text(80,560,'Camera optical axis crosses the train width along −X, perpendicular to its side.',size=16)
 if interior:
  S+=rect(px(-1.45),py(-1.4),.20*110,9,'#b7a276')+rect(px(-.25),py(-1.4),1.70*110,9,'#b7a276')
  S+=f'<path d="M{px(-2.8)} 305 H{px(-.8)} V90" fill="none" stroke="#8ee59e" stroke-width="5"/>'
  S+=text(480,115,'RIGHT TURN / −Y',size=16)+text(485,145,'1.00 m internal opening',size=15)
 else:
  S+=rect(px(-1.35),py(-1.3),2.7*110,10,'#e17b7b')
  S+=text(480,140,'Original end wall blocks route',c='#ffb0b0',size=16)
  S+=text(475,170,'No corridor opening in this wall',size=15)
 S+=text(px(-1.4)+15,380,'Boarding aperture: 1.10 m',size=16)
 return S+'</svg>'
for name,flag in [('original_plan',False),('interior_plan',True)]: (P/(name+'.svg')).write_text(plan(flag),encoding='utf8')
report='''# Boarding geometry audit — 17 September 2026

Status: REVIEW ONLY. No AI image generation. Original project scenes unchanged.

Original source: 14_Station_Asset/PressOn_Platform9_Director_Cut_v13.blend, frame 700, camera DIRECTOR 7B | Interior arrival (35 mm). Camera X≈0.724, Y8.5, Z≈2.664. Its view is frontal in plan, with a vertical tilt. The separate level-camera comparison retains X/Y/lens and sets Z3.06 with horizontal −X direction; it is a proposal, not an approved replacement.

Measured original surfaces: platform slab Z1.000; coping Z1.100; tread Z1.222 (grip ridges reach ≈1.230); threshold Z1.460; car floor Z1.425. Thus the threshold is 46 cm above the slab, not 55 cm. The 1.10×2.20 m nominal aperture is consistent between source scripts, but the threshold reduces the actual clear height relative to the nominal wall cut.

Connected interior: floor Z1.460, tread Z1.222, entry brass threshold Z1.486. Interior opening is 1.00 m wide and passage approximately 0.95 m before the rail. This is a separate model whose proposed station registration is Y68.1, whereas the approved exterior boards at Y8.5. Its floor is 3.5 cm higher than the original carriage floor. Original vestibule end wall is solid: the visible right turn is animated but the connected passage was not integrated into the exterior scene.

Simplified pilot: platform Z0, tread Z0.275, floor Z0.550. It is not dimensionally identical to the animatic. The newer camera guides must not be used as authoritative geometry.

Review decisions: use original station/door position and frontal camera direction; integrate the existing interior opening into that scene only after the registration and floor alignment are approved. A mid-thigh performance crop cannot simultaneously show the feet and step; the section and scale view verify those independently. Do not widen or angle the singing shot solely to expose the corridor.
'''
(P/'GEOMETRY_REVIEW.md').write_text(report,encoding='utf8')
body='''<h1>Press On · boarding geometry review</h1><p>Measured source geometry — no AI image generation. Original scenes remain unchanged.</p><div class="note"><b>Found:</b> the original threshold is 46 cm above the platform slab. The 55 cm pilot differs. The original vestibule has a solid end wall; the connected corridor exists in a separate interior file and was never integrated at the original boarding location.</div><h2>1 · Existing plan and route</h2><p>These diagrams use existing dimensions. They show the conflict rather than concealing it.</p><img src="original_plan.svg"><img src="interior_plan.svg"><h2>2 · Actual boarding heights</h2><img src="side_section.svg"><h2>3 · Original animated camera and stand-in</h2><p>Frame 700, DIRECTOR 7B, 35 mm. Existing pose and geometry, unchanged.</p><img src="01_original_camera_scale.png"><h2>4 · Original camera, empty environment</h2><img src="02_original_camera_empty.png"><h2>5 · Separate level-camera comparison</h2><p>Same X/Y position and 35 mm lens; horizontal direction at Z3.06. This is a labelled proposal, not a replacement for the original camera.</p><img src="03_level_frontal_review.png"><h2>What needs approval</h2><p>The existing connected interior must be registered to the original boarding doorway and its floor reconciled with the original threshold. The right-turn opening can remain outside the singing crop. We should settle these geometry differences before a photographic render.</p><p><a href="GEOMETRY_REVIEW.md">Read full audit</a> · <a href="Original_Boarding_Review.blend">Open review Blender scene</a> · <a href="source_audit.json">Measured source data</a></p>'''
(P/'REVIEW.html').write_text('<!doctype html><meta charset="utf-8"><title>Press On Boarding Geometry Review</title><style>body{font:18px system-ui;background:#111820;color:#edf0f4;max-width:1100px;margin:40px auto;padding:24px;line-height:1.6}img{width:100%;margin:12px 0 30px;border:1px solid #465261}h2{margin-top:40px}a{color:#8ee5ed}.note{padding:24px;background:#303546;border-left:4px solid #e0ac63}</style>'+body,encoding='utf8')
print(P/'REVIEW.html')
