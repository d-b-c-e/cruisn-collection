"""Actual Zeus shaders: inferred panorama continuation and foreground occlusion."""
import argparse,sys
from pathlib import Path
import numpy as np
import moderngl
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'gpu'),str(Path(__file__).resolve().parents[1]/'tests')]
import zeus_renderer as Z
from test_zeus_sky_repeat import fixture
from zeus_sky_repeat import plan
from verification import write_json


def checks():
    ctx=moderngl.create_context(standalone=True,require=430)
    program=ctx.program(vertex_shader=Z.VS,fragment_shader=Z.FS)
    for k,v in dict(uCanvas=(688.,1024.),uMargin=88.,waveram=0,palTex=1).items():program[k].value=v
    wave=ctx.texture((4096,8),1,np.repeat(np.arange(1,9,dtype=np.uint8),4096).tobytes(),dtype='u1');wave.use(0)
    pal=np.zeros(256,np.uint32);pal[1:7]=[0xf80000,0x00f800,0x0000f8,0xf8f800,0xf800f8,0x00f8f8]
    palette=ctx.texture((256,1),1,pal.tobytes(),dtype='u4');palette.use(1)
    results=[]
    for page in (0,400):
        original=fixture(page=page);p=plan(original);assert p['accepted'] and len(p['copies'])==1
        extra=[]
        for c in p['copies']:
            q=original[c['index']].copy();q['verts'][:4,0]+=c['shift'];extra.append(q)
        foreground=original[0].copy();foreground['flags']=29;foreground['solidcolor']=0x7c00
        foreground['verts'][:4]=[[580,0,100,0,0,1],[600,0,100,0,0,1],[600,400,100,0,0,1],[580,400,100,0,0,1]]
        images=[]
        for enabled in (False,True):
            quads=original+(extra if enabled else [])+[foreground]
            f,u,batches=Z.vertex_data([(q,0) for q in quads],1)
            vf,vu=ctx.buffer(f.tobytes()),ctx.buffer(u.tobytes())
            vao=ctx.vertex_array(program,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),(vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
            color=ctx.texture((688,1024),4);depth=ctx.depth_texture((688,1024));fb=ctx.framebuffer([color],depth)
            fb.use();ctx.scissor=None;ctx.viewport=(0,0,688,1024);fb.clear(0,0,0,1,depth=1)
            ctx.disable(moderngl.BLEND);ctx.enable(moderngl.DEPTH_TEST)
            for first,count,blend,dtest,dwrite,_,_ in batches:
                ctx.depth_func='<=' if dtest else '1';fb.depth_mask=dwrite
                ctx.scissor=(0,page,688,400)
                vao.render(moderngl.TRIANGLES,vertices=count,first=first)
            pixels=np.frombuffer(color.read(),np.uint8).reshape(1024,688,4).copy()
            depths=np.frombuffer(depth.read(),np.float32).reshape(1024,688).copy();images.append((pixels,depths))
            assert pixels[page+50,680,:3].tolist()==[248,0,0],'foreground must remain in front'
            assert pixels[page+50,660,:3].tolist()==([0,0,248] if enabled else [0,0,0])
            for obj in (vao,vf,vu,fb,color,depth):obj.release()
        for a,b in zip(*images):
            assert np.array_equal(a[:,88:600],b[:,88:600]),'original center changed'
            assert np.array_equal(a[:page],b[:page]) and np.array_equal(a[page+400:],b[page+400:]),'other page changed'
        results.append(dict(page=page,continued_rgb=[0,0,248],foreground_rgb=[248,0,0],original_center_and_other_page_exact=True))
    for obj in (program,wave,palette):obj.release()
    ctx.release();return dict(passed=True,cases=results,scope='Synthetic panorama, original Zeus shaders, unchanged tile UVs/shape, center preservation and foreground depth. Native gameplay acceptance separate.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',required=True,type=Path);a=p.parse_args()
    try:r=checks()
    except (AssertionError,ValueError,KeyError,moderngl.Error) as e:r=dict(passed=False,error=str(e))
    write_json(a.report,r);print(r);return 0 if r['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
