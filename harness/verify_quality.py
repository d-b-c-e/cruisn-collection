"""ROM-free OpenGL regression checks for enhanced V-Unit sampling and coverage.

Run explicitly on a machine with OpenGL 4.3 (not a wheel or an emulator).
The hostile texture atlas makes sampling outside the intended tile observable.
"""
import argparse
from pathlib import Path
import sys

import moderngl
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gpu"))
import renderer as R
from verification import write_json


def rectangle(x0=2, y0=2, x1=14, y1=3, mode=0x100):
    q = np.zeros(16, np.uint16)
    q[0] = mode
    q[2:10] = [x0, y0, x1, y0, x1, y1, x0, y1]
    q[10:14] = [2 << 8 | 3, 2 << 8 | 163, 162 << 8 | 163, 162 << 8 | 3]
    return q


def render(ctx, quads, texture, scale, *, debug=False, fragment_shader=R.FS, positions=None, canvas=(20,12)):
    size = (canvas[0] * scale, canvas[1] * scale)
    prog = ctx.program(vertex_shader=R.VS, fragment_shader=fragment_shader)
    for name, value in {"uCanvas": tuple(map(float,canvas)), "uScale": scale, "uClipRight": canvas[0]-1,
                        "texram": 0, "texMask": texture.size - 1, "uDbgQuadId": int(debug),
                        "uBgMargin": 0, "uClipW": canvas[0]}.items():
        prog[name].value = value
    tex = ctx.texture((4096, texture.size // 4096), 1, texture.tobytes(), dtype="u1")
    tex.use(0)
    f, u = R.build_vertices(quads, 0, dilate2d=scale > 1, positions=positions)
    vf, vu = ctx.buffer(f.tobytes()), ctx.buffer(u.tobytes())
    vao = ctx.vertex_array(prog, [(vf, "2f 2f 2f 2f 2f 4f 4f 4f", "in_corner",
        "in_v0", "in_v1", "in_v2", "in_v3", "in_uv01", "in_uv23", "in_uvBounds"),
        (vu, "4u", "in_meta")])
    idx, mask = ctx.texture(size, 1, dtype="u2"), ctx.texture(size, 1, dtype="u1")
    target = ctx.framebuffer([idx, mask])
    target.use(); target.clear(); ctx.viewport = (0, 0, *size)
    vao.render(moderngl.TRIANGLES)
    result = [np.flipud(np.frombuffer(t.read(alignment=1), dtype).reshape(size[1], size[0])).copy()
              for t, dtype in ((idx, np.uint16), (mask, np.uint8))]
    for obj in (vao, vf, vu, target, idx, mask, tex, prog):
        obj.release()
    return result


def checks(ctx):
    atlas = np.full(65536, 241, np.uint8)
    tile = atlas.reshape(256, 256)
    tile[2:163, 3:164] = 37
    q = rectangle()[None, :]
    outcomes = []
    # Sloped endpoint cases exposed by World: approximate GPU reciprocals can
    # turn an exact half-pixel tie into a different integer coverage decision.
    # Compare against the independent float32 CPU rasterizer, using flat colors
    # so this fixture needs no game texture/ROM data.
    from rasterize import render_quad
    endpoints = np.zeros((2, 16), np.uint16)
    endpoints[:, 1] = [37, 53]
    endpoints[0, 2:10] = [14, 249, 10, 253, 3, 254, 7, 250]
    endpoints[1, 2:10] = [198, 260, 231, 274, 82, 323, 77, 297]
    native = np.zeros(0x80000, np.uint16)
    for primitive in endpoints:
        render_quad(primitive, 0, native, atlas, 255, 399)
    actual, _ = render(ctx, endpoints, atlas, 1, canvas=(256, 400))
    expected = native[:0x40000].reshape(512, 512)[:400, :256]
    different = int(np.count_nonzero(actual != expected))
    outcomes.append({'check': 'native-sloped-endpoint-coverage', 'different_pixels': different,
                     'passed': bool(different == 0 and actual[250, 7] == 37 and actual[297, 77] == 53)})
    for scale in (1, 2, 3, 4, 6):
        idx, mask = render(ctx, q, atlas, scale)
        selected = idx[mask != 0]
        outcomes.append({"check": "thin-rectangle-atlas", "scale": scale,
                         "covered_pixels": int(selected.size),
                         "foreign_texels": int(np.count_nonzero(selected != 37)),
                         "passed": bool(selected.size and np.all(selected == 37))})
    # Two tiled rectangles must retain complete inclusive coverage after the
    # sampling fix; preventing bleed by deleting their expanded edge would fail.
    tiled = np.array([rectangle(2, 2, 7, 8), rectangle(8, 2, 14, 8)])
    for scale in (2, 4):
        _, mask = render(ctx, tiled, atlas, scale)
        region = mask[2*scale:9*scale, 2*scale:15*scale]
        outcomes.append({"check": "adjacent-tile-coverage", "scale": scale,
                         "holes": int(np.count_nonzero(region == 0)),
                         "passed": bool(np.all(region))})
    # Transparent foreground texels must leave the background polygon's ID.
    background = rectangle(mode=0)
    front = rectangle(mode=0x900)
    zeros = np.zeros_like(atlas)
    idx, mask = render(ctx, np.array([background, front]), zeros, 4, debug=True)
    outcomes.append({"check": "transparent-polygon-ownership",
                     "passed": bool(np.any(mask) and np.all(idx[mask != 0] == 0))})
    # Both builders feed the same shader; cover rotated UVs and degeneracy.
    varied = np.array([rectangle(), rectangle(3, 3, 3, 8), rectangle(8, 8, 2, 2)])
    varied[2, 10:14] = varied[2, 10:14][::-1]
    a = R.build_vertices(varied, 86, True)
    b = R.build_vertices_fast(varied, 86, True)
    outcomes.append({"check": "vertex-builder-equivalence",
                     "passed": all(np.array_equal(x, y) for x, y in zip(a, b))})
    sliver=np.zeros((1,16),np.uint16)
    sliver[0,1]=37
    sliver[0,2:10]=[2,2,3,6,2,6,2,6]
    idx,mask=render(ctx,sliver,atlas,4)
    outcomes.append({'check':'fine-sample-in-native-empty-span',
                     'passed':bool(mask[12,10] and idx[12,10]==37)})
    # A closed three-polygon T join, rounded left of its long edge, exposes
    # background through a thin wedge. Geometry alignment must restore coverage.
    from tjunctions import align
    verts=[(2,2,0,0),(12,22,20,40),(20,2,36,0),(0,22,0,40),(6,11,9,18)]
    terrain=np.zeros((3,16),np.uint16)
    for q,ids in zip(terrain,((0,1,2,2),(1,4,3,3),(4,0,3,3))):
        q[0]=0x100
        q[2:10]=[c for i in ids for c in verts[i][:2]]
        q[10:14]=[verts[i][2]+256*verts[i][3] for i in ids]
    positions, joins=align(terrain)
    for scale in (2,4):
        _,before=render(ctx,terrain,atlas,scale,canvas=(24,28))
        _,after=render(ctx,terrain,atlas,scale,positions=positions,canvas=(24,28))
        gained=int(np.count_nonzero((before==0)&(after!=0)))
        lost=int(np.count_nonzero((before!=0)&(after==0)))
        outcomes.append({'check':'closed-tjunction-coverage','scale':scale,'gained_pixels':gained,
                         'lost_pixels':lost,'passed':len(joins)==1 and gained>0 and lost==0})
    return outcomes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args(argv)
    report = {"schema": 1, "scope": "synthetic GPU quality regression", "passed": False}
    try:
        ctx = moderngl.create_context(standalone=True, require=430)
        report["renderer"] = ctx.info["GL_RENDERER"]
        report["checks"] = checks(ctx)
        report["passed"] = all(c["passed"] for c in report["checks"])
        ctx.release()
    except Exception as exc:
        report["error"] = str(exc)
    if args.report:
        write_json(args.report, report)
    for check in report.get("checks", []):
        print(check)
    print("PASS" if report["passed"] else "FAIL", report.get("error", ""))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
