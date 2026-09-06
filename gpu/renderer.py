"""GPU renderer prototype for the midvunit quad stream (moderngl / OpenGL 4.3).

Architecture - what the real port's renderer would do, exercised offline:

  one scene (one page_control run) -> ONE draw call
    - each quad becomes 2 triangles covering its bounding box; all quad data
      rides as flat varyings (positions already nudged per
      make_vertices_inclusive on the CPU, in float32)
    - the fragment shader ports poly.h analytically: the forward/backward
      edge walk, per-scanline extents with round_coordinate's
      midpoint-toward--inf rule, param interpolation with left-clip
      adjustment, and midvunit's four fill modes + dither mask. Pixels
      outside MAME's coverage are discarded, so GPU rasterization rules
      never leak in.
    - output is an R16UI *index* framebuffer - the game's palette-index
      space, exactly like the hardware framebuffer
  palette pass: full-screen triangle, index -> pal5bit RGB

  exact mode (scale=1): u/v use MAME's integer-DDA semantics
      (float32 start/step truncated to int32, stepped per pixel), so the
      output is comparable WORD FOR WORD with MAME's videoram dump.
  quality mode (scale>1): u/v interpolated in float at sub-pixel
      precision, coverage evaluated continuously -> clean edges at 4x,
      optional 16:9 margins. This is the shipping configuration.

Usage:
  python gpu/renderer.py results/capture-8000            # verify vs MAME
  python gpu/renderer.py results/capture-8000 --scale 4 --wide
"""
import argparse
import os
import sys
import time

import moderngl
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "harness"))
from rasterize import make_vertices_inclusive, load_meta  # noqa: E402

F = np.float32

VS = """
#version 430
uniform vec2 uCanvas;      // coarse canvas size (W, H)
in vec2 in_corner;         // bbox corner, coarse pixel space
in vec2 in_v0; in vec2 in_v1; in vec2 in_v2; in vec2 in_v3;
in vec4 in_uv01;           // u0,v0,u1,v1
in vec4 in_uv23;           // u2,v2,u3,v3
in vec4 in_uvBounds;       // original u min/max, v min/max before dilation
in uvec4 in_meta;          // pixdata, mode, dither, texbase
flat out vec2 v0; flat out vec2 v1; flat out vec2 v2; flat out vec2 v3;
flat out vec4 uv01; flat out vec4 uv23;
flat out vec4 uvBounds;
flat out uvec4 meta;
void main() {
    v0 = in_v0; v1 = in_v1; v2 = in_v2; v3 = in_v3;
    uv01 = in_uv01; uv23 = in_uv23; uvBounds = in_uvBounds; meta = in_meta;
    // y-down pixel space -> NDC (y flipped)
    gl_Position = vec4(in_corner.x / uCanvas.x * 2.0 - 1.0,
                       1.0 - in_corner.y / uCanvas.y * 2.0, 0.0, 1.0);
}
"""

FS = """
#version 430
uniform int  uScale;       // 1 = exact mode, >1 = quality mode
uniform vec2 uCanvas;      // coarse canvas size
uniform int  uClipRight;   // coarse cliprect right (W-1)
uniform usampler2D texram; // 4096-wide R8UI, 8 MB of texture RAM
uniform int  texMask;      // byte-size mask (size-1)
uniform int  uDbgQuadId;   // debug: if 1, outIndex = quad id (gl_PrimitiveID/2)
uniform int  uBgMargin;    // coarse margin width; backdrop quads discarded
                           // inside the margins so extend fills from the
                           // 4:3 boundary (sky above, terrain below). 0=off.
uniform int  uClipW;       // coarse canvas width (for the right margin)
flat in vec2 v0; flat in vec2 v1; flat in vec2 v2; flat in vec2 v3;
flat in vec4 uv01; flat in vec4 uv23;
flat in vec4 uvBounds;
flat in uvec4 meta;
layout(location = 0) out uint outIndex;
layout(location = 1) out uint outMask;   // 1 = this scene wrote the pixel

int round_coord(float f) {           // poly.h: floor, +1 iff frac > 0.5
    float ip = floor(f);
    return int(ip) + (((f - ip) > 0.5) ? 1 : 0);
}
int c_int32(float f) {               // C float->int32: trunc, OOR -> INT_MIN
    if (!(abs(f) < 2147483648.0)) return -2147483648;
    return int(f);
}
uint fetch_texel(int idx) {
    idx &= texMask;
    return texelFetch(texram, ivec2(idx & 4095, idx >> 12), 0).r;
}

void main() {
    vec2 vx[4] = vec2[4](v0, v1, v2, v3);
    float fx = gl_FragCoord.x;
    float fy = uCanvas.y * float(uScale) - gl_FragCoord.y;   // y-down
    float cx = fx / float(uScale);
    float cy = fy / float(uScale);
    int px = int(floor(cx));
    int py = int(floor(cy));
    // exact mode evaluates at MAME's scanline centre; quality mode uses the
    // fine fragment's own continuous coordinate
    precise float fully = (uScale == 1) ? float(py) + 0.5 : cy;

    // ---- min/max Y vertices (poly.h render_polygon) ----
    int minv = 0, maxv = 0;
    for (int i = 1; i < 4; i++) {
        if (vx[i].y < vx[minv].y) minv = i;
        else if (vx[i].y > vx[maxv].y) maxv = i;
    }
    if (uScale == 1 && round_coord(vx[maxv].y) - round_coord(vx[minv].y) <= 0) discard;
    float maxvy = vx[maxv].y;

    // poly.h renders scanlines [round(miny), round(maxy)) only - the expanded
    // bounding box generates fragments beyond that, where extrapolated edges
    // still yield plausible x-extents. Without this cut, later quads steal
    // their neighbours' shared-edge rows.
    if (uScale == 1) {
        if (py < round_coord(vx[minv].y) || py >= round_coord(maxvy)) discard;
    } else {
        if (cy < vx[minv].y || cy >= maxvy) discard;
    }

    // ---- forward / backward edge lists (<=3 each) ----
    // e[k] = (v1x, v1y, v2y, dxdy), p[k] = (u1, v1_p, dudy, dvdy)
    precise vec4 fe[3]; precise vec4 fp[3]; int fn = 0;
    precise vec4 be[3]; precise vec4 bp[3]; int bn = 0;
    vec4 uvs[4] = vec4[4](vec4(uv01.xy, 0, 0), vec4(uv01.zw, 0, 0),
                          vec4(uv23.xy, 0, 0), vec4(uv23.zw, 0, 0));
    for (int curv = minv; curv != maxv; curv = (curv + 1) & 3) {
        int nxt = (curv + 1) & 3;
        if (vx[nxt].y != vx[curv].y) {
            precise float ooy = 1.0 / (vx[nxt].y - vx[curv].y);
            fe[fn] = vec4(vx[curv].x, vx[curv].y, vx[nxt].y,
                          (vx[nxt].x - vx[curv].x) * ooy);
            fp[fn] = vec4(uvs[curv].xy,
                          (uvs[nxt].x - uvs[curv].x) * ooy,
                          (uvs[nxt].y - uvs[curv].y) * ooy);
            fn++;
        }
    }
    for (int curv = minv; curv != maxv; curv = (curv - 1) & 3) {
        int nxt = (curv - 1) & 3;
        if (vx[nxt].y != vx[curv].y) {
            precise float ooy = 1.0 / (vx[nxt].y - vx[curv].y);
            be[bn] = vec4(vx[curv].x, vx[curv].y, vx[nxt].y,
                          (vx[nxt].x - vx[curv].x) * ooy);
            bp[bn] = vec4(uvs[curv].xy,
                          (uvs[nxt].x - uvs[curv].x) * ooy,
                          (uvs[nxt].y - uvs[curv].y) * ooy);
            bn++;
        }
    }
    if (fn == 0 || bn == 0) discard;

    // ---- left/right decision (poly.h:1194) ----
    bool sharedFirst = (fe[0].x == be[0].x) && (fe[0].y == be[0].y);
    bool fwd_left = (sharedFirst && fe[0].w < be[0].w)
                 || (!sharedFirst && fe[0].x < be[0].x);

    // ---- advance to the edge pair spanning this scanline ----
    int li = 0, ri = 0;
    vec4 le, lp, re, rp;
    if (fwd_left) {
        while (fully > fe[li].z && fully < maxvy && li + 1 < fn) li++;
        while (fully > be[ri].z && fully < maxvy && ri + 1 < bn) ri++;
        le = fe[li]; lp = fp[li]; re = be[ri]; rp = bp[ri];
    } else {
        while (fully > be[li].z && fully < maxvy && li + 1 < bn) li++;
        while (fully > fe[ri].z && fully < maxvy && ri + 1 < fn) ri++;
        le = be[li]; lp = bp[li]; re = fe[ri]; rp = fp[ri];
    }

    precise float startx = le.x + (fully - le.y) * le.w;
    precise float stopx  = re.x + (fully - re.y) * re.w;
    int istartx = round_coord(startx);
    int istopx  = round_coord(stopx);
    if (istartx > istopx) { int t = istartx; istartx = istopx; istopx = t; }

    // ---- params at this scanline (poly.h:1250) ----
    precise float ldy = fully - le.y;
    precise float rdy = fully - re.y;
    precise float oox = 1.0 / (stopx - startx);
    precise float lu = lp.x + ldy * lp.z;
    precise float lv = lp.y + ldy * lp.w;
    precise float dudx = (rp.x + rdy * rp.z - lu) * oox;
    precise float dvdx = (rp.y + rdy * rp.w - lv) * oox;
    precise float su = lu + (float(istartx) + 0.5 - startx) * dudx;
    precise float sv = lv + (float(istartx) + 0.5 - startx) * dvdx;

    // ---- left/right clip with param adjust ----
    if (istartx < 0) {
        su += float(-istartx) * dudx;
        sv += float(-istartx) * dvdx;
        istartx = 0;
    }
    if (istopx > uClipRight) istopx = uClipRight + 1;
    // A native-empty span may still cover fine samples. Reject by rounded
    // integer extent only in exact mode; quality coverage is continuous below.
    if (uScale == 1 && istartx >= istopx) discard;

    // ---- coverage ----
    if (uScale == 1) {
        if (px < istartx || px >= istopx) discard;
    } else {
        // continuous edges at fine resolution; clip window still applies
        float lo = max(min(startx, stopx), 0.0);
        float hi = min(max(startx, stopx), float(uClipRight + 1));
        if (cx < lo || cx >= hi) discard;
    }

    uint pixdata = meta.x, mode = meta.y, dither = meta.z & 1u;
    // parked screen-space UI (meta bit 2, set only in wide builds): panels
    // the game slides in from past the 4:3 edge (crusnwld radio) park fully
    // off-screen where the hardware raster crop hid them - never draw the
    // parked position; sliding/deployed quads straddle x=511 and stay.
    if ((meta.z & 4u) != 0u) discard;
    bool backdrop = (meta.z & 2u) != 0u;
    // suppress backdrop (sky/horizon band) in the 16:9 margins: leaves the
    // pixel unwritten so the margin-extend fills it from the 4:3 boundary
    // column - sky in the upper margin, terrain in the lower (covers the
    // "water through the ground" reveal). Terrain/rock quads are unaffected.
    if (backdrop && uBgMargin > 0 && (px < uBgMargin || px >= uClipW - uBgMargin))
        discard;
    // dither = the hardware's 50% translucency (shadows, HUD boxes, the
    // radio panel, sprite backboards). At native scale the mask is the
    // authentic coarse checkerboard (identical to fine there - exact mode
    // stays bit-perfect); at higher internal scales mask at FINE pixel
    // granularity so it reads as the smoked glass the CRT made of it
    // instead of chunky 4x4 blocks.
    if (dither == 1u) {
        // fine coords in the same y-down space as px/py (fx,fy above);
        // at uScale==1 these ARE px,py - exact mode stays bit-perfect
        int fdx = int(fx);
        int fdy = int(floor(fy));
        if (((fdx ^ fdy) & 1) != 0) discard;
    }

    outMask = 1u;   // every non-discarded fragment marks its pixel written
    if (mode == 0u) {
        outIndex = (uDbgQuadId == 1) ? uint(gl_PrimitiveID / 2) : pixdata & 0xffffu;
        return;
    }

    int ui, vi;
    if (uScale == 1) {   // MAME's integer DDA, analytically
        ui = c_int32(su) + (px - istartx) * c_int32(dudx);
        vi = c_int32(sv) + (px - istartx) * c_int32(dvdx);
    } else {             // sub-pixel float interpolation
        // Coverage dilation must not read another tile in texture RAM.
        // A one-pixel-tall distant road quad can extrapolate by 80 texels;
        // clamping to its original UV domain retains the interior gradient
        // and extends only its edge texel. Native DDA remains unchanged.
        ui = c_int32(clamp(lu + (cx - startx) * dudx, uvBounds.x, uvBounds.y));
        vi = c_int32(clamp(lv + (cx - startx) * dvdx, uvBounds.z, uvBounds.w));
    }
    uint texel = fetch_texel(int(meta.w) + ((vi >> 8) & 0xff00) + (ui >> 16));
    if (mode == 1u)      outIndex = (pixdata + texel) & 0xffffu;
    else if (mode == 2u) { if (texel == 0u) discard;
                           outIndex = (pixdata + texel) & 0xffffu; }
    else                 { if (texel == 0u) discard;
                           outIndex = pixdata & 0xffffu; }
    // Ownership must respect transparent texels, just like the real draw.
    if (uDbgQuadId == 1) outIndex = uint(gl_PrimitiveID / 2);
}
"""

PAL_VS = """
#version 430
out vec2 uv;
void main() {  // full-screen triangle
    vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
    uv = p;
    gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}
"""

PAL_FS = """
#version 430
uniform usampler2D idxTex;
uniform usampler2D palTex;   // 256x128 R32UI - 32768 palette words
uniform int uCrop;           // fine pixels to crop from each side (2D screens)
uniform int uCrt;            // 1 = CRT pass (mask+scanline+curvature), 0 = raw
uniform float uSrcH;         // simulated source scanline count (coarse height)
uniform usampler2D maskTex;  // R8UI: 1 = written by the CURRENT scene
uniform int uFillR;          // crack-fill search radius in fine px; 0 = off
uniform int uMargin;         // margin width in fine px for clamp-extend; 0 = off
in vec2 uv;
out vec4 color;

ivec2 fill_px(ivec2 p) {
    // Crack fill: the hardware leaves sub-pixel gaps between adjacent quads
    // where the page's PREVIOUS frame shows through (authentic, but it
    // shimmers). An unwritten pixel is redirected to its nearest written
    // neighbour - only when written pixels exist on BOTH sides along some
    // axis (a true between-polys crack). One-sided pixels (silhouettes
    // against the cleared 16:9 margins) are left untouched.
    if (uFillR == 0 || texelFetch(maskTex, p, 0).r != 0u) return p;
    ivec2 sz = textureSize(maskTex, 0);
    int dl = 0, dr = 0, du = 0, dd = 0;
    for (int i = 1; i <= uFillR; i++) {
        if (dl == 0 && p.x - i >= 0
            && texelFetch(maskTex, p - ivec2(i, 0), 0).r != 0u) dl = i;
        if (dr == 0 && p.x + i < sz.x
            && texelFetch(maskTex, p + ivec2(i, 0), 0).r != 0u) dr = i;
        if (du == 0 && p.y - i >= 0
            && texelFetch(maskTex, p - ivec2(0, i), 0).r != 0u) du = i;
        if (dd == 0 && p.y + i < sz.y
            && texelFetch(maskTex, p + ivec2(0, i), 0).r != 0u) dd = i;
    }
    // fine-dither translucency leaves a 1-px checkerboard: all four axis
    // neighbours written, all four diagonals unwritten. That is
    // translucency, not a crack - never fill it.
    if (dl == 1 && dr == 1 && du == 1 && dd == 1
        && p.x > 0 && p.y > 0 && p.x + 1 < sz.x && p.y + 1 < sz.y
        && texelFetch(maskTex, p + ivec2( 1,  1), 0).r == 0u
        && texelFetch(maskTex, p + ivec2( 1, -1), 0).r == 0u
        && texelFetch(maskTex, p + ivec2(-1,  1), 0).r == 0u
        && texelFetch(maskTex, p + ivec2(-1, -1), 0).r == 0u) return p;
    int wh = (dl > 0 && dr > 0) ? dl + dr : 1 << 20;
    int wv = (du > 0 && dd > 0) ? du + dd : 1 << 20;
    if (min(wh, wv) >= (1 << 20)) {
        // not a crack. Margin extend: the 16:9 margins show black holes
        // where the game's 4:3-era culling never drew - clamp-extend the
        // nearest written hardware-boundary pixel. The outermost COVERED
        // column sits a couple of fine pixels inside the nominal edge
        // (vertices carry a +0.5 coarse offset), so probe a short inward
        // run rather than the exact edge column.
        if (uMargin > 0) {
            if (p.x < uMargin + 8) {
                int start = max(p.x + 1, uMargin);
                for (int k = start; k <= uMargin + 8; k++) {
                    ivec2 q = ivec2(k, p.y);
                    if (texelFetch(maskTex, q, 0).r != 0u) return q;
                }
            } else if (p.x >= sz.x - uMargin - 8) {
                int start = min(p.x - 1, sz.x - 1 - uMargin);
                for (int k = start; k >= sz.x - 1 - uMargin - 8; k--) {
                    ivec2 q = ivec2(k, p.y);
                    if (texelFetch(maskTex, q, 0).r != 0u) return q;
                }
            }
        }
        return p;
    }
    if (wh <= wv) return p + ((dl <= dr) ? ivec2(-dl, 0) : ivec2(dr, 0));
    return p + ((du <= dd) ? ivec2(0, -du) : ivec2(0, dd));
}

vec3 fetch_at(ivec2 p) {
    p = fill_px(p);
    uint pen = texelFetch(idxTex, p, 0).r & 0x7fffu;
    uint w = texelFetch(palTex, ivec2(pen & 255u, pen >> 8), 0).r;
    uint r = (w >> 10) & 31u, g = (w >> 5) & 31u, b = w & 31u;
    return vec3(float((r << 3) | (r >> 2)) / 255.0,
                float((g << 3) | (g >> 2)) / 255.0,
                float((b << 3) | (b >> 2)) / 255.0);
}

ivec2 src_px(vec2 tuv) {
    ivec2 sz = textureSize(idxTex, 0);
    return ivec2(float(uCrop) + tuv.x * float(sz.x - 2 * uCrop),
                 tuv.y * float(sz.y));
}

vec3 fetch_rgb(vec2 tuv) { return fetch_at(src_px(tuv)); }

void main() {
    if (uCrt == 0) {                       // raw path - untouched product look
        color = vec4(fetch_rgb(uv), 1.0);
        return;
    }

    // ---- tube geometry: gentle barrel warp, black outside the glass ----
    vec2 c = uv * 2.0 - 1.0;
    c *= vec2(1.0 + 0.041 * c.y * c.y, 1.0 + 0.052 * c.x * c.x);
    vec2 wuv = c * 0.5 + 0.5;
    if (any(lessThan(wuv, vec2(0.0))) || any(greaterThan(wuv, vec2(1.0)))) {
        color = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }
    // ---- horizontal beam softness: 3-tap blur in fine pixels ----
    ivec2 p = src_px(wuv);
    int s = max(1, int(float(textureSize(idxTex, 0).y) / uSrcH * 0.45));
    vec3 rgb = 0.5 * fetch_at(p)
             + 0.25 * fetch_at(p + ivec2(s, 0))
             + 0.25 * fetch_at(p - ivec2(s, 0));

    // ---- scanlines: gaussian beam per source line, bright beams bloom ----
    float d = fract(wuv.y * uSrcH) - 0.5;
    float lum = dot(rgb, vec3(0.299, 0.587, 0.114));
    float width = mix(0.35, 0.65, lum);
    float scan = exp(-(d * d) / (2.0 * width * width));

    // ---- shadow mask: two-phase magenta/green (rainbow-free at any res) ----
    vec3 mask = ((int(gl_FragCoord.x) & 1) == 0)
        ? vec3(1.0, 0.62, 1.0) : vec3(0.62, 1.0, 0.62);

    // ---- rounded corners + vignette ----
    vec2 cc = abs(wuv * 2.0 - 1.0);
    float cornerd = length(max(cc - vec2(0.94), 0.0)) / 0.06;
    float cornerm = 1.0 - smoothstep(0.8, 1.0, cornerd);
    float vig = 1.0 - 0.10 * dot(cc, cc);

    rgb *= scan * cornerm * vig * 1.42;
    color = vec4(min(rgb * mask, 1.0), 1.0);
}
"""


MENU_VS = """
#version 430
uniform vec4 uRect;    // x, y, w, h in window pixels, y-down from top-left
uniform vec2 uScreen;  // window size
out vec2 uv;
void main() {
    vec2 p = vec2(float(gl_VertexID & 1), float((gl_VertexID >> 1) & 1));
    uv = p;
    vec2 px = uRect.xy + p * uRect.zw;
    gl_Position = vec4(px.x / uScreen.x * 2.0 - 1.0,
                       1.0 - px.y / uScreen.y * 2.0, 0.0, 1.0);
}
"""

MENU_FS = """
#version 430
uniform sampler2D uTex;   // A8 label bitmap
uniform vec4 uColor;      // rgb tint, a = opacity
uniform int uSolid;       // 1 = ignore texture (solid fill)
in vec2 uv;
out vec4 color;
void main() {
    float a = (uSolid == 1) ? 1.0 : texture(uTex, uv).r;
    color = vec4(uColor.rgb, uColor.a * a);
}
"""


def load_scene(cap, history=True):
    """Return (quads, page_control, meta) for the last complete scene.

    With history=True the previous scene rendered to the SAME page is
    prepended. The game leaves sub-pixel cracks between adjacent quads
    (3 px on the canyon scene) where the hardware shows whatever the page
    held from the frame before - a real renderer never clears pages, so it
    reproduces this for free; an isolated-scene replay must prepend the
    prior same-page scene to match MAME bit-for-bit.
    """
    meta = load_meta(os.path.join(cap, "meta.txt"))
    raw = open(os.path.join(cap, "quads.bin"), "rb").read()
    rec = np.frombuffer(raw[4:len(raw) - (len(raw) - 4) % 38], dtype=np.uint8)
    rec = rec.reshape(-1, 38)
    pages = rec[:, 4:6].copy().view("<u2").ravel()
    dmas = rec[:, 6:38].copy().view("<u2").reshape(-1, 16)
    change = np.flatnonzero(np.diff(pages.astype(np.int32)) != 0) + 1
    starts = np.concatenate([[0], change])
    ends = np.concatenate([change, [len(pages)]])
    s, e = starts[-2], ends[-2]
    quads = dmas[s:e]
    nhist = 0
    if history and len(starts) >= 4:
        ps, pe = starts[-4], ends[-4]
        assert int(pages[ps]) == int(pages[s]), "page alternation broke"
        quads = np.concatenate([dmas[ps:pe], quads])
        nhist = int(pe - ps)
    return quads, int(pages[s]), meta, nhist


def _dilate_rect(vx, vy, ix, iy, us=None, vs=None):
    """Half-pixel outward dilation for one strict axis-aligned rectangle.

    Quality mode's continuous coverage ends at the vertex CENTERS, so two
    adjacent 2D tiles each half-cover their shared boundary columns and
    whatever lies underneath grooves through the seam (the crusnusa
    continue-map vertical line; offroadc's track-select lines, G4). The
    hardware DDA fills both endpoint pixels inclusively - expanding every
    side outward to the pixel's outer edge (0.5, +0.001 guard against
    coincident-edge tie rules) reproduces that span exactly: adjacent
    tiles then partition the fine pixels with no gap and no overlap.
    Exact/DDA mode never calls this (bit-exactness by construction).

    us/vs (textured quads): the texture params are extrapolated along
    each axis by the same amount, so du/dx and dv/dy - and therefore
    which texel every fine pixel samples - stay exactly the hardware's.
    Moving the vertices alone squeezed each tile's texture inward by up
    to half a texel and DOUBLED the quality-vs-hardware pixel mismatch
    on the continue map (15.3% -> 30.6%, review 2026-08-30)."""
    E = 0.501
    if (ix[0] == ix[1] and ix[2] == ix[3]
            and iy[1] == iy[2] and iy[3] == iy[0]):
        sides_x = ((0, 1), (2, 3))
        sides_y = ((1, 2), (3, 0))
        pairs_x = ((0, 3), (1, 2))   # same-y partners across x
        pairs_y = ((1, 0), (2, 3))   # same-x partners across y
    elif (iy[0] == iy[1] and iy[2] == iy[3]
            and ix[1] == ix[2] and ix[3] == ix[0]):
        sides_x = ((3, 0), (1, 2))
        sides_y = ((0, 1), (2, 3))
        pairs_x = ((0, 1), (3, 2))
        pairs_y = ((0, 3), (1, 2))
    else:
        return
    for (a, b), (c, d), v, s, pairs in (
            (sides_x[0], sides_x[1], vx, ix, pairs_x),
            (sides_y[0], sides_y[1], vy, iy, pairs_y)):
        e = E if s[a] <= s[c] else -E
        if us is not None:
            # float32 throughout, multiply-by-reciprocal - the exact
            # formulation of build_vertices_fast, so both builders stay
            # bit-identical (u/v sit near 2^23 where float64 rounding
            # differs by 0.5)
            e32 = F(e)
            for p, q in pairs:        # p moves by -e, q by +e
                span = F(F(v[q]) - F(v[p]))
                if span != 0.0:
                    inv = F(F(1.0) / span)
                    for arr in (us, vs):
                        g = F(F(F(arr[q]) - F(arr[p])) * inv)
                        arr[p] = F(F(arr[p]) - F(e32 * g))
                        arr[q] = F(F(arr[q]) + F(e32 * g))
        v[a] -= e
        v[b] -= e
        v[c] += e
        v[d] += e


def build_vertices(quads, xoff, dilate2d=False, positions=None):
    """Quad records -> interleaved GPU vertex data (6 verts per quad).

    dilate2d: half-pixel dilation of axis-aligned rects (quality mode
    only - see _dilate_rect). Exact mode MUST leave it False."""
    n = len(quads)
    fdata = np.zeros((n * 6, 22), dtype=np.float32)
    udata = np.zeros((n * 6, 4), dtype=np.uint32)
    for q in range(n):
        dma = quads[q].astype(np.uint32)
        vx = [F(np.int16(dma[2 + i * 2]) + F(0.5) + F(xoff)) for i in range(4)]
        vy = [F(np.int16(dma[3 + i * 2]) + F(0.5)) for i in range(4)]
        if positions is not None:
            vx = [F(positions[q, i, 0] + F(.5) + F(xoff)) for i in range(4)]
            vy = [F(positions[q, i, 1] + F(.5)) for i in range(4)]
        pixdata = int(dma[1])
        textured = (dma[0] & 0x300) == 0x100
        dither = 1 if (dma[0] & 0x2000) else 0
        # backdrop (sky/horizon band): per-game texbase low byte AND
        # full-width (excludes incidental small quads) - distinct from
        # terrain/rock; flagged into meta bit 1 for 16:9-margin suppress.
        # offroadc 0x7f, crusnusa 0x56, crusnwld 0xc5 (verified: exactly the
        # sky quads, no terrain false positives).
        _wx = [int(np.int16(dma[2 + i * 2])) for i in range(4)]
        if (int(dma[14]) & 0xff) in (0x56, 0x7f, 0xc5) and (max(_wx) - min(_wx)) > 200:
            dither |= 2
        # parked screen-space UI (see shader): untextured, fully right of
        # the 4:3 edge, in the HUD band - wide builds only (exact mode
        # keeps bit clear, preserving bit-exactness by construction)
        # dithered panel or tiny indicator dot only - moving untextured
        # margin objects (USA traffic shadows/LOD, ~20px) must stay
        if xoff > 0 and not textured and min(_wx) >= 512:
            _wy = [int(np.int16(dma[3 + i * 2])) for i in range(4)]
            small = (max(_wx) - min(_wx)) <= 8 and (max(_wy) - min(_wy)) <= 8
            if min(_wy) >= 60 and max(_wy) <= 260 and ((dither & 1) or small):
                dither |= 4
        if not textured:
            mode = 0
            pixdata = (pixdata + (dma[0] & 0xff)) & 0xffff
            us = vs = [0.0] * 4
        else:
            us = [float(F(F(dma[10 + i] & 0xff) * F(65536.0) + F(32768.0)))
                  for i in range(4)]
            vs = [float(F(F(dma[10 + i] >> 8) * F(65536.0) + F(32768.0)))
                  for i in range(4)]
            sel = dma[0] & 0xc00
            if sel == 0x000:
                mode = 1
            elif sel == 0x800:
                mode = 2
            elif sel == 0xc00:
                mode = 3
                pixdata = (pixdata + (dma[0] & 0xff)) & 0xffff
            else:
                mode = 0
                pixdata = (pixdata + (dma[0] & 0xff)) & 0xffff
        bounds = [min(us), max(us), min(vs), max(vs)]
        make_vertices_inclusive(vx, vy)
        if dilate2d:
            _iy = [int(np.int16(dma[3 + i * 2])) for i in range(4)]
            if textured:
                us, vs = list(us), list(vs)
                _dilate_rect(vx, vy, _wx, _iy, us, vs)
            else:
                _dilate_rect(vx, vy, _wx, _iy)

        x0, x1 = min(vx) - 1.0, max(vx) + 1.0
        y0, y1 = min(vy) - 1.0, max(vy) + 1.0
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y0), (x1, y1), (x0, y1)]
        row = ([c for i in range(4) for c in (float(vx[i]), float(vy[i]))]
               + [us[0], vs[0], us[1], vs[1], us[2], vs[2], us[3], vs[3]])
        base = q * 6
        for k in range(6):
            fdata[base + k, 0:2] = corners[k]
            fdata[base + k, 2:18] = row
            fdata[base + k, 18:22] = bounds
        udata[base:base + 6] = (pixdata, mode, dither, int(dma[14]) * 256)
    return fdata, udata


def build_vertices_fast(quads, xoff, dilate2d=False):
    """Vectorized build_vertices - identical output, no per-quad Python loop.

    The live viewer calls this per scene at 57 Hz; the scalar version costs
    ~65 ms for 1,300 quads, this costs ~2 ms.
    """
    n = len(quads)
    dma = np.asarray(quads, dtype=np.uint32)
    vx = (dma[:, 2:10:2].astype(np.int16).astype(np.float32)
          + np.float32(0.5) + np.float32(xoff))
    vy = (dma[:, 3:10:2].astype(np.int16).astype(np.float32)
          + np.float32(0.5))

    textured = (dma[:, 0] & 0x300) == 0x100
    sel = dma[:, 0] & 0xc00
    dither = ((dma[:, 0] & 0x2000) != 0).astype(np.uint32)
    # backdrop: per-game texbase low byte AND full-width (see build_vertices)
    _wvx = dma[:, 2:10:2].astype(np.int16)
    _wwide = (_wvx.max(axis=1).astype(np.int32) - _wvx.min(axis=1)) > 200
    _lb = dma[:, 14] & 0xff
    _isbg = ((_lb == 0x56) | (_lb == 0x7f) | (_lb == 0xc5)) & _wwide
    dither |= (_isbg.astype(np.uint32) << 1)
    if xoff > 0:
        # parked screen-space UI (see build_vertices / shader): dithered
        # panel or tiny indicator dot only
        _wvy = dma[:, 3:10:2].astype(np.int16)
        _small = ((_wvx.max(axis=1) - _wvx.min(axis=1)) <= 8)             & ((_wvy.max(axis=1) - _wvy.min(axis=1)) <= 8)
        _parked = (~textured) & (_wvx.min(axis=1) >= 512)             & (_wvy.min(axis=1) >= 60) & (_wvy.max(axis=1) <= 260)             & (((dither & 1) != 0) | _small)
        dither |= (_parked.astype(np.uint32) << 2)
    mode = np.zeros(n, dtype=np.uint32)
    mode[textured & (sel == 0x000)] = 1
    mode[textured & (sel == 0x800)] = 2
    mode[textured & (sel == 0xc00)] = 3
    # 0x400 = invalid textured combo -> flat (mode stays 0)
    addpix = (~textured) | (textured & (sel == 0xc00)) | (textured & (sel == 0x400))
    pixdata = np.where(addpix, (dma[:, 1] + (dma[:, 0] & 0xff)) & 0xffff,
                       dma[:, 1]).astype(np.uint32)

    us = ((dma[:, 10:14] & 0xff).astype(np.float32) * np.float32(65536.0)
          + np.float32(32768.0))
    vs = ((dma[:, 10:14] >> 8).astype(np.float32) * np.float32(65536.0)
          + np.float32(32768.0))
    us[~textured] = 0.0
    vs[~textured] = 0.0
    bounds = np.stack((us.min(axis=1), us.max(axis=1), vs.min(axis=1), vs.max(axis=1)), axis=1)

    # ---- make_vertices_inclusive, vectorized ----
    nx = [1, 2, 3, 0]
    vxn, vyn = vx[:, nx], vy[:, nx]
    eq = (vyn == vy) & (vxn == vx)
    rmask = (vyn > vy) | ((vyn == vy) & (vxn < vx))
    bmask = (vxn < vx) | ((vxn == vx) & (vyn < vy))
    all_eq = eq.all(axis=1)
    # eff vertex: first non-eq walking forward (<=3 steps)
    eff = np.tile(np.arange(4, dtype=np.int64), (n, 1))
    for _ in range(3):
        stuck = np.take_along_axis(eq, eff % 4, axis=1)
        eff = np.where(stuck, eff + 1, eff)
    eff %= 4
    radj = np.take_along_axis(rmask, eff, axis=1) & ~all_eq[:, None]
    badj = np.take_along_axis(bmask, eff, axis=1) & ~all_eq[:, None]
    vx = np.where(radj, (vx + np.float32(0.001)).astype(np.float32), vx)
    vy = np.where(badj, (vy + np.float32(0.001)).astype(np.float32), vy)

    if dilate2d:
        # ---- _dilate_rect, vectorized (see the scalar version) ----
        E = np.float32(0.501)
        ix = dma[:, 2:10:2].astype(np.int16)
        iy = dma[:, 3:10:2].astype(np.int16)
        pa = ((ix[:, 0] == ix[:, 1]) & (ix[:, 2] == ix[:, 3])
              & (iy[:, 1] == iy[:, 2]) & (iy[:, 3] == iy[:, 0]))
        pb = ((iy[:, 0] == iy[:, 1]) & (iy[:, 2] == iy[:, 3])
              & (ix[:, 1] == ix[:, 2]) & (ix[:, 3] == ix[:, 0]))
        pb &= ~pa   # degenerate quads match both; scalar elif picks A
        for mask, sx, sy, px_, py_ in (
                (pa, ((0, 1), (2, 3)), ((1, 2), (3, 0)),
                 ((0, 3), (1, 2)), ((1, 0), (2, 3))),
                (pb, ((3, 0), (1, 2)), ((0, 1), (2, 3)),
                 ((0, 1), (3, 2)), ((0, 3), (1, 2)))):
            if not mask.any():
                continue
            for (a, b), (c, d), v, s, pairs in ((sx[0], sx[1], vx, ix, px_),
                                                (sy[0], sy[1], vy, iy, py_)):
                e = np.where(s[:, a] <= s[:, c], E, -E) * mask
                # texture params ride along (see _dilate_rect); untextured
                # quads carry zero us/vs so this is a no-op for them
                for p, q in pairs:
                    span = v[:, q] - v[:, p]
                    ok = span != 0
                    inv = np.where(ok, 1.0 / np.where(ok, span, 1.0), 0.0)
                    for arr in (us, vs):
                        g = (arr[:, q] - arr[:, p]) * inv
                        arr[:, p] -= e * g
                        arr[:, q] += e * g
                v[:, a] -= e
                v[:, b] -= e
                v[:, c] += e
                v[:, d] += e

    # ---- bbox corners, 6 verts per quad ----
    x0 = vx.min(axis=1) - 1.0
    x1 = vx.max(axis=1) + 1.0
    y0 = vy.min(axis=1) - 1.0
    y1 = vy.max(axis=1) + 1.0
    corners = np.empty((n, 6, 2), dtype=np.float32)
    corners[:, 0] = np.stack([x0, y0], 1)
    corners[:, 1] = np.stack([x1, y0], 1)
    corners[:, 2] = np.stack([x1, y1], 1)
    corners[:, 3] = np.stack([x0, y0], 1)
    corners[:, 4] = np.stack([x1, y1], 1)
    corners[:, 5] = np.stack([x0, y1], 1)

    row = np.empty((n, 16), dtype=np.float32)
    row[:, 0:8:2] = vx
    row[:, 1:8:2] = vy
    row[:, 8:16:2] = us
    row[:, 9:16:2] = vs

    fdata = np.empty((n, 6, 22), dtype=np.float32)
    fdata[:, :, 0:2] = corners
    fdata[:, :, 2:18] = row[:, None, :]
    fdata[:, :, 18:22] = bounds[:, None, :]
    udata = np.empty((n, 6, 4), dtype=np.uint32)
    udata[:, :, 0] = pixdata[:, None]
    udata[:, :, 1] = mode[:, None]
    udata[:, :, 2] = dither[:, None]
    udata[:, :, 3] = (dma[:, 14] * 256)[:, None]
    return fdata.reshape(-1, 22), udata.reshape(-1, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture_dir")
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--crt", action="store_true",
                    help="CRT pass in the palette stage (preview only; "
                         "index-buffer verification is upstream of it)")
    ap.add_argument("--crackfill", action="store_true",
                    help="fill pixels the scene left unwritten (hardware "
                         "quad cracks showing the stale page) from bounded "
                         "neighbours - quality mode only")
    ap.add_argument("--marginfill", action="store_true",
                    help="explicit backdrop suppression and boundary-column extension experiment")
    ap.add_argument("--bench", type=int, default=0, help="timed re-renders")
    ap.add_argument("--report", help="write machine-readable verification JSON")
    ap.add_argument("--output-dir", help="write previews here instead of the capture directory")
    ap.add_argument("--no-png", action="store_true", help="verification only; do not write previews")
    ap.add_argument("--buffers", help="save indices, coverage and current-scene polygon ownership as NPZ")
    ap.add_argument("--align-tjunctions", action="store_true", help="offline quality-only experiment aligning closed, opaque textured T joins")
    args = ap.parse_args()
    if args.scale < 1 or args.bench < 0:
        ap.error("scale must be positive and bench must be non-negative")
    from verification import compare_arrays, write_json
    cap = args.capture_dir
    output_dir = args.output_dir or cap
    if not args.no_png:
        os.makedirs(output_dir, exist_ok=True)
    S = args.scale
    exact = (S == 1 and not args.wide)
    if args.align_tjunctions and S == 1:
        ap.error("T-junction experiment requires quality scale > 1")

    quads, pc, meta, nhist = load_scene(cap)
    height = meta["visarea"][1] + 1
    margin = 86 if args.wide else 0
    W = 512 + 2 * margin
    print(f"scene: {len(quads)} quads, page_control {pc}, canvas {W}x{height} "
          f"scale {S} ({'exact/DDA' if exact else 'quality'} mode)")

    texram = np.fromfile(os.path.join(cap, "textureram.bin"), dtype=np.uint8)
    pal = np.fromfile(os.path.join(cap, "paletteram.bin"), dtype="<u4")

    ctx = moderngl.create_context(standalone=True, require=430)
    print("GL:", ctx.info["GL_RENDERER"])

    # texture RAM as a 4096-wide R8UI texture; palette as 256x128 R32UI
    texsize = len(texram)
    tex2d = ctx.texture((4096, texsize // 4096), 1, texram.tobytes(),
                        dtype="u1", alignment=1)
    paltex = ctx.texture((256, 128), 1, pal.astype("<u4").tobytes(), dtype="u4")

    prog = ctx.program(vertex_shader=VS, fragment_shader=FS)
    prog["uCanvas"].value = (float(W), float(height))
    prog["uScale"].value = S
    # exact/native mode honors the hardware cliprect (offroadc's visarea is
    # 511 wide - right edge x=510); wide mode deliberately unclips into the
    # margins, which is the whole point
    prog["uClipRight"].value = (W - 1) if args.wide else meta["visarea"][0]
    prog["texram"].value = 0
    prog["texMask"].value = texsize - 1
    prog["uDbgQuadId"].value = 1 if os.environ.get("MIDV_DBG_QUADID") else 0
    prog["uClipW"].value = W
    prog["uBgMargin"].value = (margin if (args.marginfill and args.wide) else 0)
    tex2d.use(0)

    positions, joins = None, []
    if args.align_tjunctions:
        from tjunctions import align
        positions, joins = align(quads[nhist:])
        if nhist:
            previous, _ = align(quads[:nhist])
            positions = np.concatenate([previous, positions])
        print(f"T-junction experiment: {len(joins)} vertices aligned")
    fdata, udata = build_vertices(quads, margin, dilate2d=not exact, positions=positions)
    vbo_f = ctx.buffer(fdata.tobytes())
    vbo_u = ctx.buffer(udata.tobytes())
    vao = ctx.vertex_array(prog, [
        (vbo_f, "2f 2f 2f 2f 2f 4f 4f 4f",
         "in_corner", "in_v0", "in_v1", "in_v2", "in_v3",
         "in_uv01", "in_uv23", "in_uvBounds"),
        (vbo_u, "4u", "in_meta"),
    ])

    fw, fh = W * S, height * S
    idx_tex = ctx.texture((fw, fh), 1, dtype="u2")
    mask_tex = ctx.texture((fw, fh), 1, dtype="u1")
    fbo = ctx.framebuffer(color_attachments=[idx_tex, mask_tex])
    mask_fbo = ctx.framebuffer(color_attachments=[mask_tex])
    fbo.use()
    ctx.viewport = (0, 0, fw, fh)

    def draw():
        fbo.clear()
        if nhist and not exact:
            # stale-page history first, then reset the mask so it flags only
            # pixels the FINAL scene wrote - the crack fill keys off it.
            # Exact mode keeps the original single call, bit-for-bit.
            vao.render(moderngl.TRIANGLES, vertices=nhist * 6)
            mask_fbo.clear()
            fbo.use()
            vao.render(moderngl.TRIANGLES, first=nhist * 6,
                       vertices=(len(quads) - nhist) * 6)
        else:
            vao.render(moderngl.TRIANGLES)

    draw()
    ctx.finish()

    if args.bench:
        t0 = time.perf_counter()
        for _ in range(args.bench):
            draw()
        ctx.finish()
        dt = (time.perf_counter() - t0) / args.bench
        print(f"bench: {dt*1000:.3f} ms/scene at {fw}x{fh} "
              f"({1.0/dt:,.0f} fps equivalent)")

    if os.environ.get("MIDV_DBG_MASK") and not args.no_png:
        m = np.frombuffer(mask_tex.read(alignment=1), np.uint8)
        m = np.flipud(m.reshape(fh, fw)) * 255
        from PIL import Image as _I
        _I.fromarray(m).save(os.path.join(output_dir, "mask.png"))
        print("wrote mask.png")

    # ---- read back the index buffer ----
    data = np.frombuffer(fbo.read(components=1, dtype="u2"), dtype="<u2")
    gpu = np.flipud(data.reshape(fh, fw)).copy()
    if args.buffers:
        mask = np.flipud(np.frombuffer(mask_tex.read(alignment=1), np.uint8).reshape(fh, fw)).copy()
        prog["uDbgQuadId"].value = 1
        # A single draw gives IDs relative to the final scene. Sentinel 65535
        # is unambiguous; captured scenes must fit the 16-bit index target.
        current = len(quads) - nhist
        if current >= 65535:
            raise ValueError("too many quads for the ownership buffer")
        fbo.use()
        fbo.clear()
        vao.render(moderngl.TRIANGLES, first=nhist * 6, vertices=current * 6)
        owners = np.flipud(np.frombuffer(fbo.read(components=1, dtype="u2"), "<u2").reshape(fh, fw)).copy()
        owned = np.flipud(np.frombuffer(mask_tex.read(alignment=1), np.uint8).reshape(fh, fw)) != 0
        owners[~owned] = 65535
        np.savez_compressed(args.buffers, indices=gpu, coverage=mask,
                            owners=owners, quads=quads[nhist:], margin=margin, scale=S,
                            positions=positions[nhist:] if positions is not None else quads[nhist:, 2:10].copy().view(np.int16).reshape(-1,4,2))
        prog["uDbgQuadId"].value = 0
        draw()

    tag = (f"gpu-{'wide-' if args.wide else ''}{'crt-' if args.crt else ''}"
           f"{'fill-' if args.crackfill else ''}s{S}")
    report = {"schema": 1, "capture": os.path.abspath(cap), "scale": S,
              "renderer": ctx.info["GL_RENDERER"],
              "scope": "native-index-buffer" if exact else "quality-preview",
              "passed": None}
    if args.align_tjunctions:
        report["tjunction_experiment"] = joins
    if exact:
        ref_vram = np.fromfile(os.path.join(cap, "videoram.bin"), dtype="<u2")
        off = 0x40000 if pc & 4 else 0
        ref = ref_vram[off:off + 0x40000].reshape(512, 512)[:height]
        report["comparison"] = compare_arrays(gpu, ref)
        report["passed"] = report["comparison"]["passed"]
        match = report["comparison"]["exact_percent"]
        diff = report["comparison"]["differing_pixels"]
        print(f"GPU vs MAME videoram: {match:.4f}% bit-exact "
              f"({diff} differing pixels of {ref.size})")
    if args.report:
        write_json(args.report, report)
    exit_code = 1 if report["passed"] is False else 0
    if args.no_png:
        return exit_code

    # ---- palette pass -> PNG ----
    pprog = ctx.program(vertex_shader=PAL_VS, fragment_shader=PAL_FS)
    pprog["idxTex"].value = 1
    pprog["palTex"].value = 2
    pprog["uCrt"].value = 1 if args.crt else 0
    pprog["uSrcH"].value = float(height)
    pprog["maskTex"].value = 3
    pprog["uFillR"].value = (4 * S) if ((args.crackfill or args.marginfill) and not exact) else 0
    pprog["uMargin"].value = (margin * S) if (args.marginfill and not exact
                                              and args.wide) else 0
    idx_tex.use(1)
    paltex.use(2)
    mask_tex.use(3)
    rgb_tex = ctx.texture((fw, fh), 4)
    fbo2 = ctx.framebuffer(color_attachments=[rgb_tex])
    fbo2.use()
    ctx.viewport = (0, 0, fw, fh)
    pvao = ctx.vertex_array(pprog, [])
    pvao.vertices = 3
    pvao.render(moderngl.TRIANGLES)
    img = np.frombuffer(fbo2.read(components=4), dtype=np.uint8)
    img = np.flipud(img.reshape(fh, fw, 4)).copy()

    from PIL import Image
    out = os.path.join(output_dir, f"{tag}.png")
    Image.fromarray(img).save(out)
    # display-corrected copy (PAR 1.0417) for viewing
    disp = Image.fromarray(img).resize(
        (int(fw * 1.0417), fh), Image.LANCZOS if S > 1 else Image.NEAREST)
    disp.save(os.path.join(output_dir, f"{tag}-view.png"))
    print(f"wrote {out} (+ -view.png)")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
