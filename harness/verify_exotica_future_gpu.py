"""Replay an owned future insertion against its immediate private before/after.

Uses an independently expressed depth shader and Python geometry preparation.
Material/vertex shader code is shared with the diagnostic renderer. Raw game
resources and framebuffer bytes remain local.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import sys

import moderngl
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO/'harness'), str(REPO/'gpu')]
from verify_zeus_command_stream import shader
from verify_zeus_margin_depth import GL, UINT, FBO, TEX, DEPTH
from zeus_wide_packet import parse
from zeus_rasterize import QUAD_DTYPE
from verify_exotica_live_scene import decode_context
from verify_exotica_future import Memory, words
from verify_exotica_scene import reference, expected_bytes, verify_operands
from exotica_sections import sections
from zeus_host_materials import snapshot as check_materials
from exotica_future_gpu import framebuffer
import zeus_renderer as Z


def check(run, frame):
    run = Path(run); prefix = run/f'exotica-host-{frame}'
    raw = lambda suffix: Path(str(prefix)+suffix).read_bytes()
    wire = (run/f'exotica-future-{frame}.xwd').read_bytes(); packet = parse(wire)
    c = decode_context(raw('-context.bin'))
    read = Memory(words(Path(str(prefix)+'-ram.bin'), 0x100000),
                  words(run/'exotica-host-main-rom.bin', 0x800000),
                  words(run/'exotica-host-banked-rom.bin', 0x3000000), c['bank'])
    verify_operands(read, c['call'], c['position'])
    sources = sections(read, c['partial'])
    instances, counts = reference(sources['sources'], read, raw('-wave.bin'), frame, c['margin'], c['fade'],
        c['call'], c['context'], c['position'], c['view'], c['alternate'], c['frustum_bounds'])
    quads, headers, summary = expected_bytes(instances, c['multiplier'], c['frustum_bounds'])
    if quads != raw('-quads.bin') or headers != raw('-instances.bin'):
        raise ValueError('independent future geometry differs')
    material_size = struct.unpack_from('<I', wire, 4)[0]
    owned_quads = b''.join(wire[i+4:i+264] for i in range(32+material_size, len(wire), 264))
    if (owned_quads != quads or wire[32:32+material_size] != raw('-materials.bin') or
            packet['materials']['frame'] != frame or packet['multiplier'] != c['multiplier'] or
            packet['margin'] != c['margin'] or packet['page'] != c['context']['render'][4]):
        raise ValueError('independent future packet ownership differs')
    for header in struct.iter_unpack('<11I', headers):
        first, count = header[9:11]
        for quad in packet['quads'][first:first+count]:
            if packet['materials']['palettes'][quad['palette']][:2] != header[6:8]:
                raise ValueError('independent future palette ownership differs')
    materials = check_materials(run, frame)
    buffers = [(run/f'exotica-future-{frame}-{suffix}.bin').read_bytes()
               for suffix in ('before-color', 'before-depth', 'after-color', 'after-depth')]
    integrity = framebuffer(buffers, packet['margin'], packet['page'], packet['draw'])
    w, h = integrity['width'], integrity['height']; scale = h//1024
    ctx = moderngl.create_standalone_context(require=430); gl = GL()
    program = ctx.program(vertex_shader=Z.VS, fragment_shader=shader(True))
    for k, v in dict(uCanvas=(float(w//scale), 1024.), uMargin=float(packet['margin']), waveram=0, palTex=1).items():
        program[k].value = v
    color = ctx.texture((w, h), 4, buffers[0]); target = ctx.framebuffer([color]); depth = UINT()
    gl.GenTextures(1, C.byref(depth)); gl.BindTexture(TEX, depth)
    for parameter in (0x2800, 0x2801): gl.TexParameteri(TEX, parameter, 0x2600)
    seed = np.frombuffer(buffers[1], np.uint8)
    gl.TexImage2D(TEX, 0, 0x8cac, w, h, 0, DEPTH, 0x1406, seed.ctypes.data)
    gl.BindFramebuffer(FBO, target.glo); gl.FramebufferTexture2D(FBO, 0x8d00, TEX, depth, 0)
    if gl.CheckFramebufferStatus(FBO) != 0x8cd5: raise ValueError('insertion framebuffer incomplete')
    wave = ctx.texture((4096, 4096), 1, raw('-gpu-wave.bin'), dtype='u1')
    palette_bytes = raw('-gpu-palettes.bin') or bytes(1024)
    palettes = ctx.texture((256, len(palette_bytes)//1024), 1, palette_bytes, dtype='u4')
    ctx.viewport = (0, 0, w, h); ctx.blend_func = (moderngl.ONE, moderngl.SRC_ALPHA)
    vf = vu = vao = None
    try:
        if packet['draw'] and packet['quads']:
            polygons = np.frombuffer(quads, QUAD_DTYPE)
            pairs = [(q, binding['palette']) for q, binding in zip(polygons, packet['quads'])]
            f, u, batches = Z.vertex_data(pairs, 1)
            vf, vu = ctx.buffer(f.tobytes()), ctx.buffer(u.tobytes())
            vao = ctx.vertex_array(program, [(vf, '2f 1f 4f', 'in_pos', 'in_rowbase', 'in_p'),
                (vu, '4u 4u 2u', 'in_meta0', 'in_meta1', 'in_meta2')])
            target.use(); gl.BindFramebuffer(FBO, target.glo); wave.use(0); palettes.use(1)
            gl.Enable(0x0b71); gl.Enable(0x0c11)
            for first, count, blend, dtest, dwrite, row, clip in batches:
                (gl.Enable if blend else gl.Disable)(0x0be2); gl.DepthFunc(0x0203 if dtest else 0x0207)
                gl.DepthMask(dwrite); gl.ColorMask(True, True, True, True)
                gl.Scissor(0, (row+clip[1])*scale, w, (clip[3]-clip[1]+1)*scale)
                vao.render(moderngl.TRIANGLES, first=first, vertices=count)
        gl.check(); actual_color = color.read(); actual_depth = np.zeros((h, w), np.float32)
        gl.BindFramebuffer(0x8ca8, target.glo)
        gl.ReadPixels(0, 0, w, h, DEPTH, 0x1406, actual_depth.ctypes.data); gl.check()
        dc = int(np.count_nonzero(np.frombuffer(actual_color, '<u4') != np.frombuffer(buffers[2], '<u4')))
        dd = int(np.count_nonzero(actual_depth.ravel() != np.frombuffer(buffers[3], '<f4')))
        return dict(passed=not dc and not dd, frame=frame, multiplier=c['multiplier'], draw=packet['draw'],
            sources=counts, geometry=summary, materials=materials, integrity=integrity,
            color_differences=dc, depth_differences=dd, renderer=ctx.info['GL_RENDERER'],
            shader_sha256=hashlib.sha256(shader(True).encode()).hexdigest(),
            actual_sha256=[hashlib.sha256(v).hexdigest() for v in (actual_color, actual_depth.tobytes())],
            scope='Independent geometry preparation and immediate insertion on captured private state; shared material/vertex shader. No complete temporal/occlusion/handover acceptance.')
    finally:
        gl.Disable(0x0c11)
        for obj in (vao, vf, vu, palettes, wave, target, color, program):
            if obj is not None: obj.release()
        gl.DeleteTextures(1, C.byref(depth)); ctx.release()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path); p.add_argument('--frames', required=True)
    p.add_argument('--report', required=True, type=Path); a = p.parse_args()
    result = dict(passed=False)
    try:
        frames = [int(f) for f in a.frames.split(',')]
        if not 1 <= len(frames) <= 16 or len(frames) != len(set(frames)):
            raise ValueError('bounded unique frame list required')
        result['samples'] = [check(a.run, f) for f in frames]
        result['passed'] = all(r['passed'] for r in result['samples'])
    except Exception as e:
        result['error'] = str(e)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result)); return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
