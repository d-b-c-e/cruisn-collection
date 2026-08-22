"""GPU renderer prototype for the Zeus2 capture stream (Cruis'n Exotica).

Renders a MIDZ_CAPTURE dir on the GPU (moderngl / OpenGL 4.3) and compares
against the bit-exact CPU oracle (zeus_rasterize.py). Architecture mirrors
gpu/renderer.py for V-Unit, adapted to Zeus2's depth-buffered pipeline:

- target = the FULL 512x2048 frame-buffer space (quads address rows via
  renderRegs[0x4] - Zeus double-buffers by row base), x scale factor
- GL depth24 buffer; the fragment shader computes zeus2's 24-bit depth
  value (integer z from plane params, depth_min/depth_clear variants) and
  emits gl_FragDepth; LEQUAL matches "fail if curDepthVal > stored"
- ONE universal blend config: the shader premultiplies src by srcAlpha
  (or the texture_alpha per-pixel alpha) and outputs dstAlpha in the
  fragment alpha channel; glBlendFunc(ONE, SRC_ALPHA). Non-blended
  batches just disable blending. Batches split only on
  (blend, depth_test, effective depth_write, row base).
- texel fetch ports the swizzled fetchers + the SSE bilinear formula
  (integer, row lerps halved) straight from zeus2; palettes bake into a
  256-wide array texture, one row per pal_table load.

Exactness stance (documented in RESULTS.md): GL rasterization coverage
and float blending round differently from the scanline/integer original,
so the CPU oracle stays the bit-exact reference; the GL path is verified
statistically against it (target: ~99.9% at scale 1, artifact-free at 4x).

Usage:
  python gpu/zeus_renderer.py results/capture-zeus-3d [--scale 3] [--png]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "harness"))
from zeus_rasterize import (  # noqa: E402
    FB_COUNT, QUAD_DTYPE, Replay, parse_records)

FB_W, FB_H = 512, 2048

VS = """
#version 430
uniform vec2 uCanvas;      // FB_W, FB_H (coarse)
in vec2 in_pos;            // x, y (quad-local, coarse pixels)
in float in_rowbase;       // renderRegs[0x4] row offset
in vec4 in_p;              // p0 (z 12.12), p1 (u/z), p2 (v/z), p3 (1/z)
in uvec4 in_meta0;         // flags, texbase(byte), texwidth, texmode
in uvec4 in_meta1;         // transcolor, solidcolor, palidx, srcAlpha
in uvec2 in_meta2;         // dstAlpha, zbuf_min(as u32)
out vec4 p;
flat out uvec4 meta0;
flat out uvec4 meta1;
flat out uvec2 meta2;
void main() {
    p = in_p;
    meta0 = in_meta0; meta1 = in_meta1; meta2 = in_meta2;
    // no y flip: FB row order == GL texture row order end-to-end
    float y = in_pos.y + in_rowbase;
    gl_Position = vec4(in_pos.x / uCanvas.x * 2.0 - 1.0,
                       y / uCanvas.y * 2.0 - 1.0, 0.0, 1.0);
}
"""

FS = """
#version 430
uniform usampler2D waveram;   // 4096x4096 R8UI (16 MB)
uniform usampler2D palTex;    // 256 x NPAL R32UI
in vec4 p;                    // interpolated params
flat in uvec4 meta0;          // flags, texbase, texwidth, texmode
flat in uvec4 meta1;          // transcolor, solidcolor, palidx, srcAlpha
flat in uvec2 meta2;          // dstAlpha, zbuf_min
out vec4 color;

const int WAVE_MASK = 0xFFFFFF;

uint wave8(int idx) {
    idx &= WAVE_MASK;
    return texelFetch(waveram, ivec2(idx & 4095, idx >> 12), 0).r;
}

// swizzled texel fetchers (zeus2.h; plain byte addressing on LE)
uint texel_4bit_2x2(int base, int y, int x, int w) {
    int off = (y >> 2) * (w * 4) + ((x >> 2) << 3) + ((y & 3) << 1) + ((x >> 1) & 1);
    return (wave8(base + off) >> ((x & 1) << 2)) & 0x0fu;
}
uint texel_8bit_4x2(int base, int y, int x, int w) {
    int off = (y >> 1) * (w * 2) + ((x >> 2) << 3) + ((y & 1) << 2) + (x & 3);
    return wave8(base + off);
}
uint texel_8bit_2x2(int base, int y, int x, int w) {
    int off = (y >> 2) * (w * 4) + ((x >> 1) << 3) + ((y & 3) << 1) + (x & 1);
    return wave8(base + off);
}
uint texel_alpha_t(int base, int y, int x, int w) {
    int off = ((y >> 1) * (w * 2) + ((x >> 1) << 2) + ((y & 1) << 1) + (x & 1)) << 1;
    return wave8(base + off);
}
uint texel_alpha_a(int base, int y, int x, int w) {
    int off = (((y >> 1) * (w * 2) + ((x >> 1) << 2) + ((y & 1) << 1) + (x & 1)) << 1) + 1;
    return wave8(base + off);
}
uint rgb555_at(int base, int y, int x, int w) {
    int off = (y >> 1) * (w * 2) + ((x >> 1) << 2) + ((y & 1) << 1) + (x & 1);
    int b = base + off * 2;
    uint c = wave8(b) | (wave8(b + 1) << 8);
    return c;
}

uint fetch(int mode, int base, int y, int x, int w) {
    if (mode == 0) return texel_4bit_2x2(base, y, x, w);
    if (mode == 1) return texel_8bit_4x2(base, y, x, w);
    return texel_8bit_2x2(base, y, x, w);
}

uvec3 pal_rgb(uint idx, uint palrow) {
    uint c = texelFetch(palTex, ivec2(int(idx), int(palrow)), 0).r;
    return uvec3((c >> 16) & 0xffu, (c >> 8) & 0xffu, c & 0xffu);
}

// rgbaint_t::bilinear_filter (SSE path): row lerps halved into 16 bits
uvec3 bilerp(uvec3 c00, uvec3 c01, uvec3 c10, uvec3 c11, uint u, uint v) {
    u &= 0xffu; v &= 0xffu;
    uvec3 r0 = c01 * u + c00 * (256u - u);
    uvec3 r1 = c11 * u + c10 * (256u - u);
    return min(((r1 >> 1) * v + (r0 >> 1) * (256u - v)) >> 15, uvec3(255u));
}

void main() {
    uint flags = meta0.x;
    int  texbase = int(meta0.y);
    int  texw = int(meta0.z);
    int  texmode = int(meta0.w & 3u);
    uint transcolor = meta1.x;
    uint palrow = meta1.z;
    uint srcA = meta1.w;
    uint dstA = meta2.x;
    int  zmin = int(meta2.y);

    // ---- zeus2 depth value ----
    int curz = int(p.x);
    int dv;
    if ((flags & 32u) != 0u)      dv = 0xffffff;          // depth_clear
    else if ((flags & 4u) != 0u)  dv = curz + zmin;       // depth_min
    else                          dv = curz;
    dv = clamp(dv, 0, 0xffffff);
    gl_FragDepth = float(dv) / 16777215.0;

    bool blend = (flags & 2u) != 0u;
    if (blend && srcA == 0u) discard;

    // ---- perspective texel coords ----
    float oozinv = 1.0 / p.w;
    int curu = int(p.y * oozinv);
    int curv = int(p.z * oozinv);
    int u0 = max(curu >> 8, 0);
    int v0 = max(curv >> 8, 0);
    int u1 = u0 + 1;
    int v1 = v0 + 1;

    uvec3 src;
    float outA = float(dstA) / 256.0;       // dst blend factor via alpha

    if ((flags & 1u) != 0u) {               // solid RGB555 fill
        uint sc = meta1.y;
        src = uvec3((sc & 0x7c00u) >> 7, (sc & 0x3e0u) >> 2, (sc & 0x1fu) << 3);
        if (blend && srcA != 0x100u) src = (src * srcA) >> 8;
        if (!blend) outA = 1.0;
    } else if ((flags & 128u) != 0u) {      // direct RGB555 texture
        uint c = rgb555_at(texbase, v0, u0, texw);
        src = uvec3((c & 0x7c00u) >> 7, (c & 0x3e0u) >> 2, (c & 0x1fu) << 3);
        outA = 0.0;                         // plain overwrite, no blending
    } else if ((flags & 64u) != 0u) {       // texture with embedded alpha
        uint a00 = texel_alpha_a(texbase, v0, u0, texw);
        uint a01 = texel_alpha_a(texbase, v0, u1, texw);
        uint a10 = texel_alpha_a(texbase, v1, u0, texw);
        uint a11 = texel_alpha_a(texbase, v1, u1, texw);
        uint uF = uint(curu) & 0xffu;
        uint vF = uint(curv) & 0xffu;
        uint sA = ((a00 * (256u - uF) + a01 * uF) * (256u - vF)
                 + (a10 * (256u - uF) + a11 * uF) * vF) >> 16;
        if (sA == 0u) discard;
        uvec3 c00 = pal_rgb(texel_alpha_t(texbase, v0, u0, texw), palrow);
        uvec3 c01 = pal_rgb(texel_alpha_t(texbase, v0, u1, texw), palrow);
        uvec3 c10 = pal_rgb(texel_alpha_t(texbase, v1, u0, texw), palrow);
        uvec3 c11 = pal_rgb(texel_alpha_t(texbase, v1, u1, texw), palrow);
        src = (bilerp(c00, c01, c10, c11, uint(curu), uint(curv)) * sA) >> 8;
        outA = float(0x100u - sA) / 256.0;
    } else {                                // palette texture
        uint t00 = fetch(texmode, texbase, v0, u0, texw);
        uint t01 = fetch(texmode, texbase, v0, u1, texw);
        uint t10 = fetch(texmode, texbase, v1, u0, texw);
        uint t11 = fetch(texmode, texbase, v1, u1, texw);
        if (t00 == transcolor || t01 == transcolor
            || t10 == transcolor || t11 == transcolor) discard;
        uvec3 c00 = pal_rgb(t00, palrow);
        uvec3 c01 = pal_rgb(t01, palrow);
        uvec3 c10 = pal_rgb(t10, palrow);
        uvec3 c11 = pal_rgb(t11, palrow);
        src = bilerp(c00, c01, c10, c11, uint(curu), uint(curv));
        if (blend && srcA != 0x100u) src = (src * srcA) >> 8;
        if (!blend) outA = 1.0;
    }
    color = vec4(vec3(src) / 255.0, outA);
}
"""

FLAG_SOLID, FLAG_BLEND, FLAG_DMIN, FLAG_DTEST, FLAG_DWRITE, FLAG_DCLEAR, \
    FLAG_TALPHA, FLAG_RGB555 = (1 << i for i in range(8))


def build_quads(records):
    """Split the record stream into segments: ('direct', payloadfn-args) and
    ('quads', [(rec, palidx)]). Also returns the baked palette list."""
    segments = []
    pals = []
    cur_quads = []
    palidx = -1
    for t, payload in records:
        if t == 1:
            r = np.frombuffer(payload, QUAD_DTYPE)[0]
            cur_quads.append((r, max(palidx, 0)))
        else:
            if cur_quads:
                segments.append(("quads", cur_quads))
                cur_quads = []
            if t == 2:
                pals.append(np.frombuffer(payload, "<u4").copy())
                palidx = len(pals) - 1
            else:
                segments.append(("direct", (t, payload)))
    if cur_quads:
        segments.append(("quads", cur_quads))
    if not pals:
        pals.append(np.zeros(256, np.uint32))
    return segments, pals


def vertex_data(quads, scale):
    """Fan-triangulate quads into flat vertex arrays + batch list."""
    fdata, udata = [], []
    batches = []       # (first_vertex, count, blend, dtest, dwrite, rowbase)
    key = None
    for r, palidx in quads:
        flags = int(r["flags"])
        blend = bool(flags & FLAG_BLEND)
        dtest = bool(flags & FLAG_DTEST)
        dwrite = bool(flags & FLAG_DWRITE) and not (flags & FLAG_RGB555)
        rowbase = int(r["rr04"])
        clip = tuple(int(c) for c in r["clip"])
        k = (blend, dtest, dwrite, rowbase, clip)
        if k != key:
            batches.append([len(fdata) // 7, 0, *k])
            key = k
        nv = int(r["numverts"])
        verts = r["verts"]
        meta_u = [flags, (int(r["tex_src"]) * 8) & 0xFFFFFF, int(r["texwidth"]),
                  int(r["texdata"]) & 0xffff, int(r["transcolor"]),
                  int(r["solidcolor"]), palidx, int(r["srcAlpha"]),
                  int(r["dstAlpha"]), int(np.uint32(np.int64(r["zbuf_min"]) & 0xFFFFFFFF))]
        for i in range(2, nv):
            for vi in (0, i - 1, i):
                v = verts[vi]
                fdata.extend((float(v[0]), float(v[1]), float(rowbase),
                              float(v[2]), float(v[3]), float(v[4]), float(v[5])))
                udata.extend(meta_u)
        batches[-1][1] = len(fdata) // 7 - batches[-1][0]
    return (np.asarray(fdata, np.float32), np.asarray(udata, np.uint32),
            batches)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture_dir")
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--png", action="store_true")
    args = ap.parse_args()
    cap = args.capture_dir
    S = args.scale

    import moderngl
    ctx = moderngl.create_context(standalone=True, require=430)
    print("GL:", ctx.info["GL_RENDERER"])

    records = parse_records(os.path.join(cap, "records.bin"))
    segments, pals = build_quads(records)
    nquads = sum(len(q) for k, q in segments if k == "quads")
    print(f"{len(segments)} segments, {nquads} quads, {len(pals)} palettes")

    wave = np.fromfile(os.path.join(cap, "waveram.bin"), np.uint8)
    wtex = ctx.texture((4096, 4096), 1, wave.tobytes(), dtype="u1", alignment=1)
    ptex = ctx.texture((256, len(pals)), 1,
                       np.stack(pals).astype("<u4").tobytes(), dtype="u4")

    prog = ctx.program(vertex_shader=VS, fragment_shader=FS)
    prog["uCanvas"].value = (float(FB_W), float(FB_H))
    prog["waveram"].value = 0
    prog["palTex"].value = 1
    wtex.use(0)
    ptex.use(1)

    fw, fh = FB_W * S, FB_H * S
    ctex = ctx.texture((fw, fh), 4)
    dtex = ctx.depth_texture((fw, fh))
    fbo = ctx.framebuffer(color_attachments=[ctex], depth_attachment=dtex)
    fbo.use()
    ctx.viewport = (0, 0, fw, fh)

    # CPU mirrors, kept in sync at segment boundaries
    color_np = np.fromfile(os.path.join(cap, "pre_color.bin"), "<u4").copy()
    depth_np = np.fromfile(os.path.join(cap, "pre_depth.bin"), "<i4").copy()

    def upload_state():
        rgba = np.empty((FB_COUNT, 4), np.uint8)
        rgba[:, 0] = (color_np >> 16) & 0xff
        rgba[:, 1] = (color_np >> 8) & 0xff
        rgba[:, 2] = color_np & 0xff
        rgba[:, 3] = 255
        img = rgba.reshape(FB_H, FB_W, 4)
        d = (np.clip(depth_np, 0, 0xffffff).astype(np.float32) / 16777215.0)
        d = d.reshape(FB_H, FB_W)
        if S > 1:
            img = np.repeat(np.repeat(img, S, 0), S, 1)
            d = np.repeat(np.repeat(d, S, 0), S, 1)
        ctex.write(np.ascontiguousarray(img))
        dtex.write(np.ascontiguousarray(d))

    def readback_state():
        img = np.frombuffer(ctex.read(), np.uint8).reshape(fh, fw, 4)
        d = np.frombuffer(dtex.read(alignment=4), np.float32).reshape(fh, fw)
        if S > 1:
            img = img[::S, ::S]
            d = d[::S, ::S]
        color_np[:] = ((img[..., 0].astype(np.uint32) << 16)
                       | (img[..., 1].astype(np.uint32) << 8)
                       | img[..., 2]).reshape(-1)
        depth_np[:] = np.rint(d.reshape(-1).astype(np.float64)
                              * 16777215.0).astype(np.int32)

    rp = Replay.__new__(Replay)     # reuse direct-op logic without re-reading
    rp.color, rp.depth = color_np, depth_np
    rp.wave = wave
    rp.wave16 = wave.view("<u2")
    rp.pal = np.zeros(256, np.uint32)

    upload_state()
    gpu_dirty = False
    for kind, data in segments:
        if kind == "direct":
            if gpu_dirty:
                readback_state()
                gpu_dirty = False
            t, payload = data
            if t == 3:
                a, npx, col, dep = np.frombuffer(payload, "<u4")
                rp.fast_clear(int(a), int(npx), int(col),
                              int(np.uint32(dep).view(np.int32)))
            elif t == 4:
                pv = np.frombuffer(payload, "<u4")
                rp.frame_write(*(int(x) for x in pv))
            upload_state()
        else:
            fdata, udata, batches = vertex_data(data, S)
            vbo_f = ctx.buffer(fdata.tobytes())
            vbo_u = ctx.buffer(udata.tobytes())
            vao = ctx.vertex_array(prog, [
                (vbo_f, "2f 1f 4f", "in_pos", "in_rowbase", "in_p"),
                (vbo_u, "4u 4u 2u", "in_meta0", "in_meta1", "in_meta2"),
            ])
            ctx.enable(moderngl.DEPTH_TEST)
            ctx.blend_func = (moderngl.ONE, moderngl.SRC_ALPHA)
            for first, count, blend, dtest, dwrite, rowbase, clip in batches:
                if blend:
                    ctx.enable(moderngl.BLEND)
                else:
                    ctx.disable(moderngl.BLEND)
                ctx.depth_func = "<=" if dtest else "1"   # LEQUAL / ALWAYS
                fbo.depth_mask = dwrite
                # the hardware cliprect applies in QUAD-LOCAL y before the
                # page row base is added - without this, back-page quads
                # with y slightly outside [top, bottom] spill into the
                # displayed page
                ctx.scissor = (clip[0] * S, (rowbase + clip[1]) * S,
                               (clip[2] - clip[0] + 1) * S,
                               (clip[3] - clip[1] + 1) * S)
                vao.render(moderngl.TRIANGLES, first=first, vertices=count)
            ctx.scissor = None
            ctx.disable(moderngl.BLEND)
            fbo.depth_mask = True
            gpu_dirty = True
            vao.release()
            vbo_f.release()
            vbo_u.release()
    if gpu_dirty:
        readback_state()

    # ---- ground truth: CPU oracle ----
    truth = Replay(cap)
    for t, payload in records:
        if t == 1:
            truth.quad(np.frombuffer(payload, QUAD_DTYPE)[0])
        elif t == 2:
            truth.pal = np.frombuffer(payload, "<u4").copy()
        elif t == 3:
            a, npx, col, dep = np.frombuffer(payload, "<u4")
            truth.fast_clear(int(a), int(npx), int(col),
                             int(np.uint32(dep).view(np.int32)))
        elif t == 4:
            pv = np.frombuffer(payload, "<u4")
            truth.frame_write(*(int(x) for x in pv))

    regs = dict(ln.split()[:2] for ln in open(os.path.join(cap, "regs.txt"))
                if ln.strip())
    ys = int(regs["yScale"])
    base = int(regs["zb38"], 16) >> (16 - 9 - 2 * ys)
    H, W = 400, 512
    rows = (base + np.arange(H)[:, None] * (1 << (9 + ys))
            + np.arange(W)[None, :]) & (FB_COUNT - 1)
    gl_c = color_np[rows]
    cpu_c = truth.color[rows] & 0xffffff
    match = (gl_c == cpu_c)
    def chan(c, s):
        return ((c >> s) & 0xff).astype(np.int32)
    maxd = np.maximum.reduce([np.abs(chan(gl_c, s) - chan(cpu_c, s))
                              for s in (16, 8, 0)])
    print(f"GL vs CPU oracle (display window, scale {S} sampled at native):")
    print(f"  exact:      {100.0 * match.sum() / match.size:.4f}% "
          f"({(~match).sum()} of {match.size} differ)")
    print(f"  within +-1: {100.0 * (maxd <= 1).sum() / maxd.size:.4f}%")
    print(f"  within +-4: {100.0 * (maxd <= 4).sum() / maxd.size:.4f}%")
    print(f"  max channel delta: {maxd.max()}")

    if args.png:
        from PIL import Image
        img = np.frombuffer(ctex.read(), np.uint8).reshape(fh, fw, 4)
        y0 = (base // FB_W) * S
        crop = img[y0:y0 + H * S, :W * S, :3]
        out = os.path.join(cap, f"gl-s{S}.png")
        Image.fromarray(crop).save(out)
        print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
