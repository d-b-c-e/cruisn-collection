"""Synthetic GPU regression: stale margin depth, both pages, untouched center."""
from pathlib import Path
import argparse,sys
import moderngl
import numpy as np
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'gpu')]
import zeus_renderer as Z
from zeus_rasterize import QUAD_DTYPE
from verification import write_json


def checks():
    ctx=moderngl.create_context(standalone=True,require=430)
    program=ctx.program(vertex_shader=Z.VS,fragment_shader=Z.FS)
    for key,value in dict(uCanvas=(688.,1024.),uMargin=88.,waveram=0,palTex=1).items():program[key].value=value
    wave=ctx.texture((4096,4),1,dtype='u1');wave.use(0)
    palette=ctx.texture((256,1),1,dtype='u4');palette.use(1)
    results=[]
    for page in (0,400):
        r=np.zeros(1,QUAD_DTYPE)[0];r['numverts']=4;r['clip']=[0,0,511,399]
        r['srcAlpha']=256;r['transcolor']=256;r['flags']=29;r['solidcolor']=0x03e0
        r['rr04']=page
        for i,(x,y) in enumerate(((-88,0),(600,0),(600,400),(-88,400))):r['verts'][i]=[x,y,150,0,0,1]
        f,u,_=Z.vertex_data([(r,0)],1)
        vf,vu=ctx.buffer(f.tobytes()),ctx.buffer(u.tobytes())
        vao=ctx.vertex_array(program,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),
            (vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
        for mode in ('legacy','page'):
            color=ctx.texture((688,1024),4);depth=ctx.depth_texture((688,1024))
            fb=ctx.framebuffer([color],depth);fb.use();ctx.viewport=(0,0,688,1024)
            ctx.scissor=None;fb.depth_mask=True;ctx.disable(moderngl.BLEND)
            fb.clear(248/255,0,0,1,depth=100/16777215)
            original=np.frombuffer(color.read(),np.uint8).reshape(1024,688,4).copy()
            original_depth=np.frombuffer(depth.read(),np.float32).reshape(1024,688).copy()
            row,count=(page+216,184) if mode=='legacy' else (page,400)
            for x in (0,600):fb.clear(0,0,0,1,depth=1,viewport=(x,row,88,count))
            ctx.scissor=None;ctx.enable(moderngl.DEPTH_TEST);ctx.depth_func='<='
            vao.render(moderngl.TRIANGLES)
            pixels=np.frombuffer(color.read(),np.uint8).reshape(1024,688,4)
            depths=np.frombuffer(depth.read(),np.float32).reshape(1024,688)
            untouched=np.ones((1024,688),bool);untouched[page:page+400,:88]=False;untouched[page:page+400,600:]=False
            assert np.array_equal(pixels[untouched],original[untouched]),'center/other page color changed'
            assert np.array_equal(depths[untouched],original_depth[untouched]),'center/other page depth changed'
            samples=[pixels[page+y,x,:3].tolist() for y in (50,300) for x in (40,648)]
            expected=([[248,0,0]]*2+[[0,248,0]]*2) if mode=='legacy' else [[0,248,0]]*4
            assert samples==expected,(page,mode,samples)
            results.append(dict(page=page,mode=mode,samples=samples,center_and_other_page_exact=True))
            for obj in (fb,color,depth):obj.release()
        for obj in (vao,vf,vu):obj.release()
    for obj in (program,wave,palette):obj.release()
    ctx.release()
    return dict(passed=True,cases=results,scope='Synthetic stale-depth regression using Zeus shaders. Known page-only margin clears preserve center and other page. Gameplay acceptance separate.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',required=True,type=Path);a=p.parse_args()
    try:r=checks()
    except (AssertionError,ValueError,KeyError,moderngl.Error) as e:r=dict(passed=False,error=str(e))
    write_json(a.report,r);print(r)
    return 0 if r['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
