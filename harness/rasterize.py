"""Offline re-rasterizer for the captured midvunit DMA quad stream.

Faithful Python port of the exact pipeline MAME applies to each quad:

    process_dma_queue()        midvunit_v.cpp - vertex/uv/mode unpack
    make_vertices_inclusive()  midvunit_v.cpp - right/bottom +0.001f nudges
    render_polygon<4, 2>()     poly.h         - edge walk, extents, params
    render_flat/tex/trans/mask midvunit_v.cpp - per-scanline pixel fill

All float math uses np.float32 because poly_manager's BaseType is float;
double-precision Python floats would round edge cases differently. Fixed-point
u/v use int32 with C truncation semantics (float->int32 trunc, wrapping adds).

Inputs (from a run of the patched vunit build):
    quads.bin       MVQ1 header + 38-byte records (frame u32, page u16, dma[16] u16)
    videoram.bin    4 MB - both pages, u16 little-endian, 512 px stride
    textureram.bin  texture RAM bytes at dump time
    paletteram.bin  u32 words, xRRRRRGGGGGBBBBB per entry (pal5bit)
    meta.txt        dump frame, page_control, visible page offset, visarea

Output: re-rendered PNG, reference PNG, diff PNG, and a pixel-match report.
Painter's algorithm - quads replay in captured order into a simulated 4 MB
videoram; the visible page is then compared word-for-word against the dump.
"""
import argparse
import os
import struct
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = np.float32


def round_coordinate(value):
    """poly.h round_coordinate: floor, then +1 only if frac STRICTLY > 0.5."""
    ipart = np.floor(value)
    return int(ipart) + (1 if (value - ipart) > F(0.5) else 0)


def c_int32(f):
    """C 'int32_t x = float_expr' on x86: cvttss2si - truncate toward zero,
    out-of-range/NaN becomes INT_MIN. Degenerate quads hit this for real."""
    f = float(f)
    if not np.isfinite(f) or f >= 2147483648.0 or f < -2147483648.0:
        return np.int32(-2147483648)
    return np.int32(int(f))


def make_vertices_inclusive(vx, vy):
    """midvunit_v.cpp - nudge right/bottom vertices so they rasterize."""
    rmask = bmask = eqmask = 0
    for vnum in range(4):
        nxt = (vnum + 1) & 3
        if vy[nxt] == vy[vnum] and vx[nxt] == vx[vnum]:
            eqmask |= 1 << vnum
        if vy[nxt] > vy[vnum] or (vy[nxt] == vy[vnum] and vx[nxt] < vx[vnum]):
            rmask |= 1 << vnum
        if vx[nxt] < vx[vnum] or (vx[nxt] == vx[vnum] and vy[nxt] < vy[vnum]):
            bmask |= 1 << vnum
    if eqmask == 0x0f:
        return
    for vnum in range(4):
        eff = vnum
        while eqmask & (1 << eff):
            eff = (eff + 1) & 3
        if rmask & (1 << eff):
            vx[vnum] = F(vx[vnum] + F(0.001))
        if bmask & (1 << eff):
            vy[vnum] = F(vy[vnum] + F(0.001))


def render_quad(dma, page_control, vram, texram, clip_right, clip_bottom,
                cover=None, stride=512, xoff=0):
    """One captured DMA record -> pixels, exactly as MAME would.

    stride/xoff generalize the canvas for the widescreen experiment: a wider
    framebuffer with the original screen occupying columns [xoff, xoff+512).
    Defaults reproduce MAME's real 512-stride pages exactly.
    """
    page_words = 512 * stride
    destbase = page_words if (page_control & 4) else 0
    dest = vram[destbase:destbase + page_words].reshape(512, stride)
    cov = (cover[destbase:destbase + page_words].reshape(512, stride)
           if cover is not None else None)

    vx = [F(np.int16(dma[2 + i * 2]) + F(0.5) + F(xoff)) for i in range(4)]
    vy = [F(np.int16(dma[3 + i * 2]) + F(0.5)) for i in range(4)]

    pixdata = dma[1]
    textured = (dma[0] & 0x300) == 0x100
    dither = 1 if (dma[0] & 0x2000) else 0

    pu = pv = None
    if not textured:
        mode = "flat"
        pixdata = (pixdata + (dma[0] & 0x00ff)) & 0xffff
    else:
        pu = [F(F(dma[10 + i] & 0xff) * F(65536.0) + F(32768.0)) for i in range(4)]
        pv = [F(F(dma[10 + i] >> 8) * F(65536.0) + F(32768.0)) for i in range(4)]
        sel = dma[0] & 0xc00
        if sel == 0x000:
            mode = "tex"
        elif sel == 0x800:
            mode = "textrans"
        elif sel == 0xc00:
            mode = "textransmask"
            pixdata = (pixdata + (dma[0] & 0x00ff)) & 0xffff
        else:
            mode = "flat"
            pixdata = (pixdata + (dma[0] & 0x00ff)) & 0xffff
            textured = False

    make_vertices_inclusive(vx, vy)

    texbase = (dma[14] * 256) & 0xffffffff

    # ---- render_polygon<4, 2> (poly.h), Flags=0 ----
    minv = maxv = 0
    for i in range(1, 4):
        if vy[i] < vy[minv]:
            minv = i
        elif vy[i] > vy[maxv]:
            maxv = i

    miny = round_coordinate(vy[minv])
    maxy = round_coordinate(vy[maxv])
    minyclip = max(miny, 0)
    maxyclip = min(maxy, clip_bottom + 1)
    if maxyclip - minyclip <= 0:
        return mode, 0

    params = 2 if textured else 0

    def build_edges(forward):
        edges = []
        curv = minv
        while curv != maxv:
            nxt = ((curv + 1) & 3) if forward else ((curv - 1) & 3)
            if vy[nxt] != vy[curv]:
                ooy = F(F(1.0) / F(vy[nxt] - vy[curv]))
                e = {
                    "v1x": vx[curv], "v1y": vy[curv], "v2y": vy[nxt],
                    "dxdy": F(F(vx[nxt] - vx[curv]) * ooy),
                }
                if params:
                    e["p1"] = (pu[curv], pv[curv])
                    e["dpdy"] = (F(F(pu[nxt] - pu[curv]) * ooy),
                                 F(F(pv[nxt] - pv[curv]) * ooy))
                edges.append(e)
            curv = nxt
        return edges

    fedge = build_edges(True)
    bedge = build_edges(False)
    if not fedge or not bedge:
        return mode, 0

    # left/right decision (poly.h:1194)
    f0, b0 = fedge[0], bedge[0]
    shared = (f0["v1x"] == b0["v1x"] and f0["v1y"] == b0["v1y"])
    if (shared and f0["dxdy"] < b0["dxdy"]) or (not shared and f0["v1x"] < b0["v1x"]):
        ledges, redges = fedge, bedge
    else:
        ledges, redges = bedge, fedge

    li = ri = 0
    maxvy = vy[maxv]
    pixels = 0

    for curscan in range(minyclip, maxyclip):
        fully = F(F(curscan) + F(0.5))
        while fully > ledges[li]["v2y"] and fully < maxvy and li + 1 < len(ledges):
            li += 1
        while fully > redges[ri]["v2y"] and fully < maxvy and ri + 1 < len(redges):
            ri += 1
        le, re_ = ledges[li], redges[ri]
        startx = F(le["v1x"] + F(fully - le["v1y"]) * le["dxdy"])
        stopx = F(re_["v1x"] + F(fully - re_["v1y"]) * re_["dxdy"])
        istartx = round_coordinate(startx)
        istopx = round_coordinate(stopx)
        if istartx > istopx:
            istartx, istopx = istopx, istartx

        if params:
            ldy = F(fully - le["v1y"])
            rdy = F(fully - re_["v1y"])
            oox = F(F(1.0) / F(stopx - startx)) if stopx != startx else F(0)
            pstart, pdpdx = [], []
            for pn in range(2):
                lp = F(le["p1"][pn] + ldy * le["dpdy"][pn])
                rp = F(re_["p1"][pn] + rdy * re_["dpdy"][pn])
                dpdx = F(F(rp - lp) * oox)
                pstart.append(F(lp + F(F(istartx) + F(0.5) - startx) * dpdx))
                pdpdx.append(dpdx)

        # left/right clip (cliprect.left() == 0)
        if istartx < 0:
            if params:
                for pn in range(2):
                    pstart[pn] = F(pstart[pn] + F(0 - istartx) * pdpdx[pn])
            istartx = 0
        if istopx > clip_right:
            istopx = clip_right + 1
        if istartx >= istopx:
            continue

        # ---- the four render callbacks (midvunit_v.cpp) ----
        xstep = dither + 1
        sx = istartx
        row = dest[curscan]
        crow = cov[curscan] if cov is not None else None

        if mode == "flat":
            sx += (curscan ^ sx) & dither
            if xstep == 1:
                row[sx:istopx] = pixdata
                if crow is not None:
                    crow[sx:istopx] = True
                pixels += max(0, istopx - sx)
            else:
                row[sx:istopx:2] = pixdata
                if crow is not None:
                    crow[sx:istopx:2] = True
                pixels += len(range(sx, istopx, 2))
            continue

        # textured paths: int32 fixed-point with C truncation semantics
        u = c_int32(pstart[0])
        v = c_int32(pstart[1])
        dudx = c_int32(pdpdx[0])
        dvdx = c_int32(pdpdx[1])
        if xstep == 2:
            if (curscan ^ sx) & 1:
                sx += 1
                u = np.int32(u + dudx)
                v = np.int32(v + dvdx)
            dudx = np.int32(dudx * 2)
            dvdx = np.int32(dvdx * 2)
        n = len(range(sx, istopx, xstep))
        if n <= 0:
            continue
        idx = np.arange(n, dtype=np.int64)
        uu = (np.int64(int(u)) + idx * int(dudx)).astype(np.int32)
        vv = (np.int64(int(v)) + idx * int(dvdx)).astype(np.int32)
        # texbase[((v >> 8) & 0xff00) + (u >> 16)]
        toff = (texbase
                + ((vv >> np.int32(8)) & np.int32(0xff00)).astype(np.int64)
                + (uu >> np.int32(16)).astype(np.int64))
        texels = texram[toff & (len(texram) - 1)]
        xs = np.arange(sx, istopx, xstep, dtype=np.int64)[:n]

        if mode == "tex":
            row[xs] = (pixdata + texels).astype(np.uint16)
            if crow is not None:
                crow[xs] = True
            pixels += n
        elif mode == "textrans":
            m = texels != 0
            row[xs[m]] = (pixdata + texels[m]).astype(np.uint16)
            if crow is not None:
                crow[xs[m]] = True
            pixels += int(m.sum())
        else:  # textransmask
            m = texels != 0
            row[xs[m]] = pixdata
            if crow is not None:
                crow[xs[m]] = True
            pixels += int(m.sum())
    return mode, pixels


def load_meta(path):
    meta = {}
    for line in open(path):
        k, *v = line.split()
        meta[k] = [int(x, 0) for x in v]
    return meta


def to_rgb(indices, palette_words):
    """videoram value -> pen index (&0x7fff) -> pal5bit RGB, as screen_update."""
    pens = indices & 0x7fff
    words = palette_words[pens]
    r = ((words >> 10) & 0x1f).astype(np.uint16)
    g = ((words >> 5) & 0x1f).astype(np.uint16)
    b = (words & 0x1f).astype(np.uint16)
    # pal5bit: (v << 3) | (v >> 2)
    img = np.stack([(r << 3) | (r >> 2), (g << 3) | (g >> 2),
                    (b << 3) | (b >> 2)], axis=-1)
    return img.astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture_dir", help="dir with quads.bin + state dumps")
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-frame", type=int, default=0,
                    help="replay only quads from this frame on. The game "
                    "redraws the whole back page every cycle, so a small "
                    "window before the dump should fully cover the visible "
                    "page - and coverage is measured, not assumed.")
    args = ap.parse_args()
    cap = args.capture_dir
    out = args.out or cap

    meta = load_meta(os.path.join(cap, "meta.txt"))
    dump_frame = meta["frame"][0]
    vis_off = meta["visible_page_offset"][0]
    clip_right, clip_bottom = meta["visarea"]
    width, height = clip_right + 1, clip_bottom + 1

    ref_vram = np.fromfile(os.path.join(cap, "videoram.bin"), dtype="<u2")
    texram = np.fromfile(os.path.join(cap, "textureram.bin"), dtype=np.uint8)
    pal = np.fromfile(os.path.join(cap, "paletteram.bin"), dtype="<u4")
    print(f"state: videoram {ref_vram.nbytes>>20} MB, texram {len(texram)>>10} KB, "
          f"palette {len(pal)} words, dump frame {dump_frame}, "
          f"visible page 0x{vis_off:x}, {width}x{height}")

    raw = open(os.path.join(cap, "quads.bin"), "rb").read()
    assert raw[:4] == b"MVQ1", "bad quad log magic"
    rec = np.frombuffer(raw[4:len(raw) - (len(raw) - 4) % 38], dtype=np.uint8)
    rec = rec.reshape(-1, 38)
    frames = rec[:, 0:4].copy().view("<u4").ravel()
    pages = rec[:, 4:6].copy().view("<u2").ravel()
    dmas = rec[:, 6:38].copy().view("<u2").reshape(-1, 16)
    print(f"quad log: {len(rec)} quads across frames "
          f"{frames.min()}..{frames.max()}")

    # Replay the window up to and including the dump frame.
    keep = (frames <= dump_frame) & (frames >= args.min_frame)
    dmas, pages, frames = dmas[keep], pages[keep], frames[keep]
    print(f"replaying {len(dmas)} quads "
          f"(frames {args.min_frame}..{dump_frame})...")

    sim = np.zeros(0x80000, dtype=np.uint16)
    cover = np.zeros(0x80000, dtype=bool) if args.min_frame else None
    stats = {}
    for i in range(len(dmas)):
        mode, px = render_quad(dmas[i].astype(np.uint32), int(pages[i]),
                               sim, texram, clip_right, clip_bottom, cover)
        stats[mode] = stats.get(mode, 0) + 1
        if i % 20000 == 0:
            print(f"  {i}/{len(dmas)} quads (frame {frames[i]})")

    print("mode distribution:", dict(sorted(stats.items())))

    # ---- compare pages ----
    # The dump can fire mid page-flip, leaving meta's visible-page pointer one
    # step stale, and the final scene in the log is in-progress. The robust
    # target is structural: consecutive frames sharing a page_control form one
    # scene, and the last COMPLETE scene is the second-to-last such run (the
    # final run is the scene still being drawn when the dump fired). A
    # quad-count threshold is NOT robust - gameplay scene-start chunks grew
    # past 100 quads and broke it.
    if len(pages):
        runs = [int(pages[0])]
        for pc in pages[1:]:
            if int(pc) != runs[-1]:
                runs.append(int(pc))
        target_pc = runs[-2] if len(runs) >= 2 else runs[-1]
        vis_off = 0x40000 if (target_pc & 4) else 0x00000
        print(f"comparison page: 0x{vis_off:05x} "
              f"(dest of last complete scene, page_control {target_pc})")
    ref = ref_vram[vis_off:vis_off + 0x40000].reshape(512, 512)
    mine = sim[vis_off:vis_off + 0x40000].reshape(512, 512)
    ref_vis = ref[:height, :width]
    my_vis = mine[:height, :width]

    total = ref_vis.size
    if cover is not None:
        cov_vis = cover[vis_off:vis_off + 0x40000].reshape(512, 512)[:height, :width]
        covered = int(cov_vis.sum())
        print(f"coverage: {covered}/{total} = {100.0*covered/total:.2f}% of "
              f"visible pixels written by the replay window")

    exact = int((ref_vis == my_vis).sum())
    display = int(((ref_vis & 0x7fff) == (my_vis & 0x7fff)).sum())
    print(f"\npixel match (visible {width}x{height}):")
    print(f"  raw u16 : {exact}/{total} = {100.0*exact/total:.2f}%")
    print(f"  display : {display}/{total} = {100.0*display/total:.2f}%  (&0x7fff)")
    if cover is not None and covered:
        cm = cov_vis
        exact_c = int(((ref_vis == my_vis) & cm).sum())
        print(f"  covered : {exact_c}/{covered} = {100.0*exact_c/covered:.2f}%"
              f"  (raw match within written pixels)")

    from PIL import Image
    Image.fromarray(to_rgb(ref_vis, pal)).save(os.path.join(out, "reference.png"))
    Image.fromarray(to_rgb(my_vis, pal)).save(os.path.join(out, "rerendered.png"))
    diff = np.zeros((height, width, 3), dtype=np.uint8)
    mism = (ref_vis & 0x7fff) != (my_vis & 0x7fff)
    diff[..., 0] = np.where(mism, 255, 0)
    diff[..., 1] = np.where(~mism, 40, 0)
    Image.fromarray(diff).save(os.path.join(out, "diff.png"))
    print(f"wrote reference.png / rerendered.png / diff.png -> {out}")

    return 0 if display / total > 0.90 else 1


if __name__ == "__main__":
    sys.exit(main())
