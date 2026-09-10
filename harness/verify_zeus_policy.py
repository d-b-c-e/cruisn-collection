"""ROM-free pixel/occlusion checks for isolated upstream Zeus rendering semantics."""
import argparse,ast,hashlib,re,sys
from pathlib import Path
import moderngl
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gpu'))
import zeus_renderer as Z
from zeus_rasterize import QUAD_DTYPE
from zeus_render_policy import material
from verification import write_json,sha256_file


def fixture(mask,kind):
    r=np.zeros(1,QUAD_DTYPE)[0];r['numverts']=4;r['clip']=[0,0,15,15]
    mode=0x82 if kind.startswith('alpha') else 0xc01
    depth=0x4000;blend=0x20204 if kind=='blend-unity' else 0x20202
    if kind=='depth-clear':depth=0x4420
    m=material(mask,mode,depth,blend,64 if kind=='blend-unity' else 256)
    r['texdata']=mode;r['texwidth']=32;r['solidcolor']=0x7c00;r['transcolor']=256
    r['srcAlpha']=m['source_alpha'];r['dstAlpha']=128 if kind=='blend-unity' else 0
    # Depth fixtures use opaque solids so blend behavior is independent.
    flags=4|(512 if mask&1 else 0)|(8 if m['depth_test'] else 0)|(16 if m['depth_write'] else 0)
    if kind.startswith('alpha'):flags|=64|2
    else:flags|=1
    if kind=='blend-unity' and m['blend']:flags|=2
    if kind=='depth-clear':flags|=32
    r['flags']=flags;r['zbuf_min']=50 if kind=='depth-floor' else 0
    z=150 if kind=='alpha-behind' else 100
    for i,(x,y) in enumerate(((2,2),(12,2),(12,12),(2,12))):r['verts'][i]=[x,y,z,0,0,1]
    return r


def render(ctx,program,r):
    data,meta,batches=Z.vertex_data([(r,0)],1)
    vf,vu=ctx.buffer(data.tobytes()),ctx.buffer(meta.tobytes())
    vao=ctx.vertex_array(program,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),
        (vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
    color=ctx.texture((16,16),4);depth=ctx.depth_texture((16,16))
    fbo=ctx.framebuffer([color],depth);fbo.use();ctx.viewport=(0,0,16,16)
    fbo.clear(0,0,128/255,1,depth=125/16777215)
    ctx.enable(moderngl.DEPTH_TEST);ctx.blend_func=(moderngl.ONE,moderngl.SRC_ALPHA)
    for first,count,blend,dtest,dwrite,_,_ in batches:
        (ctx.enable if blend else ctx.disable)(moderngl.BLEND)
        ctx.depth_func='<=' if dtest else '1';fbo.depth_mask=dwrite
        vao.render(moderngl.TRIANGLES,first=first,vertices=count)
    rgb=np.frombuffer(color.read(),np.uint8).reshape(16,16,4)[6,6,:3].tolist()
    d=float(np.frombuffer(depth.read(),np.float32).reshape(16,16)[6,6])*16777215
    for obj in (vao,vf,vu,fbo,color,depth):obj.release()
    return rgb,round(d)


def checks(native_shader=None):
    sources={'prototype':(Z.VS,Z.FS)}
    if native_shader:
        text=Path(native_shader).read_text()
        def extract(name):
            # C string contents can contain semicolons; delimit at the next definition.
            body=text.split('static const char *MZGL_'+name+' =',1)[1].split('static const char *',1)[0]
            return ''.join(ast.literal_eval(s) for s in re.findall(r'^\s*("(?:[^"\\]|\\.)*")',body,re.M))
        sources['native']=(extract('VS'),extract('FS'))
        # gen_shaders.cstr adds one final newline after splitlines, including the
        # trailing empty source line. Compare that exact generated form.
        if sources['native']!=tuple(s+'\n' for s in sources['prototype']):raise ValueError('native/prototype Zeus shader source mismatch')
    ctx=moderngl.create_context(standalone=True,require=430)
    wave=np.tile(np.array([1,128],np.uint8),4096*2)
    texture=ctx.texture((4096,4),1,wave.tobytes(),dtype='u1');texture.use(0)
    pal=np.zeros(256,np.uint32);pal[1]=0xf80000
    palette=ctx.texture((256,1),1,pal.tobytes(),dtype='u4');palette.use(1)
    outcomes=[]
    for source,(vs,fs) in sources.items():
        program=ctx.program(vertex_shader=vs,fragment_shader=fs)
        for key,value in dict(uCanvas=(16.,16.),uMargin=0.,waveram=0,palTex=1).items():program[key].value=value
        for mask in (0,1,2,4,7):
            for kind in ('depth-floor','alpha-behind','alpha-front','blend-unity','depth-clear'):
                actual,d=render(ctx,program,fixture(mask,kind))
                if kind=='depth-floor':expected,dep=([248,0,0],100) if mask&1 else ([0,0,128],125)
                elif kind=='alpha-behind':expected,dep=([0,0,128],125) if mask&2 else ([124,0,64],125)
                elif kind=='alpha-front':expected,dep=[124,0,64],100 if mask&2 else 125
                elif kind=='blend-unity':expected,dep=[248,0,64 if mask&4 else 0],100
                else:expected,dep=[248,0,0],0xffffff
                passed=actual==expected and abs(d-dep)<=1
                outcomes.append(dict(source=source,mask=mask,kind=kind,rgb=actual,depth=d,expected_rgb=expected,expected_depth=dep,passed=passed))
        program.release()
    palette.release();texture.release();ctx.release()
    return dict(passed=all(r['passed'] for r in outcomes),checks=outcomes,
        native_shader_sha256=sha256_file(native_shader) if native_shader else None,
        fragment_sha256=hashlib.sha256(Z.FS.encode()).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',required=True,type=Path)
    p.add_argument('--native-shader',type=Path);a=p.parse_args()
    try:r=checks(a.native_shader)
    except (ValueError,OSError,KeyError,moderngl.Error) as e:r=dict(passed=False,error=str(e))
    write_json(a.report,r);print('PASS' if r['passed'] else 'FAIL',a.report)
    return 0 if r['passed'] else 1
if __name__=='__main__':sys.exit(main())
