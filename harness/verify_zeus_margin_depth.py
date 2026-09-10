"""Synthetic GL proof: shared color, private D24, depth-only margin blits.

No game resources; requires an idle emulator rig.
This proves target isolation and ordering, not game geometry/material lifetime.
"""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import json
import os
import subprocess

import moderngl
import numpy as np

UINT = C.c_uint
INT = C.c_int
BOOL = C.c_ubyte
FBO, READ, DRAW = 0x8d40, 0x8ca8, 0x8ca9
TEX, DEPTH, DEPTH24 = 0x0de1, 0x1902, 0x81a6
COLOR_BIT, DEPTH_BIT = 0x4000, 0x100


class GL:
    def __init__(self):
        self.dll = C.WinDLL('opengl32')
        self.dll.wglGetProcAddress.argtypes = [C.c_char_p]
        self.dll.wglGetProcAddress.restype = C.c_void_p
        signatures = {
            'BindFramebuffer': (None, UINT, UINT),
            'FramebufferTexture2D': (None, UINT, UINT, UINT, UINT, INT),
            'CheckFramebufferStatus': (UINT, UINT),
            'BlitFramebuffer': (None, *([INT] * 8), UINT, UINT),
            'GenTextures': (None, INT, C.POINTER(UINT)),
            'DeleteTextures': (None, INT, C.POINTER(UINT)),
            'BindTexture': (None, UINT, UINT),
            'TexImage2D': (None, UINT, INT, INT, INT, INT, INT, UINT, UINT, C.c_void_p),
            'TexParameteri': (None, UINT, UINT, INT),
            'GetTexLevelParameteriv': (None, UINT, INT, UINT, C.POINTER(INT)),
            'ReadPixels': (None, INT, INT, INT, INT, UINT, UINT, C.c_void_p),
            'ClearDepth': (None, C.c_double), 'Clear': (None, UINT),
            'DepthMask': (None, BOOL), 'DepthFunc': (None, UINT),
            'ColorMask': (None, BOOL, BOOL, BOOL, BOOL),
            'Enable': (None, UINT), 'Disable': (None, UINT),
            'Scissor': (None, INT, INT, INT, INT), 'GetError': (UINT,),
        }
        for name, (result, *args) in signatures.items():
            try:
                fn = getattr(self.dll, 'gl' + name)
                fn.restype, fn.argtypes = result, args
            except AttributeError:
                address = self.dll.wglGetProcAddress(('gl' + name).encode('ascii'))
                assert address not in (None, 0, 1, 2, 3, -1), name
                fn = C.WINFUNCTYPE(result, *args)(address)
            setattr(self, name, fn)

    def check(self):
        assert self.GetError() == 0, 'GL error'

    def depth(self, size):
        texture = UINT()
        self.GenTextures(1, C.byref(texture))
        self.BindTexture(TEX, texture)
        for parameter in (0x2800, 0x2801):
            self.TexParameteri(TEX, parameter, 0x2600)
        self.TexImage2D(TEX, 0, DEPTH24, *size, 0, DEPTH, 0x1405, None)
        bits = INT()
        self.GetTexLevelParameteriv(TEX, 0, 0x884a, C.byref(bits))
        assert bits.value == 24, bits.value
        return texture

    def read_depth(self, framebuffer, size):
        self.BindFramebuffer(READ, framebuffer.glo)
        result = np.zeros((size[1], size[0]), dtype=np.uint32)
        self.ReadPixels(0, 0, *size, DEPTH, 0x1405, result.ctypes.data)
        self.check()
        return result


VS = '''#version 430
void main() {
    vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);
    gl_Position=vec4(p*2.-1.,0.,1.);
}'''
FS = '''#version 430
uniform int mode;
uniform float depth;
out vec4 color;
void main() {
    gl_FragDepth=depth;
    if(mode==0) color=vec4(float(int(gl_FragCoord.x)%251)/255.,
                         float(int(gl_FragCoord.y)%241)/255.,.2,1.);
    else if(mode==1) color=vec4(0.,1.,0.,1.);
    else if(mode==2) color=vec4(1.,0.,0.,1.);
    else color=vec4(0.,0.,1.,1.);
}'''


def check_case(ctx, gl, scale, margin, page):
    size = ((512 + margin * 2) * scale, 1024 * scale)
    width, height = size
    texture = ctx.texture(size, 4)
    original = ctx.framebuffer([texture])
    private = ctx.framebuffer([texture])
    original_depth, private_depth = gl.depth(size), gl.depth(size)
    program = ctx.program(vertex_shader=VS, fragment_shader=FS)
    vao = ctx.vertex_array(program, [])
    for target, depth in ((original, original_depth), (private, private_depth)):
        gl.BindFramebuffer(FBO, target.glo)
        gl.FramebufferTexture2D(FBO, 0x8d00, TEX, depth, 0)
        assert gl.CheckFramebufferStatus(FBO) == 0x8cd5
    rectangles = [(0, page*scale, margin*scale, 400*scale),
                  ((512+margin)*scale, page*scale, margin*scale, 400*scale)]
    mask = np.zeros((height, width), dtype=bool)
    for x, y, w, h in rectangles:
        mask[y:y+h, x:x+w] = True

    def draw(target, mode, depth, rect=None):
        target.use()
        ctx.viewport = (0, 0, width, height)
        gl.Enable(0x0b71)
        gl.DepthFunc(0x0203)  # LEQUAL
        gl.DepthMask(1)
        gl.ColorMask(1, 1, 1, 1)
        gl.Disable(0x0be2)
        if rect is None:
            gl.Disable(0x0c11)
        else:
            gl.Enable(0x0c11)
            gl.Scissor(*rect)
        program['mode'].value = mode
        program['depth'].value = depth
        vao.render(vertices=3)
        gl.check()

    fingerprints = []
    try:
        for repeat in range(2):
            original.use()
            gl.Disable(0x0c11)
            gl.DepthMask(1)
            gl.ClearDepth(1.)
            gl.Clear(DEPTH_BIT)
            draw(original, 0, .5)
            before_color = np.frombuffer(texture.read(), np.uint8).reshape(height,width,4).copy()
            before_depth = gl.read_depth(original, size)
            private.use()
            gl.ClearDepth(.9)
            gl.Clear(DEPTH_BIT)
            empty_private = gl.read_depth(private, size)

            # Never copy color onto its shared attachment. Source/destination depth
            # formats and samples match; copied rectangles address exactly one page.
            gl.Disable(0x0c11)
            gl.BindFramebuffer(READ, original.glo)
            gl.BindFramebuffer(DRAW, private.glo)
            for x, y, w, h in rectangles:
                if w:
                    gl.BlitFramebuffer(x,y,x+w,y+h,x,y,x+w,y+h,DEPTH_BIT,0x2600)
            gl.check()
            copied = gl.read_depth(private, size)
            assert np.array_equal(copied[mask], before_depth[mask]), 'depth blit mismatch'
            assert np.array_equal(copied[~mask], empty_private[~mask]), 'blit escaped margins'

            # Behind original depth is rejected; near geometry appears. A later
            # overlapping object behind that addition must respect PRIVATE depth.
            for rect in rectangles:
                draw(private, 2, .75, rect)
            assert texture.read() == before_color.tobytes(), 'far object overwrote foreground'
            for rect in rectangles:
                draw(private, 1, .25, rect)
                draw(private, 2, .375, rect)
            after = np.frombuffer(texture.read(), np.uint8).reshape(height,width,4).copy()
            assert np.array_equal(after[~mask], before_color[~mask]), 'color escaped margins/page'
            assert np.all(after[mask] == np.array([0,255,0,255])), 'private depth/order failed'
            assert np.array_equal(gl.read_depth(original,size),before_depth), 'original depth changed'
            private_after = gl.read_depth(private,size)
            assert np.array_equal(private_after[~mask],empty_private[~mask]), 'private writes escaped'
            assert np.all(private_after[mask] < before_depth[mask]), 'private depth not written'
            fingerprints.append(hashlib.sha256(after.tobytes()+private_after.tobytes()).hexdigest())

            # A subsequent ORIGINAL opaque draw uses its untouched depth. If it
            # accidentally inherits the private target, this pass would be rejected.
            draw(original, 3, .375)
            resumed = np.frombuffer(texture.read(),np.uint8).reshape(height,width,4)
            assert np.all(resumed == np.array([0,0,255,255])), 'original continuation changed'
        assert fingerprints[0] == fingerprints[1], 'repeat differs'
        return dict(scale=scale, margin=margin, page=page, size=size,
                    depth_bits=24, copied_pixels=int(mask.sum()),
                    center_and_other_page_unchanged=True, original_depth_unchanged=True,
                    foreground_occlusion=True, private_depth_order=True,
                    original_continuation=True, repeat_sha256=fingerprints[0])
    finally:
        gl.Disable(0x0c11)
        vao.release(); program.release(); original.release(); private.release(); texture.release()
        gl.DeleteTextures(1,C.byref(original_depth)); gl.DeleteTextures(1,C.byref(private_depth))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert os.name == 'nt'
    assert subprocess.check_output(['powershell','-NoProfile','-Command',
        "@(Get-Process -Name vunit -ErrorAction SilentlyContinue).Count"],text=True).strip() == '0', 'rig occupied'
    context = moderngl.create_standalone_context(require=430)
    report = dict(passed=False, scope=__doc__.strip(), cases=[])
    try:
        gl = GL()
        report['renderer'] = context.info['GL_RENDERER']
        for scale, margin in [(1,0),(1,86),(1,88),(3,86),(4,0),(4,86),(4,88),(4,120)]:
            for page in (0,400):
                report['cases'].append(check_case(context,gl,scale,margin,page))
                print('PASS',scale,margin,page,flush=True)
        report['passed'] = True
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        context.release()


if __name__ == '__main__':
    main()
