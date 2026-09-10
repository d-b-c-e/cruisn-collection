"""Synthetic original-only D24/D32F mirror using the actual Zeus material shader.

No game resources. Run only on an idle emulator rig. This does not draw farther
scenery or prove full game command ordering. Uses the current driver's D24 behavior.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,subprocess,sys
import moderngl,numpy as np
REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'harness'),str(REPO/'gpu')]
import zeus_renderer as Z
from zeus_rasterize import QUAD_DTYPE
from verify_zeus_margin_depth import GL,UINT,INT,FBO,TEX,DEPTH,DEPTH_BIT
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
out=args.report;assert not out.exists(),'preserve previous evidence';out.parent.mkdir(parents=True,exist_ok=True)
assert subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process -Name vunit -ErrorAction SilentlyContinue).Count"],text=True).strip()=='0','rig occupied'
from zeus_depth import compatibility_fragment
sources=[Z.FS,compatibility_fragment(Z.FS)]
ctx=moderngl.create_standalone_context(require=430);gl=GL()
gl.ClearColor=gl.dll.glClearColor;gl.ClearColor.argtypes=[C.c_float]*4;gl.ClearColor.restype=None
scratch_color=ctx.texture((1,1),4);scratch=ctx.framebuffer([scratch_color]);scratch.use()
programs=[ctx.program(vertex_shader=Z.VS,fragment_shader=source) for source in sources]
wavebytes=np.tile(np.array([1,128,2,64,3,255,0,0],np.uint8),2048)
wave=ctx.texture((4096,4),1,wavebytes.tobytes(),dtype='u1')
pal=np.arange(256,dtype=np.uint32);pal=(pal*47%256)<<16|(pal*71%256)<<8|(pal*23%256)
palette=ctx.texture((256,1),1,pal.tobytes(),dtype='u4')
for p in programs:
    for k,v in dict(uCanvas=(32.,432.),uMargin=0.,waveram=0,palTex=1).items():p[k].value=v
report=dict(passed=False,renderer=ctx.info['GL_RENDERER'],cases=[],fragment_sha256=hashlib.sha256(Z.FS.encode()).hexdigest(),
    variant_sha256=hashlib.sha256(sources[1].encode()).hexdigest(),scope=__doc__+' No future geometry, full command-stream replay, game-image or other-driver acceptance.')
def quad(page,z,flags=29,rect=(0,0,32,32),solid=0x03e0,alpha=256,bias=0,mode=1):
    r=np.zeros(1,QUAD_DTYPE)[0];r['numverts']=4;r['rr04']=page;r['clip']=[0,0,31,31]
    r['flags']=flags;r['texdata']=mode;r['texwidth']=32;r['transcolor']=256
    r['srcAlpha']=alpha;r['dstAlpha']=128;r['solidcolor']=solid;r['zbuf_min']=bias
    x0,y0,x1,y1=rect
    for i,(x,y) in enumerate(((x0,y0),(x1,y0),(x1,y1),(x0,y1))):r['verts'][i]=[x,y,z,x*256,y*256,1]
    return r
def draw(target,program,r):
    f,u,batches=Z.vertex_data([(r,0)],1);vf=ctx.buffer(f.tobytes());vu=ctx.buffer(u.tobytes())
    vao=ctx.vertex_array(program,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),(vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
    try:
        target.use();gl.BindFramebuffer(FBO,target.glo);wave.use(0);palette.use(1);gl.Enable(0x0b71);gl.Disable(0x0c11)
        ctx.blend_func=(moderngl.ONE,moderngl.SRC_ALPHA)
        for first,count,blend,dtest,dwrite,_,_ in batches:
            (gl.Enable if blend else gl.Disable)(0x0be2);gl.DepthFunc(0x0203 if dtest else 0x0207);gl.DepthMask(dwrite);gl.ColorMask(1,1,1,1)
            vao.render(moderngl.TRIANGLES,first=first,vertices=count)
    finally:vao.release();vf.release();vu.release()
try:
    for scale in (1,4):
      for page in (0,400):
        size=(32*scale,432*scale);targets=[]
        try:
          for policy in (0,1):
            color=ctx.texture(size,4);target=ctx.framebuffer([color]);depth=UINT();gl.GenTextures(1,C.byref(depth));gl.BindTexture(TEX,depth)
            for parameter in (0x2800,0x2801):gl.TexParameteri(TEX,parameter,0x2600)
            gl.TexImage2D(TEX,0,0x81a6 if policy==0 else 0x8cac,*size,0,DEPTH,0x1405 if policy==0 else 0x1406,None)
            bits=INT();gl.GetTexLevelParameteriv(TEX,0,0x884a,C.byref(bits));assert bits.value==(24 if policy==0 else 32)
            gl.BindFramebuffer(FBO,target.glo);gl.FramebufferTexture2D(FBO,0x8d00,TEX,depth,0);assert gl.CheckFramebufferStatus(FBO)==0x8cd5
            targets.append((target,color,depth))
          for name,z,flags,alpha,bias,mode in (
              ('low-depth',100,29,256,0,1),('round-boundary',6291456,29,256,0,1),
              ('middle-tie',8388608,29,256,0,1),('maximum-tie',16777215,29,256,0,1),
              ('negative-bias',100,29,256,-200,1),('depth-floor',100,541,256,300,1),
              ('depth-clear',100,61,256,0,1),('no-depth-test',8388608,21,256,0,1),
              ('blended-no-depth-test',100,22,128,0,1),
              ('no-depth-write',100,13,256,0,1),('blend',100,31,128,0,1),
              ('alpha-zero',100,31,0,0,1),('palette4',100,28,256,0,0),
              ('palette8',100,28,256,0,1),('palette8-other',100,28,256,0,2),
              ('texture-alpha',100,94,256,0,1),('rgb555',100,156,256,0,1),
              ('raw-write',100,284,256,0,1),('transparent-index',100,28,256,0,1)):
            for target,color,depth in targets:
                target.use();ctx.viewport=(0,0,*size);gl.Disable(0x0c11);gl.DepthMask(1);gl.ColorMask(1,1,1,1)
                gl.BindFramebuffer(FBO,target.glo);gl.DepthMask(1);gl.ColorMask(1,1,1,1);gl.ClearColor(0,0,0,1);gl.ClearDepth(1);gl.Clear(0x4100);gl.check()
            foreground=quad(page,z,flags,(4,4,28,28),0x7c00,alpha,bias,mode)
            if name=='transparent-index':foreground['transcolor']=0
            background_z=max(z-1,0) if name in ('round-boundary','middle-tie','maximum-tie','depth-floor') else z+1
            sequence=[quad(page,background_z),foreground,quad(page,z+1,29,(12,12,20,20),0x001f),
                      quad(page,0xffffff,288,(0,0,8,8),0x123456),quad(page,0xffffff,29,(0,0,8,8),0x7c1f)]
            hashes=[]
            for step,r in enumerate(sequence):
                for program,(target,_,_) in zip(programs,targets):draw(target,program,r)
                colors=[color.read() for _,color,_ in targets];assert colors[0]==colors[1],(scale,page,name,step,'color')
                if step==0:
                    lit=int(np.count_nonzero(np.any(np.frombuffer(colors[0],np.uint8).reshape(-1,4)[:,:3],axis=1)))
                    report['base_diagnostic']=dict(lit=lit,expected=32*32*scale*scale,scale=scale,page=page,name=name,rgba=np.unique(np.frombuffer(colors[0],np.uint8).reshape(-1,4),axis=0).tolist())
                    assert lit==32*32*scale*scale,'blank or incomplete base fixture'
                original=np.zeros((size[1],size[0]),np.uint32);private=np.zeros_like(original,dtype=np.float32)
                gl.BindFramebuffer(0x8ca8,targets[0][0].glo);gl.ReadPixels(0,0,*size,DEPTH,0x1405,original.ctypes.data)
                gl.BindFramebuffer(0x8ca8,targets[1][0].glo);gl.ReadPixels(0,0,*size,DEPTH,0x1406,private.ctypes.data);gl.check()
                code=original>>8;expected=np.ldexp(code.astype(np.float32),-26);expected[code==0xffffff]=1
                assert np.array_equal(private,expected),(scale,page,name,step,'stored depth mapping')
                hashes.append(hashlib.sha256(colors[0]).hexdigest())
            report['cases'].append(dict(scale=scale,page=page,kind=name,steps=5,color_sha256=hashes,passed=True))
        finally:
            scratch.use()
            for target,color,depth in targets:target.release();color.release();gl.DeleteTextures(1,C.byref(depth))
    report['passed']=True
except Exception as error:report['error']=repr(error);raise
finally:
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for program in programs:program.release()
    wave.release();palette.release();scratch.release();scratch_color.release();ctx.release()
print('PASS',len(report['cases']),'actual-shader cases',5*len(report['cases']),'ordered steps')
