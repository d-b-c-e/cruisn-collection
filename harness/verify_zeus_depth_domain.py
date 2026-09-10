"""Exhaustive original D24/D32F comparison; no game resources or MAME changes.

All 24-bit input codes are checked with closer/equal/farther draws. This checks
the actual driver and reports its ties instead of assuming ideal normalization.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,subprocess,sys
import moderngl
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_zeus_margin_depth import GL,UINT,INT,FBO,TEX,DEPTH,DEPTH_BIT,VS
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
assert subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process -Name vunit -ErrorAction SilentlyContinue).Count"],text=True).strip()=='0','rig occupied'
out=args.report;assert not out.exists(),'preserve previous evidence';out.parent.mkdir(parents=True,exist_ok=True)
ctx=moderngl.create_standalone_context(require=430);gl=GL();size=(4096,4096)
shader='''#version 430
uniform int policy;
uniform int bias;
uniform vec4 paint;
out vec4 color;
void main() {
    int d=clamp(int(gl_FragCoord.x)+int(gl_FragCoord.y)*4096+bias,0,16777215);
    float legacy=float(d)/16777215.;
    uint q=uint(floor(double(legacy)*16777215.0lf+0.5lf));
    gl_FragDepth=policy==0 ? legacy : (q==16777215u ? 1. : float(q)/67108864.);
    color=paint;
}'''
program=ctx.program(vertex_shader=VS,fragment_shader=shader);vao=ctx.vertex_array(program,[])
targets=[];report=dict(passed=False,renderer=ctx.info['GL_RENDERER'],original_depth_values=1<<24,cases=[],
    scope='Synthetic D24 versus D32F original-only depth mapping, preserving measured reciprocal-float/D24 quantization using double intermediate. Diagnostic only; this result applies to the measured driver. No game shader/material/scene ordering, future insertion, original/future handover or emulator integration acceptance.')
try:
    for policy in (0,1):
        color=ctx.texture(size,4);target=ctx.framebuffer([color]);depth=UINT()
        gl.GenTextures(1,C.byref(depth));gl.BindTexture(TEX,depth)
        for parameter in (0x2800,0x2801):gl.TexParameteri(TEX,parameter,0x2600)
        gl.TexImage2D(TEX,0,0x81a6 if policy==0 else 0x8cac,*size,0,DEPTH,0x1405 if policy==0 else 0x1406,None)
        bits=INT();kind=INT();gl.GetTexLevelParameteriv(TEX,0,0x884a,C.byref(bits));gl.GetTexLevelParameteriv(TEX,0,0x8c16,C.byref(kind))
        assert bits.value==(24 if policy==0 else 32)
        if policy:assert kind.value==0x1406
        gl.BindFramebuffer(FBO,target.glo);gl.FramebufferTexture2D(FBO,0x8d00,TEX,depth,0)
        assert gl.CheckFramebufferStatus(FBO)==0x8cd5
        targets.append((target,color,depth))
    for direction in (1,0,-1):
        images=[];depth_hash=None
        for policy,(target,color,depth) in enumerate(targets):
            target.use();ctx.viewport=(0,0,*size)
            gl.Disable(0x0be2);gl.Disable(0x0c11);gl.Enable(0x0b71);gl.DepthFunc(0x0203);gl.DepthMask(1);gl.ColorMask(1,1,1,1)
            gl.ClearDepth(1);gl.Clear(DEPTH_BIT)
            program['policy'].value=policy;program['bias'].value=0;program['paint'].value=(0,1,0,1)
            vao.render(vertices=3)
            if policy==0:
                original=np.zeros(size,dtype=np.uint32)
                gl.BindFramebuffer(0x8ca8,target.glo);gl.ReadPixels(0,0,*size,DEPTH,0x1405,original.ctypes.data)
                codes=original.ravel()>>8
                assert np.all(codes[1:]>=codes[:-1]) and codes[0]==0 and codes[-1]==16777215
                ties=int(np.count_nonzero(codes[1:]==codes[:-1]))
                report['original_depth_sha256']=hashlib.sha256(codes.tobytes()).hexdigest()
                report['adjacent_ties']=ties
            if policy:
                actual=np.zeros(size,dtype=np.float32)
                gl.BindFramebuffer(0x8ca8,target.glo);gl.ReadPixels(0,0,*size,DEPTH,0x1406,actual.ctypes.data)
                expected=np.ldexp(codes.astype(np.float32),-26);expected[codes==16777215]=1
                assert np.array_equal(actual.ravel(),expected),'GPU depth differs from exact power-of-two mapping'
                depth_hash=hashlib.sha256(actual.tobytes()).hexdigest()
            program['bias'].value=direction;program['paint'].value=(1,0,0,1);vao.render(vertices=3);gl.check()
            images.append(color.read())
        assert images[0]==images[1],'original-only pixel ordering differs'
        pixels=np.frombuffer(images[0],np.uint8).reshape(-1,4)
        red=int(np.count_nonzero(pixels[:,0]))
        assert red==(ties+1 if direction==1 else 1<<24),'adjacent/equal depth test differs'
        report['cases'].append(dict(bias=direction,red_pixels=red,original_color_equal=True,private_depth_sha256=depth_hash,color_sha256=hashlib.sha256(images[0]).hexdigest()))
    report['passed']=True
except Exception as error:
    report['error']=repr(error);raise
finally:
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    vao.release();program.release()
    for target,color,depth in targets:target.release();color.release();gl.DeleteTextures(1,C.byref(depth))
    ctx.release()
print(report)
