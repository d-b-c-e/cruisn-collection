"""Synthetic wider-original/future depth policy; standalone, not integrated in MAME."""
from pathlib import Path
import argparse,ctypes as C,hashlib,itertools,json,subprocess,sys
import moderngl,numpy as np
REPO=Path(__file__).resolve().parents[1];sys.path[:0]=[str(REPO/'harness'),str(REPO/'gpu')]
import zeus_renderer as Z
from zeus_rasterize import QUAD_DTYPE
from verify_zeus_margin_depth import GL,UINT,INT,FBO,TEX,DEPTH

from zeus_depth import wide_fragment
FS=wide_fragment(Z.FS)

def policy(z,flags,bias=0):
    # Independent scalar reference; input follows actual float vertex storage.
    cur=int(np.float32(z))
    d=0xffffff if flags&32 else max(cur,bias) if flags&4 and flags&512 else cur+bias if flags&4 else cur
    if flags&1024:
        normalized=np.float32(max(0,min(d,0xffffff)))*np.float32(1/16777215)
        q=int(np.floor(float(normalized)*16777215+.5))
        return np.float32(np.ldexp(np.float32(q),-24))
    if flags&32 or flags&256 and d>=0xffffff:return np.float32(1)
    d=max(0,min(d,67108860))
    if d<=0xffffff:
        normalized=np.float32(d)*np.float32(1/16777215)
        d=int(np.floor(float(normalized)*16777215+.5))
    return np.float32(np.ldexp(np.float32(d),-26))

def event(z,color=0x03e0,flags=29,bias=0,alpha=256,dst=128):
    return dict(z=z,color=color,flags=flags,bias=bias,alpha=alpha,dst=dst)

def expected_step(color,depth,e):
    f=e['flags'];d=policy(e['z'],f,e['bias'])
    if f&8 and d>depth or f&2 and e['alpha']==0:return color,depth
    c=e['color']
    if f&256:src=np.array([c>>16&255,c>>8&255,c&255,0],np.float64)
    else:
        src=np.array([(c&0x7c00)>>7,(c&0x3e0)>>2,(c&31)<<3,255],np.float64)
        if f&2:
            src[:3]=np.floor(src[:3]*e['alpha']/256)
            a=e['dst']/256
            src[3]=a*255
            src=np.clip(src+color*a,0,255)
    return np.rint(src).astype(np.uint8),d if f&16 and not f&128 else depth

def cases():
    for order in itertools.permutations([event(18000000,0x7c00),event(34000000,0x001f),event(50000000)]):
        yield 'far-order-'+','.join(str(e['z']) for e in order),list(order)
    yield 'near-original-occludes-future',[event(8000000),event(40000000,0x7c00)]
    yield 'future-front-of-far-original',[event(50000000),event(30000000,0x7c00)]
    yield 'raw-clear',[event(18000000),event(0xffffff,0x123456,272),event(50000000,0x7c00)]
    yield 'actual-range-clear',[event(18000000),event(0xffff00,0x123456,1296),event(50000000,0x7c00)]
    yield 'untagged-range-clear-control',[event(18000000),event(0xffff00,0x123456,272),event(50000000,0x7c00)]
    yield 'range-clear-zero',[event(18000000),event(0,0x123456,1296),event(100,0x7c00)]
    yield 'range-clear-half-blocks-third-band',[event(0x800000,0x123456,1296),event(50000000,0x7c00)]
    yield 'range-clear-half-admits-first-band',[event(0x800000,0x123456,1296),event(20000000,0x7c00)]
    yield 'range-clear-max',[event(0xffffff,0x123456,1296),event(67108860,0x7c00)]
    yield 'polygon-clear',[event(18000000),event(3,0x001f,49),event(50000000,0x7c00)]
    yield 'raw-nonmax-depth',[event(8000000,0x010203,272),event(19000000,0x7c00)]
    yield 'raw-max-versus-geometry-max',[event(0xffffff,0x010203,272),event(0xffffff),event(20000000,0x7c00)]
    yield 'no-depth-write',[event(50000000),event(20000000,0x7c00,13),event(30000000,0x001f)]
    yield 'nondepthtest-foreground',[event(20000000),event(50000000,0x7c00,21)]
    yield 'blended-nondepthtest-foreground',[event(20000000),event(50000000,0x7c00,23,alpha=128)]
    yield 'transparent-foreground',[event(50000000),event(20000000,0x7c00,31,alpha=0)]
    yield 'bias-add-crossing',[event(16777216),event(16777200,0x7c00,29,bias=32)]
    yield 'bias-floor-crossing',[event(16777216),event(100,0x7c00,541,bias=20000000)]
    yield 'negative-bias',[event(0),event(100,0x7c00,29,bias=-200)]
    for z in [0,100,6291455,6291456,8388607,8388608,16777213,16777214,16777215,16777216,16777218,33554430,33554432,50331644,67108856,67108860]:
        for offset in [-2,0,2]:yield f'boundary-{z}-{offset}',[event(z),event(max(0,z+offset),0x7c00)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,required=True);a=ap.parse_args();assert not a.report.exists()
    assert subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process -Name vunit -ErrorAction SilentlyContinue).Count"],text=True).strip()=='0','rig occupied'
    ctx=moderngl.create_standalone_context(require=430);gl=GL()
    gl.ClearColor=gl.dll.glClearColor;gl.ClearColor.argtypes=[C.c_float]*4;gl.ClearColor.restype=None
    scratch_color=ctx.texture((1,1),4);scratch=ctx.framebuffer([scratch_color]);scratch.use()
    program=ctx.program(vertex_shader=Z.VS,fragment_shader=FS)
    legacy=ctx.program(vertex_shader=Z.VS,fragment_shader=Z.FS)
    for p in (program,legacy):
        for k,v in dict(uCanvas=(16.,432.),uMargin=0.,waveram=0,palTex=1).items():p[k].value=v
    wave=ctx.texture((4096,1),1,bytes(4096),dtype='u1');palette=ctx.texture((256,1),1,bytes(1024),dtype='u4')
    report=dict(passed=False,renderer=ctx.info['GL_RENDERER'],cases=[],source_sha256=hashlib.sha256(FS.encode()).hexdigest(),legacy_sha256=hashlib.sha256(Z.FS.encode()).hexdigest(),scope=__doc__+' Constant-depth synthetic solids/raw writes. Exact RGB and stored depth use an independent scalar oracle. Exact RGBA uses unmodified material shader with CPU-decided depth admission (original GPU depth test disabled); preserves actual fixed-function alpha rounding. No game or future insertion acceptance.')
    try:
      for scale,page in itertools.product((1,4),(0,400)):
        size=(16*scale,432*scale);color=ctx.texture(size,4);target=ctx.framebuffer([color]);depth=UINT()
        reference_color=ctx.texture(size,4);reference=ctx.framebuffer([reference_color])
        gl.GenTextures(1,C.byref(depth));gl.BindTexture(TEX,depth)
        for parameter in (0x2800,0x2801):gl.TexParameteri(TEX,parameter,0x2600)
        gl.TexImage2D(TEX,0,0x8cac,*size,0,DEPTH,0x1406,None)
        bits=INT();kind=INT();gl.GetTexLevelParameteriv(TEX,0,0x884a,C.byref(bits));gl.GetTexLevelParameteriv(TEX,0,0x8c16,C.byref(kind));assert bits.value==32 and kind.value==0x1406
        gl.BindFramebuffer(FBO,target.glo);gl.FramebufferTexture2D(FBO,0x8d00,TEX,depth,0);assert gl.CheckFramebufferStatus(FBO)==0x8cd5
        try:
          for name,sequence in cases():
            for t in (target,reference):
                t.use();ctx.viewport=(0,0,*size);gl.Disable(0x0c11);gl.DepthMask(1);gl.ColorMask(1,1,1,1);gl.ClearColor(0,0,0,1);gl.ClearDepth(1);gl.Clear(0x4100)
            expected_color=np.array([0,0,0,255],np.uint8);expected_depth=np.float32(1);hashes=[]
            for step,e in enumerate(sequence):
                r=np.zeros(1,QUAD_DTYPE)[0];r['numverts']=4;r['rr04']=page;r['clip']=[0,0,15,15]
                for k,v in dict(flags=e['flags'],solidcolor=e['color'],srcAlpha=e['alpha'],dstAlpha=e['dst'],zbuf_min=e['bias'],texwidth=32,transcolor=256).items():r[k]=v
                for i,(x,y) in enumerate(((0,0),(16,0),(16,16),(0,16))):r['verts'][i]=[x,y,e['z'],0,0,1]
                floats,integers,batches=Z.vertex_data([(r,0)],1);vf=ctx.buffer(floats.tobytes());vu=ctx.buffer(integers.tobytes())
                vao=ctx.vertex_array(program,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),(vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
                original_vao=ctx.vertex_array(legacy,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),(vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
                try:
                    target.use();gl.BindFramebuffer(FBO,target.glo);wave.use(0);palette.use(1);gl.Enable(0x0b71);ctx.blend_func=(moderngl.ONE,moderngl.SRC_ALPHA)
                    for first,count,blend,dtest,dwrite,_,_ in batches:
                        (gl.Enable if blend else gl.Disable)(0x0be2);gl.DepthFunc(0x0203 if dtest else 0x0207);gl.DepthMask(dwrite);gl.ColorMask(1,1,1,1);vao.render(moderngl.TRIANGLES,first=first,vertices=count)
                    admitted=(not e['flags']&8 or policy(e['z'],e['flags'],e['bias'])<=expected_depth) and not(e['flags']&2 and e['alpha']==0)
                    if admitted:
                        reference.use();gl.Disable(0x0b71);gl.DepthMask(0)
                        for first,count,blend,_,_,_,_ in batches:
                            (gl.Enable if blend else gl.Disable)(0x0be2);gl.ColorMask(1,1,1,1);original_vao.render(moderngl.TRIANGLES,first=first,vertices=count)
                finally:vao.release();original_vao.release();vf.release();vu.release()
                expected_color,expected_depth=expected_step(expected_color,expected_depth,e)
                actual_color=np.frombuffer(color.read(),np.uint8).reshape(size[1],size[0],4)
                actual_depth=np.zeros((size[1],size[0]),np.float32);gl.BindFramebuffer(0x8ca8,target.glo);gl.ReadPixels(0,0,*size,DEPTH,0x1406,actual_depth.ctypes.data);gl.check()
                rows=slice(page*scale,(page+16)*scale)
                assert np.all(actual_color[rows,:,:3]==expected_color[:3]),(name,scale,page,step,'RGB',expected_color.tolist(),np.unique(actual_color[rows].reshape(-1,4),axis=0).tolist())
                assert actual_color.tobytes()==reference_color.read(),(name,scale,page,step,'original material RGBA with independently decided depth')
                assert np.all(actual_depth[rows]==expected_depth),(name,scale,page,step,'depth',float(expected_depth),np.unique(actual_depth[rows]).tolist())
                outside=np.ones(size[1],bool);outside[rows]=False
                assert np.all(actual_color[outside]==[0,0,0,255]) and np.all(actual_depth[outside]==1),'other-page/row isolation'
                hashes.append(hashlib.sha256(actual_color.tobytes()+actual_depth.tobytes()).hexdigest())
            report['cases'].append(dict(name=name,scale=scale,page=page,steps=len(sequence),hashes=hashes,passed=True))
        finally:scratch.use();reference.release();reference_color.release();target.release();color.release();gl.DeleteTextures(1,C.byref(depth))
      report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');program.release();legacy.release();wave.release();palette.release();scratch.release();scratch_color.release();ctx.release()
    print('PASS',len(report['cases']),'wider-depth cases',sum(r['steps'] for r in report['cases']),'ordered steps')

if __name__=='__main__':main()
