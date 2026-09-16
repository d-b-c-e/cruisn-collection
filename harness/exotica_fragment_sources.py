"""Locate visible source fragments in a saved Exotica future insertion.

An auxiliary integer target records the last surviving quad without changing
color, material discard, draw order or depth. The full insertion must reproduce
saved color/depth exactly before any subset is screened against completed depth.
Labels do not identify every contributor to blended pixels. No game execution.
"""
import argparse
import ctypes as C
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
from exotica_future_gpu import framebuffer
import zeus_renderer as Z
from exotica_distance_samples import bands
from verification import write_json, sha256_file


def render_owned(run, frame, quads, bindings, owners, probe_completed_depth=None):
    if len(quads) % 260 or len(quads) > 131072 * 260 or len(bindings) != len(quads)//260 or len(owners) != len(bindings):
        raise ValueError('invalid bounded quad/owner stream')
    polygons = np.frombuffer(quads, QUAD_DTYPE)
    if any(not 3 <= int(q['numverts']) <= 8 for q in polygons):
        raise ValueError('invalid quad vertex count')
    if any(not 1 <= int(owner) <= 0xffffffff for owner in owners):
        raise ValueError('invalid fragment owner')
    run=Path(run); prefix=run/f'exotica-host-{frame}'
    raw=lambda suffix:Path(str(prefix)+suffix).read_bytes()
    packet=parse((run/f'exotica-future-{frame}.xwd').read_bytes())
    packet['quads']=bindings
    buffers=[(run/f'exotica-future-{frame}-{s}.bin').read_bytes() for s in ('before-color','before-depth','after-color','after-depth')]
    integrity=framebuffer(buffers,packet['margin'],packet['page'],packet['draw'])
    w, h = integrity['width'], integrity['height']; scale = h//1024
    if probe_completed_depth is not None:
        if len(probe_completed_depth) != w*h*4:
            raise ValueError('completed-depth probe dimensions')
        # Diagnostic only: original immediate resources, black color, and the
        # later completed depth. Surviving fragments are candidates, not proof
        # of actual command ownership, opacity or completed contribution.
        buffers[0] = bytes(w*h*4)
        buffers[1] = probe_completed_depth
    ctx = moderngl.create_standalone_context(require=430); gl = GL()
    vs=Z.VS.replace('out vec4 p;', 'in uint in_owner; flat out uint owner; out vec4 p;').replace('    p = in_p;', '    owner=in_owner; p = in_p;')
    fs=shader(True).replace('out vec4 color;', 'layout(location=0) out vec4 color; flat in uint owner; layout(location=1) out uint owner_out;').replace('void main() {', 'void main() { owner_out=owner;')
    program = ctx.program(vertex_shader=vs, fragment_shader=fs)
    for k, v in dict(uCanvas=(float(w//scale), 1024.), uMargin=float(packet['margin']), waveram=0, palTex=1).items():
        program[k].value = v
    color = ctx.texture((w, h), 4, buffers[0])
    owner_tex=ctx.texture((w,h),1,bytes(w*h*4),dtype='u4')
    target = ctx.framebuffer([color,owner_tex]); depth = UINT()
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
    vf = vu = vo = vao = None
    try:
        if packet['draw'] and packet['quads']:
            polygons = np.frombuffer(quads, QUAD_DTYPE)
            pairs = [(q, binding['palette']) for q, binding in zip(polygons, packet['quads'])]
            f, u, batches = Z.vertex_data(pairs, 1)
            vf, vu = ctx.buffer(f.tobytes()), ctx.buffer(u.tobytes())
            assert len(owners)==len(polygons)
            ids=np.concatenate([np.full((int(q['numverts'])-2)*3,owner,np.uint32) for q,owner in zip(polygons,owners)])
            assert len(ids)==len(f)//7
            vo=ctx.buffer(ids.tobytes())
            vao = ctx.vertex_array(program, [(vf, '2f 1f 4f', 'in_pos', 'in_rowbase', 'in_p'),
                (vu, '4u 4u 2u', 'in_meta0', 'in_meta1', 'in_meta2'),(vo,'1u','in_owner')])
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
        return actual_color, actual_depth.tobytes(), owner_tex.read()
    finally:
        gl.Disable(0x0c11)
        for obj in (vao, vf, vu, vo, palettes, wave, target, color, owner_tex, program):
            if obj is not None: obj.release()
        gl.DeleteTextures(1, C.byref(depth)); ctx.release()


def source_spans(raw, quad_count):
    counts = bands(raw)
    if sum(v['quads'] for v in counts.values()) != quad_count:
        raise ValueError('instance and quad counts differ')
    return list(struct.iter_unpack('<11I', raw))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    ap.add_argument('--frame', type=int, required=True)
    ap.add_argument('--band', type=int, choices=(1, 2, 3), default=3)
    ap.add_argument('--output', type=Path, required=True, help='new directory')
    ap.add_argument('--require-visible', action='store_true')
    ap.add_argument('--save-labels', action='store_true', help='retain local per-pixel quad labels')
    args = ap.parse_args(argv)
    if not 1800 <= args.frame <= 16000:
        ap.error('frame must be within 1800..16000')
    args.output.mkdir(parents=True, exist_ok=False)
    run, frame = args.run.resolve(), args.frame
    report = dict(passed=False, selection_passed=False, frame=frame, band=args.band,
        run=str(run), scope='Saved insertion and completed-depth screen only. '
        'Labels identify the last surviving fragment, not every blended contributor '
        'or its actual final-screen/temporal visibility.')
    try:
        packet_path = run/f'exotica-future-{frame}.xwd'
        packet = parse(packet_path.read_bytes())
        raw = (run/f'exotica-host-{frame}-quads.bin').read_bytes()
        spans = source_spans((run/f'exotica-host-{frame}-instances.bin').read_bytes(), len(packet['quads']))
        if len(raw) != len(packet['quads'])*260:
            raise ValueError('packet and raw quad counts differ')
        all_ids = list(range(1, len(packet['quads'])+1))
        color, depth, _ = render_owned(run, frame, raw, packet['quads'], all_ids)
        expected = tuple((run/f'exotica-future-{frame}-after-{k}.bin').read_bytes() for k in ('color', 'depth'))
        if (color, depth) != expected:
            raise ValueError('labeled insertion changed saved color or depth')
        report.update(immediate_full_color_depth_exact=True, packet_sha256=sha256_file(packet_path))
        indices = [i for row in spans if row[5] == args.band for i in range(row[9], row[9]+row[10])]
        depth_path = run/f'zeus-depth-{frame+1}-mirror-depth.bin'
        color, _, labels = render_owned(run, frame,
            b''.join(raw[i*260:(i+1)*260] for i in indices),
            [packet['quads'][i] for i in indices], [i+1 for i in indices],
            probe_completed_depth=depth_path.read_bytes())
        base = (512+2*packet['margin'])*1024*4
        scales = [s for s in (1, 2, 3, 4) if len(color) == base*s*s]
        if len(scales) != 1:
            raise ValueError('unsupported framebuffer scale')
        scale = scales[0]; shape = (1024*scale, (512+2*packet['margin'])*scale)
        mask = np.any(np.frombuffer(color, np.uint8).reshape(*shape, 4)[:, :, :3] != 0, axis=2)
        ids = np.frombuffer(labels, '<u4').reshape(shape)
        values, counts = np.unique(ids[mask], return_counts=True)
        selected_indices = set(indices)
        if any(int(v)-1 not in selected_indices for v in values):
            raise ValueError('visible fragment has no selected source')
        counts_by_quad = dict(zip(map(int, values), map(int, counts)))
        quads = np.frombuffer(raw, QUAD_DTYPE)
        owners = []
        for row in spans:
            selected = [(i, counts_by_quad[i+1]) for i in range(row[9], row[9]+row[10]) if i+1 in counts_by_quad]
            if selected:
                owners.append(dict(entry=row[0], source=row[1], descriptor=row[2],
                    last_fragment_pixels=sum(n for _, n in selected),
                    blended_last_fragment_pixels=sum(n for i, n in selected if int(quads[i]['flags']) & 2)))
        report.update(passed=True, selection_passed=bool(mask.any()), selected_quads=len(indices),
            possible_visible_pixels=int(mask.sum()), sources=owners,
            completed_depth_sha256=sha256_file(depth_path), size=[shape[1], shape[0]])
        if args.save_labels:
            np.save(args.output/'last-fragment-quad.npy', ids)
            np.save(args.output/'possible-visible.npy', mask)
    except Exception as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
    write_json(args.output/'report.json', report)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] and (report['selection_passed'] or not args.require_visible) else 1


if __name__ == '__main__':
    raise SystemExit(main())
