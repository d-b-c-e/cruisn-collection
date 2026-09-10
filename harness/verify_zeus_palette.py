"""GPU fixture: pending palette rows survive batch boundaries. No game resources."""
from pathlib import Path
import sys,json,argparse
import numpy as np
import moderngl
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'gpu')]
import zeus_renderer as Z
from zeus_rasterize import QUAD_DTYPE
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--report',type=Path,required=True)
args=ap.parse_args()
ctx=moderngl.create_context(standalone=True,require=430)
program=ctx.program(vertex_shader=Z.VS,fragment_shader=Z.FS)
for name,value in dict(uCanvas=(16.,16.),uMargin=0.,waveram=0,palTex=1).items():program[name].value=value
wave=ctx.texture((4096,4),1,np.ones(4096*4,np.uint8).tobytes(),dtype='u1');wave.use(0)
palette=ctx.texture((256,256),1,dtype='u4');palette.use(1)
r=np.zeros(1,QUAD_DTYPE)[0];r['numverts']=4;r['texdata']=1;r['texwidth']=32
r['srcAlpha']=256;r['transcolor']=256;r['flags']=28;r['clip']=[0,0,15,15]
for i,(x,y) in enumerate(((2,2),(12,2),(12,12),(2,12))):r['verts'][i]=[x,y,100,0,0,1]
f,u,batches=Z.vertex_data([(r,1)],1)
vf,vu=ctx.buffer(f.tobytes()),ctx.buffer(u.tobytes())
vao=ctx.vertex_array(program,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),(vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
out=[]
for cadence in ('late','early','guarded-late'):
 color=ctx.texture((16,16),4);depth=ctx.depth_texture((16,16));fbo=ctx.framebuffer([color],depth)
 fbo.use();fbo.clear(0,0,0,1,depth=1);ctx.viewport=(0,0,16,16);ctx.disable(moderngl.BLEND)
 ctx.enable(moderngl.DEPTH_TEST);ctx.depth_func='<=';pending=True;flushes=0
 for load in range(1,258):
  slot=load&255
  if pending and ((cadence=='early' and load==128) or (cadence=='guarded-late' and slot==0)):
   vao.render(moderngl.TRIANGLES);pending=False;flushes+=1
  row=np.zeros(256,np.uint32);row[1]=0xf80000 if load==1 else 0x00f800
  palette.write(row.tobytes(),viewport=(0,slot,256,1))
 if pending:vao.render(moderngl.TRIANGLES);flushes+=1
 rgb=np.frombuffer(color.read(),np.uint8).reshape(16,16,4)[6,6,:3].tolist()
 out.append(dict(cadence=cadence,rgb=rgb,flushes=flushes))
 for obj in (fbo,color,depth):obj.release()
expected={'late':[0,248,0],'early':[248,0,0],'guarded-late':[248,0,0]}
assert all(r['rgb']==expected[r['cadence']] for r in out)
result=dict(passed=True,scope='Synthetic reproduction only: same pending geometry and palette loads, different consumer batch boundaries change legacy pixels. Flush before slot reuse preserves intended material. Does not establish cause of Amazon frame3600.',cases=out)
from verification import write_json
write_json(args.report,result)
print(result)
for obj in (vao,vf,vu,program,wave,palette):obj.release()
ctx.release()
