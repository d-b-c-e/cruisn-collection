"""Exhaustive D24 reset seeding check on an idle GPU; no game resources."""
import argparse
import ctypes as C
from pathlib import Path
import re
import moderngl
import numpy as np
from verify_zeus_margin_depth import GL,UINT,FBO,TEX,DEPTH
from verification import write_json,sha256_file

def check():
    header=Path(__file__).resolve().parents[1]/'native/exotica_reset.h'
    source=header.read_text(encoding='utf-8')
    shaders=re.findall(r'R"GLSL\((.*?)\)GLSL"',source,re.S)
    if len(shaders)!=2:raise ValueError('reset shader source extent')
    ctx=moderngl.create_standalone_context(require=430);gl=GL();size=(4096,4096)
    codes=np.arange(1<<24,dtype=np.uint32).reshape(size)
    upload=((codes.astype(np.uint64)*0xffffffff+0x7fffff)//0xffffff).astype(np.uint32)
    colors=np.stack([codes&255,(codes>>8)&255,(codes>>16)&255,np.full_like(codes,255)],axis=-1).astype(np.uint8).tobytes()
    original_color=ctx.texture(size,4,colors);original=ctx.framebuffer([original_color])
    private_color=ctx.texture(size,4);private=ctx.framebuffer([private_color])
    depths=[]
    program=ctx.program(vertex_shader=shaders[0],fragment_shader=shaders[1]);vao=ctx.vertex_array(program,[])
    try:
        for fbo,fmt,typ,data in ((original,0x81a6,0x1405,upload),(private,0x8cac,0x1406,None)):
            texture=UINT();gl.GenTextures(1,C.byref(texture));depths.append(texture)
            gl.BindTexture(TEX,texture)
            for param in (0x2800,0x2801):gl.TexParameteri(TEX,param,0x2600)
            gl.TexImage2D(TEX,0,fmt,*size,0,DEPTH,typ,data.ctypes.data if data is not None else None)
            gl.BindFramebuffer(FBO,fbo.glo);gl.FramebufferTexture2D(FBO,0x8d00,TEX,texture,0)
            assert gl.CheckFramebufferStatus(FBO)==0x8cd5
        before_depth=gl.read_depth(original,size)
        assert np.array_equal(before_depth>>8,codes),'D24 source upload differs'
        private.use();ctx.viewport=(0,0,*size);original_color.use(0)
        # Use moderngl only to select the unit; bind the actual D24 texture.
        original_color.use(1);gl.BindTexture(TEX,depths[0])
        program['original_color'].value=0;program['original_depth'].value=1
        gl.Disable(0x0be2);gl.Disable(0x0c11);gl.Enable(0x0b71)
        gl.DepthMask(True);gl.DepthFunc(0x0207);gl.ColorMask(True,True,True,True)
        vao.render(moderngl.TRIANGLES,vertices=3);gl.check()
        actual=np.empty(size,np.float32);gl.BindFramebuffer(FBO,private.glo)
        gl.ReadPixels(0,0,*size,DEPTH,0x1406,actual.ctypes.data);gl.check()
        expected=codes.astype(np.float32)*np.float32(1/67108864);expected[-1,-1]=1
        assert np.array_equal(actual,expected),'private D32F depth differs'
        assert private_color.read()==colors,'private color differs'
        assert original_color.read()==colors,'ordinary color changed'
        assert np.array_equal(gl.read_depth(original,size),before_depth),'ordinary depth changed'
        return dict(passed=True,depth_codes=1<<24,color_pixels=1<<24,ordinary_unchanged=True,
                    header_sha256=sha256_file(header),scope='Synthetic reset target seeding only; no live reset ownership claim.')
    finally:
        for texture in depths:gl.DeleteTextures(1,C.byref(texture))
        for obj in (vao,program,private,original,private_color,original_color):obj.release()
        ctx.release()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('retain prior reset seed result')
    try:report=check()
    except Exception as e:report=dict(passed=False,error=f'{type(e).__name__}: {e}')
    write_json(a.output,report);print(report);return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
