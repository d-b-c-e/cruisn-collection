"""CPU reference rasterizer for the Zeus2 capture stream (Cruis'n Exotica).

Replays a MIDZ_CAPTURE dir: starting from pre_color/pre_depth, applies
records.bin (quads + palette loads + fast clears + frame writes) in
submission order and compares the result against post_color/post_depth -
the oracle for the Zeus GL renderer, exactly like rasterize.py was for
V-Unit.

This CPU-buffer oracle requires native rasterization to be enabled explicitly.
The normal live Zeus GL path skips CPU polygons; its unchanged CPU buffers do
not validate gameplay. Use completed GL plus submission/resource comparisons.

Semantics replicated bit-for-bit from MAME:
- poly.h render_triangle: y-sort, round_coordinate (floor + frac>0.5),
  plane-equation param interpolation in float32, extent params at
  (istartx+0.5, curscan+0.5).
- zeus2.cpp render_poly_8bit: integer-stepped z, perspective divide
  (u/z, v/z, 1/z in float32), swizzled texel fetchers, transcolor
  reject-if-any, SSE bilinear_filter (row lerps halved into 16-bit lanes:
  ((r1>>1)*v + (r0>>1)*(256-v)) >> 15), rgb_t::scale8 ((ch*s)>>8) and
  saturating add, the texture_alpha integer alpha lerp, and the
  fast-clear / frame_write direct paths.

Usage: python harness/zeus_rasterize.py results/capture-zeus [--png]
"""
import argparse
import os
import sys

import numpy as np
from zeus_capture import parse_records

F = np.float32
FB_COUNT = 512 * 1024 * 2          # frameColor/frameDepth entries
WAVE_MASK = 1024 * 2048 * 8 - 1    # waveram byte-wrap mask

QUAD_DTYPE = np.dtype([
    ("frame", "<u4"), ("numverts", "<u4"), ("texdata", "<u4"), ("tex_src", "<u4"),
    ("texwidth", "<u4"), ("solidcolor", "<u4"), ("transcolor", "<u4"),
    ("srcAlpha", "<u4"), ("dstAlpha", "<u4"), ("flags", "<u4"),
    ("zbuf_min", "<i4"), ("rr04", "<u4"), ("yscale", "<u4"),
    ("clip", "<i4", 4), ("verts", "<f4", (8, 6)),
])

FLAG_SOLID, FLAG_BLEND, FLAG_DMIN, FLAG_DTEST, FLAG_DWRITE, FLAG_DCLEAR, \
    FLAG_TALPHA, FLAG_RGB555 = (1 << i for i in range(8))


def round_coord(v):
    """poly.h round_coordinate: floor, +1 iff frac > 0.5 (float32 math)."""
    ip = np.floor(v)
    return int(ip) + (1 if (v - ip) > F(0.5) else 0)


# ---- texel fetchers (zeus2.h, plain-byte addressing on little-endian) ----
def texel_8bit_4x2(wave, base, y, x, width):
    off = (y >> 1) * (width * 2) + ((x >> 2) << 3) + ((y & 1) << 2) + (x & 3)
    return wave[(base + off) & WAVE_MASK]


def texel_4bit_2x2(wave, base, y, x, width):
    off = (y >> 2) * (width * 4) + ((x >> 2) << 3) + ((y & 3) << 1) + ((x >> 1) & 1)
    b = wave[(base + off) & WAVE_MASK]
    return (b >> ((x & 1) << 2)) & 0x0f


def texel_8bit_2x2(wave, base, y, x, width):
    off = (y >> 2) * (width * 4) + ((x >> 1) << 3) + ((y & 3) << 1) + (x & 1)
    return wave[(base + off) & WAVE_MASK]


def texel_8bit_2x2_alpha(wave, base, y, x, width):
    off = ((y >> 1) * (width * 2) + ((x >> 1) << 2) + ((y & 1) << 1) + (x & 1)) << 1
    return wave[(base + off) & WAVE_MASK]


def alpha_8bit_2x2_alpha(wave, base, y, x, width):
    off = (((y >> 1) * (width * 2) + ((x >> 1) << 2) + ((y & 1) << 1) + (x & 1)) << 1) + 1
    return wave[(base + off) & WAVE_MASK]


def rgb555_2x2(wave16, base16, y, x, width):
    off = (y >> 1) * (width * 2) + ((x >> 1) << 2) + ((y & 1) << 1) + (x & 1)
    c = wave16[(base16 + off) & (WAVE_MASK >> 1)].astype(np.uint32)
    return ((c & 0x7c00) << 9) | ((c & 0x3e0) << 6) | ((c & 0x1f) << 3)


# ---- rgb_t helpers (channel-wise on uint32 arrays) ----
def unpack(c):
    return ((c >> 24) & 0xff, (c >> 16) & 0xff, (c >> 8) & 0xff, c & 0xff)


def pack(a, r, g, b):
    return (a << 24) | (r << 16) | (g << 8) | b


def scale8(c, s):
    """rgb_t::scale8: (ch*s)>>8 per channel (s scalar or array <= 0x100)."""
    a, r, g, b = unpack(c)
    return pack((a * s) >> 8, (r * s) >> 8, (g * s) >> 8, (b * s) >> 8)


def sat_add(c1, c2):
    a1, r1, g1, b1 = unpack(c1)
    a2, r2, g2, b2 = unpack(c2)
    return pack(np.minimum(a1 + a2, 255), np.minimum(r1 + r2, 255),
                np.minimum(g1 + g2, 255), np.minimum(b1 + b2, 255))


def bilinear_sse(c00, c01, c10, c11, u, v):
    """rgbaint_t::bilinear_filter (SSE path): per channel,
    r0 = c01*u + c00*(256-u); r1 = c11*u + c10*(256-u);
    out = ((r1>>1)*v + (r0>>1)*(256-v)) >> 15   (row lerps lose bit 0)."""
    u = u & 0xff
    v = v & 0xff
    out = np.zeros_like(c00)
    for shift in (24, 16, 8, 0):
        p00 = (c00 >> shift) & 0xff
        p01 = (c01 >> shift) & 0xff
        p10 = (c10 >> shift) & 0xff
        p11 = (c11 >> shift) & 0xff
        r0 = p01 * u + p00 * (256 - u)
        r1 = p11 * u + p10 * (256 - u)
        ch = ((r1 >> 1) * v + (r0 >> 1) * (256 - v)) >> 15
        out |= np.minimum(ch, 255) << shift
    return out


class Replay:
    def __init__(self, cap):
        self.color = np.fromfile(os.path.join(cap, "pre_color.bin"), "<u4").copy()
        self.depth = np.fromfile(os.path.join(cap, "pre_depth.bin"), "<i4").copy()
        self.wave = np.fromfile(os.path.join(cap, "waveram.bin"), np.uint8)
        self.wave16 = self.wave.view("<u2")
        self.pal = np.zeros(256, np.uint32)
        self.stat_quads = self.stat_pixels = 0

    def fast_clear(self, addr, npx, color, depth):
        idx = (addr + np.arange(npx, dtype=np.int64)) & (FB_COUNT - 1)
        self.color[idx] = color
        self.depth[idx] = np.int32(depth)

    def frame_write(self, addr, r57, r58, r59, r5a, r5e):
        if r57 & 0x1:
            self.color[addr] = r58
        if r5e & 0x20:
            if r57 & 0x4:
                self.color[addr + 1] = r5a
        else:
            if r57 & 0x4:
                self.color[addr + 1] = r59
            if r57 & 0x10:
                self.depth[addr] = np.int32(np.uint32(r5a).view(np.int32))

    def quad(self, r):
        flags = int(r["flags"])
        numverts = int(r["numverts"])
        verts = r["verts"][:numverts].astype(np.float32)
        for i in range(2, numverts):
            self.triangle(r, flags, verts[0], verts[i - 1], verts[i])

    def triangle(self, r, flags, v1, v2, v3):
        # y-sort exactly like poly.h (strict < swaps only)
        if v2[1] < v1[1]:
            v1, v2 = v2, v1
        if v3[1] < v2[1]:
            v2, v3 = v3, v2
            if v2[1] < v1[1]:
                v1, v2 = v2, v1
        clip = r["clip"]
        v1y = round_coord(v1[1])
        v3y = round_coord(v3[1])
        y0 = max(v1y, int(clip[1]))
        y1 = min(v3y, int(clip[3]) + 1)
        if y1 - y0 <= 0:
            return

        one = F(1.0)
        dxdy_v1v2 = F(0.0) if v2[1] == v1[1] else (v2[0] - v1[0]) / (v2[1] - v1[1])
        dxdy_v1v3 = F(0.0) if v3[1] == v1[1] else (v3[0] - v1[0]) / (v3[1] - v1[1])
        dxdy_v2v3 = F(0.0) if v3[1] == v2[1] else (v3[0] - v2[0]) / (v3[1] - v2[1])

        # plane-equation param interpolation (float32, params p0..p3)
        a00 = v2[1] - v3[1]
        a01 = v3[0] - v2[0]
        a02 = v2[0] * v3[1] - v3[0] * v2[1]
        a10 = v3[1] - v1[1]
        a11 = v1[0] - v3[0]
        a12 = v3[0] * v1[1] - v1[0] * v3[1]
        a20 = v1[1] - v2[1]
        a21 = v2[0] - v1[0]
        a22 = v1[0] * v2[1] - v2[0] * v1[1]
        det = a02 + a12 + a22
        if abs(det) < F(0.00001):
            dpdx = np.zeros(4, np.float32)
            dpdy = np.zeros(4, np.float32)
            pstart = v1[2:6].copy()
        else:
            idet = one / det
            p1, p2, p3 = v1[2:6], v2[2:6], v3[2:6]
            dpdx = (idet * (p1 * a00 + p2 * a10 + p3 * a20)).astype(np.float32)
            dpdy = (idet * (p1 * a01 + p2 * a11 + p3 * a21)).astype(np.float32)
            pstart = (idet * (p1 * a02 + p2 * a12 + p3 * a22)).astype(np.float32)

        half = F(0.5)
        clipl, clipr = int(clip[0]), int(clip[2]) + 1
        for curscan in range(y0, y1):
            fully = F(curscan) + half
            startx = v1[0] + (fully - v1[1]) * dxdy_v1v3
            if fully < v2[1]:
                stopx = v1[0] + (fully - v1[1]) * dxdy_v1v2
            else:
                stopx = v2[0] + (fully - v2[1]) * dxdy_v2v3
            istartx = round_coord(startx)
            istopx = round_coord(stopx)
            if istartx > istopx:
                istartx, istopx = istopx, istartx
            istartx = max(istartx, clipl)
            istopx = min(istopx, clipr)
            if istartx >= istopx:
                continue
            fullstartx = F(istartx) + half
            p0 = pstart + fullstartx * dpdx + fully * dpdy   # float32 vec4
            self.extent(r, flags, curscan, istartx, istopx,
                        p0.astype(np.float32), dpdx)

    def extent(self, r, flags, scanline, startx, stopx, p0, dpdx):
        n = stopx - startx
        self.stat_pixels += n
        addr = (int(r["rr04"]) << (9 + int(r["yscale"]))) \
            + (scanline << (9 + int(r["yscale"])))
        xs = np.arange(startx, stopx, dtype=np.int64)
        fbidx = addr + xs

        # z: float->int32 truncation of start and step, integer stepping
        curz0 = int(np.int32(np.trunc(p0[0]))) if abs(p0[0]) < 2**31 else -2**31
        dz = int(np.int32(np.trunc(dpdx[0]))) if abs(dpdx[0]) < 2**31 else -2**31
        curz = curz0 + dz * np.arange(n, dtype=np.int64)

        # float32 sequential accumulation for u/z, v/z, 1/z
        def seq(start, step):
            arr = np.empty(n, np.float32)
            arr[0] = start
            if n > 1:
                arr[1:] = step
                arr = np.cumsum(arr, dtype=np.float32)
            return arr
        curupz = seq(p0[1], dpdx[1])
        curvpz = seq(p0[2], dpdx[2])
        curooz = seq(p0[3], dpdx[3])

        if flags & FLAG_DCLEAR:
            depthval = np.full(n, 0xffffff, np.int64)
        elif flags & FLAG_DMIN:
            depthval = np.maximum(curz,int(r["zbuf_min"])) if flags & 512 else curz + int(r["zbuf_min"])
        else:
            depthval = curz.copy()
        np.maximum(depthval, 0, out=depthval)

        dcur = self.depth[fbidx].astype(np.int64)
        if flags & FLAG_DTEST:
            passed = depthval <= dcur
        else:
            passed = np.ones(n, bool)
        if not passed.any():
            return

        oozinv = (F(1.0) / curooz).astype(np.float32)
        curu = np.trunc(curupz * oozinv).astype(np.int64)
        curv = np.trunc(curvpz * oozinv).astype(np.int64)
        u0 = np.maximum(curu >> 8, 0)
        v0 = np.maximum(curv >> 8, 0)
        u1 = u0 + 1
        v1 = v0 + 1

        wave = self.wave
        base = (int(r["tex_src"]) * 8) & WAVE_MASK
        width = int(r["texwidth"])
        texmode = int(r["texdata"]) & 0xffff
        srcA = int(r["srcAlpha"])
        dstA = int(r["dstAlpha"])
        blend = bool(flags & FLAG_BLEND)
        dwrite = bool(flags & FLAG_DWRITE)

        sel = np.nonzero(passed)[0]
        fbs = fbidx[sel]
        dvs = depthval[sel]

        if flags & FLAG_SOLID:
            sc = int(r["solidcolor"])
            solid = ((sc & 0x7c00) << 9) | ((sc & 0x3e0) << 6) | ((sc & 0x1f) << 3)
            src = np.full(len(sel), solid, np.uint32)
            self.write_pixels(fbs, src, dvs, blend, srcA, dstA, dwrite)
        elif flags & FLAG_RGB555:
            col = rgb555_2x2(self.wave16, base >> 1, v0[sel], u0[sel], width)
            self.color[fbs] = col
        elif flags & FLAG_TALPHA:
            fetch_t = texel_8bit_2x2_alpha
            fetch_a = alpha_8bit_2x2_alpha
            t00 = fetch_t(wave, base, v0[sel], u0[sel], width).astype(np.int64)
            t01 = fetch_t(wave, base, v0[sel], u1[sel], width).astype(np.int64)
            t10 = fetch_t(wave, base, v1[sel], u0[sel], width).astype(np.int64)
            t11 = fetch_t(wave, base, v1[sel], u1[sel], width).astype(np.int64)
            a00 = fetch_a(wave, base, v0[sel], u0[sel], width).astype(np.int64)
            a01 = fetch_a(wave, base, v0[sel], u1[sel], width).astype(np.int64)
            a10 = fetch_a(wave, base, v1[sel], u0[sel], width).astype(np.int64)
            a11 = fetch_a(wave, base, v1[sel], u1[sel], width).astype(np.int64)
            uF = curu[sel] & 0xff
            vF = curv[sel] & 0xff
            sA = ((a00 * (256 - uF) + a01 * uF) * (256 - vF)
                  + (a10 * (256 - uF) + a11 * uF) * vF) >> 16
            live = sA != 0
            if not live.any():
                return
            li = sel[live]
            c00 = self.pal[t00[live]].astype(np.int64)
            c01 = self.pal[t01[live]].astype(np.int64)
            c10 = self.pal[t10[live]].astype(np.int64)
            c11 = self.pal[t11[live]].astype(np.int64)
            filt = bilinear_sse(c00, c01, c10, c11, curu[sel][live], curv[sel][live])
            dst = self.color[fbidx[li]].astype(np.int64)
            out = sat_add(scale8(filt, sA[live]), scale8(dst, 0x100 - sA[live]))
            self.color[fbidx[li]] = out.astype(np.uint32)
            if dwrite:
                self.depth[fbidx[li]] = depthval[li].astype(np.int32)
        else:
            fetch = {0: texel_4bit_2x2, 1: texel_8bit_4x2}.get(
                texmode & 3, texel_8bit_2x2)
            t00 = fetch(wave, base, v0[sel], u0[sel], width).astype(np.int64)
            t01 = fetch(wave, base, v0[sel], u1[sel], width).astype(np.int64)
            t10 = fetch(wave, base, v1[sel], u0[sel], width).astype(np.int64)
            t11 = fetch(wave, base, v1[sel], u1[sel], width).astype(np.int64)
            trans = int(r["transcolor"])
            live = (t00 != trans) & (t01 != trans) & (t10 != trans) & (t11 != trans)
            if not live.any():
                return
            c00 = self.pal[t00[live]].astype(np.int64)
            c01 = self.pal[t01[live]].astype(np.int64)
            c10 = self.pal[t10[live]].astype(np.int64)
            c11 = self.pal[t11[live]].astype(np.int64)
            src = bilinear_sse(c00, c01, c10, c11, curu[sel][live], curv[sel][live])
            self.write_pixels(fbs[live], src, dvs[live], blend, srcA, dstA, dwrite)

    def write_pixels(self, fbidx, src, depthval, blend, srcA, dstA, dwrite):
        """zeus2_write_pixel, vectorized (srcA/dstA scalars <= 0x100)."""
        src = src.astype(np.int64)
        if blend:
            if srcA == 0:
                return
            dst = self.color[fbidx].astype(np.int64)
            if srcA != 0x100:
                src = scale8(src, srcA)
            if dstA == 0x100:
                src = sat_add(src, dst)
            else:
                src = sat_add(src, scale8(dst, dstA))
        self.color[fbidx] = src.astype(np.uint32)
        if dwrite:
            self.depth[fbidx] = depthval.astype(np.int32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture_dir")
    ap.add_argument("--png", action="store_true",
                    help="write replay/reference/diff PNGs of the display window")
    args = ap.parse_args()
    cap = args.capture_dir

    rp = Replay(cap)
    records = parse_records(os.path.join(cap, "records.bin"))
    nq = sum(1 for t, _ in records if t == 1)
    print(f"{len(records)} records ({nq} quads)")
    for t, payload in records:
        if t == 1:
            r = np.frombuffer(payload, QUAD_DTYPE)[0]
            rp.stat_quads += 1
            rp.quad(r)
        elif t == 2:
            rp.pal = np.frombuffer(payload, "<u4").astype(np.uint32).copy()
        elif t == 3:
            a, npx, col, dep = np.frombuffer(payload, "<u4")
            rp.fast_clear(int(a), int(npx), int(col),
                          int(np.uint32(dep).view(np.int32)))
        elif t == 4:
            p = np.frombuffer(payload, "<u4")
            rp.frame_write(int(p[0]), int(p[1]), int(p[2]), int(p[3]),
                           int(p[4]), int(p[5]))

    post_c = np.fromfile(os.path.join(cap, "post_color.bin"), "<u4")
    post_d = np.fromfile(os.path.join(cap, "post_depth.bin"), "<i4")
    # compare RGB24 (alpha byte is never displayed and pal alpha varies)
    mc = (rp.color & 0xffffff) == (post_c & 0xffffff)
    md = rp.depth == post_d
    print(f"color: {100.0 * mc.sum() / mc.size:.4f}% of full buffer "
          f"({(~mc).sum()} differ)")
    print(f"depth: {100.0 * md.sum() / md.size:.4f}% of full buffer "
          f"({(~md).sum()} differ)")

    # display-window comparison
    regs = dict(ln.split()[:2] for ln in open(os.path.join(cap, "regs.txt"))
                if ln.strip())
    ys = int(regs["yScale"])
    base = int(regs["zb38"], 16) >> (16 - 9 - 2 * ys)
    pitch = 1 << (9 + ys)
    H, W = 400, 512
    rows = (base + np.arange(H)[:, None] * pitch + np.arange(W)[None, :]) \
        & (FB_COUNT - 1)
    wc = (rp.color[rows] & 0xffffff) == (post_c[rows] & 0xffffff)
    print(f"display window: {100.0 * wc.sum() / wc.size:.4f}% "
          f"({(~wc).sum()} of {wc.size} differ)")

    if args.png:
        from PIL import Image

        def to_img(buf):
            v = buf[rows]
            img = np.zeros((H, W, 3), np.uint8)
            img[..., 0] = (v >> 16) & 0xff
            img[..., 1] = (v >> 8) & 0xff
            img[..., 2] = v & 0xff
            return img
        Image.fromarray(to_img(rp.color)).save(os.path.join(cap, "replay.png"))
        Image.fromarray(to_img(post_c)).save(os.path.join(cap, "reference.png"))
        d = (to_img(rp.color).astype(int) - to_img(post_c).astype(int))
        dm = (np.abs(d).sum(2) > 0).astype(np.uint8) * 255
        Image.fromarray(dm).save(os.path.join(cap, "diff.png"))
        print("wrote replay.png / reference.png / diff.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
