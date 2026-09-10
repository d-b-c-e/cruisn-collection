"""Independent captured-command playback; shared material shader, separate wide mapping.

Raw game resources remain local. Starts from the prior completed GPU state and
checks the complete target after ordered commands, palettes and texture uploads.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,struct,subprocess,sys
import moderngl,numpy as np
REPO=Path(__file__).resolve().parents[1];sys.path[:0]=[str(REPO/'harness'),str(REPO/'gpu')]
from zeus_command_stream import load
from zeus_rasterize import QUAD_DTYPE
from zeus_sky_repeat import plan
from verify_zeus_margin_depth import GL,UINT,FBO,TEX,DEPTH
import zeus_renderer as Z

# Independent spelling of the wide-depth contract. It deliberately does not
# import the generator/helper used to build the native candidate's shader.
def shader(wide):
    if not wide:return Z.FS
    a='    dv = clamp(dv, 0, 0xffffff);\n    gl_FragDepth = float(dv) / 16777215.0;'
    assert Z.FS.count(a)==1
    return Z.FS.replace(a,'''    if ((flags & 32u) != 0u || ((flags & 256u) != 0u && (flags & 1024u) == 0u && dv >= 16777215)) {
        gl_FragDepth = 1.0;
    } else {
        bool range = (flags & 1024u) != 0u;
        int bounded = clamp(dv, 0, range ? 16777215 : 67108860);
        double code = double(bounded);
        if (bounded <= 16777215) {
            float legacy = float(bounded) / 16777215.0;
            code = floor(double(legacy) * 16777215.0 + 0.5);
        }
        gl_FragDepth = float(code / (range ? 16777216.0 : 67108864.0));
    }''')

def sky_candidate(q):
    v=q['verts'][:4]
    return (int(q['numverts'])==4 and int(q['flags'])&~512==52 and not int(q['yscale']) and
        int(q['rr04']) in (0,400) and list(q['clip'])==[0,0,511,399] and
        np.isfinite(v).all() and np.max(np.abs(v))<=1e12 and np.all(v[:,2]==v[0,2]) and np.all(v[:,5]==v[0,5]) and
        v[0,2]>0 and v[0,5]>0 and abs(v[0,0]-v[3,0])<.002 and abs(v[1,0]-v[2,0])<.002 and
        abs(v[0,1]-v[1,1])<.002 and abs(v[2,1]-v[3,1])<.002 and 1<v[1,0]-v[0,0]<4096 and 1<v[2,1]-v[0,1]<2048)

def render(run,frame,wide,dump=None):
    header,records,files=load(run,frame);w,h=header['width'],header['height'];S=header['scale'];M=header['margin']
    ctx=moderngl.create_standalone_context(require=430);gl=GL()
    gl.ClearColor=gl.dll.glClearColor;gl.ClearColor.argtypes=[C.c_float]*4;gl.ClearColor.restype=None
    program=ctx.program(vertex_shader=Z.VS,fragment_shader=shader(wide))
    for k,v in dict(uCanvas=(float(w//S),1024.),uMargin=float(M),waveram=0,palTex=1).items():program[k].value=v
    kind='mirror' if wide else 'original'
    seed_color=(run/f'zeus-depth-{frame-1}-{kind}-color.bin').read_bytes()
    seed_depth=(run/f'zeus-depth-{frame-1}-{kind}-depth.bin').read_bytes()
    assert len(seed_color)==len(seed_depth)==w*h*4
    color=ctx.texture((w,h),4,seed_color);target=ctx.framebuffer([color]);depth=UINT()
    gl.GenTextures(1,C.byref(depth));gl.BindTexture(TEX,depth)
    for parameter in (0x2800,0x2801):gl.TexParameteri(TEX,parameter,0x2600)
    seed=np.frombuffer(seed_depth,np.uint8)
    gl.TexImage2D(TEX,0,0x8cac if wide else 0x81a6,w,h,0,DEPTH,0x1406 if wide else 0x1405,seed.ctypes.data)
    gl.BindFramebuffer(FBO,target.glo);gl.FramebufferTexture2D(FBO,0x8d00,TEX,depth,0);assert gl.CheckFramebufferStatus(FBO)==0x8cd5
    wave=bytearray(files['wave']);pal=bytearray(files['palette'])
    wt=ctx.texture((4096,4096),1,bytes(wave),dtype='u1');pt=ctx.texture((256,256),1,bytes(pal),dtype='u4')
    ctx.viewport=(0,0,w,h);ctx.blend_func=(moderngl.ONE,moderngl.SRC_ALPHA)
    slot=header['palette'];flags=header['flags'];sky_open=bool(flags&2);sky=[]
    counters=dict(quads=0,sky_copies=0,clears=0,uploads=0)
    def draw(q,palette_slot=None,cmask=True):
        f,u,batches=Z.vertex_data([(q,slot if palette_slot is None else palette_slot)],1)
        vf,vu=ctx.buffer(f.tobytes()),ctx.buffer(u.tobytes())
        vao=ctx.vertex_array(program,[(vf,'2f 1f 4f','in_pos','in_rowbase','in_p'),(vu,'4u 4u 2u','in_meta0','in_meta1','in_meta2')])
        target.use();gl.BindFramebuffer(FBO,target.glo);wt.use(0);pt.use(1);gl.Enable(0x0b71);gl.Enable(0x0c11)
        for first,count,blend,dtest,dwrite,row,clip in batches:
            (gl.Enable if blend else gl.Disable)(0x0be2);gl.DepthFunc(0x0203 if dtest else 0x0207)
            gl.DepthMask(dwrite);gl.ColorMask(cmask,cmask,cmask,cmask);gl.Scissor(0,(row+clip[1])*S,w,(clip[3]-clip[1]+1)*S)
            vao.render(moderngl.TRIANGLES,first=first,vertices=count)
        vao.release();vf.release();vu.release()
    def finish_sky():
        nonlocal sky_open
        sky_open=False
        if sky:
            p=plan(sky,M)
            for copy in p['copies'] if p['accepted'] else []:
                q=sky[copy['index']].copy();q['verts'][:4,0]+=np.float32(copy['shift']);draw(q);counters['sky_copies']+=1
            sky.clear()
    def span(address,n,rgb,d,dwrite,cmask,range_clear=False):
        while n:
            row,x=divmod(address,512);take=min(n,512-x)
            q=np.zeros(1,QUAD_DTYPE)[0];q['numverts']=4;q['flags']=256+(16 if dwrite else 0)+(1024 if range_clear else 0)
            q['solidcolor']=rgb;q['clip']=[0,0,511,1023]
            q['verts'][:4]=[[x,row,d,0,0,1],[x+take,row,d,0,0,1],[x+take,row+1,d,0,0,1],[x,row+1,d,0,0,1]]
            draw(q,0,cmask);address=(address+take)&(512*1024-1);n-=take
    try:
        for index,(k,p) in enumerate(records):
            if flags&1 and k!=1 and sky:finish_sky()
            if k==1:
                q=np.frombuffer(p,QUAD_DTYPE)[0]
                if flags&1 and sky_open:
                    if sky_candidate(q):
                        if len(sky)<64:sky.append(q.copy())
                        else:sky.clear();sky_open=False
                    else:finish_sky()
                draw(q);counters['quads']+=1
            elif k==2:
                slot=(slot+1)&255;pal[slot*1024:(slot+1)*1024]=p;pt.write(p,viewport=(0,slot,256,1))
            elif k==3:
                address,n,rgb,d=struct.unpack('<4I',p);d=struct.unpack('<i',p[12:])[0]
                if M and n>2048:
                    start=address&(512*1024-1);row=start//512;count=min(n//512,1024-row);page=row//400*400
                    if flags&4 and start%512==0 and n%512==0 and count and n<=512*1024 and page<800 and n//512<=page+400-row:row,count=page,400
                    target.use();gl.BindFramebuffer(FBO,target.glo);gl.Enable(0x0c11);gl.DepthMask(1);gl.ColorMask(1,1,1,1);gl.ClearColor(0,0,0,1);gl.ClearDepth(1)
                    for x in (0,w-M*S):gl.Scissor(x,row*S,M*S,count*S);gl.Clear(0x4100)
                    if flags&1:sky_open=True
                span(address&(512*1024-1),min(n,512*1024),rgb&0xffffff,d,True,True,True);counters['clears']+=1
            elif k==4:
                address,r57,r58,r59,r5a,r5e=struct.unpack('<6I',p);address&=512*1024-1
                if r57&1:span(address,1,r58&0xffffff,0,False,True)
                if r5e&32:
                    if r57&4:span(address+1,1,r5a&0xffffff,0,False,True)
                else:
                    if r57&4:span(address+1,1,r59&0xffffff,0,False,True)
                    if r57&16:span(address,1,0,struct.unpack('<i',p[16:20])[0],True,False)
            elif k==5:
                start,n=struct.unpack_from('<2I',p);wave[start:start+n]=p[8:];row0=start//4096;row1=(start+n-1)//4096
                wt.write(bytes(wave[row0*4096:(row1+1)*4096]),viewport=(0,row0,4096,row1-row0+1));counters['uploads']+=1
            elif k==6 and len(p)==16:assert index==len(records)-1
        gl.check();actual_color=color.read();actual_depth=np.zeros((h,w),np.float32 if wide else np.uint32)
        gl.BindFramebuffer(0x8ca8,target.glo);gl.ReadPixels(0,0,w,h,DEPTH,0x1406 if wide else 0x1405,actual_depth.ctypes.data);gl.check()
        expected_color=(run/f'zeus-depth-{frame}-{kind}-color.bin').read_bytes();expected_depth=(run/f'zeus-depth-{frame}-{kind}-depth.bin').read_bytes()
        ca=np.frombuffer(actual_color,np.uint8).reshape(h,w,4);ce=np.frombuffer(expected_color,np.uint8).reshape(h,w,4)
        de=np.frombuffer(expected_depth,actual_depth.dtype).reshape(h,w)
        cd=int(np.count_nonzero(np.any(ca!=ce,axis=2)));dd=int(np.count_nonzero(actual_depth!=de))
        if dump is not None:
            # Explicit fresh local directory only; never overwrite prior evidence.
            (dump/f'{kind}-color.bin').write_bytes(actual_color)
            (dump/f'{kind}-depth.bin').write_bytes(actual_depth.tobytes())
        return dict(passed=cd==0 and dd==0,mode=kind,header=header,counters=counters,color_differences=cd,depth_differences=dd,
            renderer=ctx.info['GL_RENDERER'],journal_sha256={k:hashlib.sha256(v).hexdigest() for k,v in files.items()},
            initial_sha256=[hashlib.sha256(v).hexdigest() for v in (seed_color,seed_depth)],
            shader_sha256=hashlib.sha256(shader(wide).encode()).hexdigest(),actual_sha256=[hashlib.sha256(v).hexdigest() for v in (actual_color,actual_depth.tobytes())],
            expected_sha256=[hashlib.sha256(v).hexdigest() for v in (expected_color,expected_depth)],
            scope='Independent command playback from prior completed GPU state, including exact initial materials and ordered updates. Original material/vertex shaders shared; wider mapping independently expressed. No future geometry or whole-game acceptance.')
    finally:
        gl.Disable(0x0c11);vao=None;target.release();color.release();gl.DeleteTextures(1,C.byref(depth));wt.release();pt.release();program.release();ctx.release()

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run',type=Path);ap.add_argument('--frame',type=int,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--dump-dir',type=Path);a=ap.parse_args()
    assert not a.report.exists()
    if a.dump_dir is not None:a.dump_dir.mkdir()
    assert subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process -Name vunit -ErrorAction SilentlyContinue).Count"],text=True).strip()=='0'
    r=dict(passed=False,cases=[])
    try:
        for wide in (False,True):r['cases'].append(render(a.run,a.frame,wide,a.dump_dir))
        r['passed']=all(c['passed'] for c in r['cases'])
    except Exception as e:r['error']=repr(e);raise
    finally:a.report.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(r);sys.exit(0 if r['passed'] else 1)
