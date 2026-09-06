"""Legacy out-of-process reference viewer (not a rendering equivalence oracle).

The product's MIDV_GL stream is private to its process. This viewer supports
MIDV_LIVE-only experiments and retains the earlier asynchronous resource and
underlay handling. Use replay.py + gl_frames.py for ordered product captures.

Live GPU renderer for midvunit - Phase 1 step 1 (out-of-process).

Attaches to the shared-memory ring that a MIDV_LIVE=1 vunit.exe publishes
("Local\\MIDV_LIVE") and renders the stream in its own window, in real time:

  QUAD     buffered per page_control run; a run boundary renders the whole
           scene into that page's index FBO in ONE draw call (the shipping
           renderer's unit of work, same shaders as gpu/renderer.py)
  VRAM     coalesced CPU writes (boot screens, test menus). Applied in
           stream order to a native-res underlay texture per page; a page
           whose latest content is CPU-written presents from the underlay,
           one whose latest content is a quad scene presents from the FBO.
  TEXTURE/ full snapshots, uploaded on arrival (sent by MAME only when
  PALETTE  dirty, so this is rare outside load screens)
  FLIP     display-page change -> present the newly visible page

Keys: F toggles 16:9 <-> 4:3 window crop, ESC quits.

Usage:  python gpu/live_viewer.py [--scale 3] [--stats]
        (start it before or after MAME - it resyncs on the next texture
        snapshot, which MAME re-sends whenever texture RAM changes)
"""
import argparse
import mmap
import os
import struct
import sys
import time

import glfw
import moderngl
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "harness"))
from renderer import VS, FS, PAL_VS, PAL_FS, build_vertices_fast  # noqa: E402

RING_TAG = "Local\\MIDV_LIVE"
HDR = 64
MARGIN = 86                      # 16:9 at the original pixel aspect
W_WIDE = 512 + 2 * MARGIN        # 684
HEIGHT = 400
PAR = 1.0417                     # 4:3 on a 512x400 raster


class Ring:
    """Reader side of the single-producer/single-consumer byte ring."""

    def __init__(self):
        self.mm = None
        self.size = 0

    def try_attach(self):
        try:
            mm = mmap.mmap(-1, HDR + (128 << 20), tagname=RING_TAG)
        except OSError:
            return False
        if mm[0:4] != b"MVL1":
            mm.close()
            return False
        self.mm = mm
        self.size = struct.unpack_from("<I", mm, 4)[0]
        return True

    @property
    def wpos(self):
        return struct.unpack_from("<Q", self.mm, 8)[0]

    def get_rpos(self):
        return struct.unpack_from("<Q", self.mm, 16)[0]

    def set_rpos(self, v):
        struct.pack_into("<Q", self.mm, 16, v)

    @property
    def dropped(self):
        return struct.unpack_from("<Q", self.mm, 24)[0]

    def read_at(self, pos, length):
        off = pos % self.size
        first = min(length, self.size - off)
        out = self.mm[HDR + off:HDR + off + first]
        if length > first:
            out += self.mm[HDR:HDR + (length - first)]
        return out

    def drain(self, budget_bytes=64 << 20):
        """Yield (type, payload) messages currently in the ring."""
        r, w = self.get_rpos(), self.wpos
        used = 0
        while r < w and used < budget_bytes:
            mtype, mlen = struct.unpack("<II", self.read_at(r, 8))
            payload = self.read_at(r + 8, mlen)
            step = (8 + mlen + 7) & ~7
            r += step
            used += step
            self.set_rpos(r)     # release space as we go
            yield mtype, payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--snap-dir", default=None,
                    help="save a backbuffer PNG every ~2s (for unattended tests)")
    ap.add_argument("--seconds", type=float, default=0,
                    help="exit after N seconds (0 = run until closed)")
    ap.add_argument("--fullscreen", action="store_true",
                    help="borderless fullscreen on the primary monitor, and "
                         "never steal focus - MAME keeps it for wheel/keys")
    args = ap.parse_args()
    S = args.scale

    fw, fh = W_WIDE * S, HEIGHT * S
    win_w, win_h = int(fw * PAR), fh

    if not glfw.init():
        sys.exit("glfw init failed")
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    if args.fullscreen:
        # Borderless on the primary monitor. FOCUSED/FOCUS_ON_SHOW off so the
        # MAME window keeps keyboard + DirectInput foreground acquisition -
        # the user looks at this window but plays "into" MAME's.
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        glfw.window_hint(glfw.FOCUSED, glfw.FALSE)
        glfw.window_hint(glfw.FOCUS_ON_SHOW, glfw.FALSE)
        glfw.window_hint(glfw.FLOATING, glfw.TRUE)
        mode = glfw.get_video_mode(glfw.get_primary_monitor())
        win_w, win_h = mode.size.width, mode.size.height
    win = glfw.create_window(win_w, win_h, "Cruis'n USA - live GPU renderer", None, None)
    if args.fullscreen:
        glfw.set_window_pos(win, 0, 0)
    glfw.make_context_current(win)
    glfw.swap_interval(1)        # vsync paces presentation
    ctx = moderngl.create_context()
    print(f"GL: {ctx.info['GL_RENDERER']}  window {win_w}x{win_h} "
          f"(scale {S}, 16:9 canvas {W_WIDE}x{HEIGHT})")

    # ---- pipeline objects (same shaders as the verified offline renderer) ----
    prog = ctx.program(vertex_shader=VS, fragment_shader=FS)
    prog["uCanvas"].value = (float(W_WIDE), float(HEIGHT))
    prog["uScale"].value = S
    prog["uClipRight"].value = W_WIDE - 1
    prog["texram"].value = 0
    tex2d = ctx.texture((4096, 2048), 1, dtype="u1", alignment=1)  # 8 MB texram
    prog["texMask"].value = (8 << 20) - 1
    paltex = ctx.texture((256, 128), 1, dtype="u4")

    pprog = ctx.program(vertex_shader=PAL_VS, fragment_shader=PAL_FS)
    pprog["idxTex"].value = 1
    pprog["palTex"].value = 2
    pvao = ctx.vertex_array(pprog, [])
    pvao.vertices = 3

    # per page: hi-res quad FBO + native CPU underlay + which is fresher
    pages = []
    for _ in range(2):
        idx = ctx.texture((fw, fh), 1, dtype="u2")
        fbo = ctx.framebuffer(color_attachments=[idx])
        fbo.clear()
        under = ctx.texture((512, HEIGHT), 1, dtype="u2")
        under.write(np.zeros(512 * HEIGHT, dtype="<u2").tobytes())
        # native-underlay presentation path: an FBO wrapping a scaled copy
        pages.append(dict(idx=idx, fbo=fbo, under=under, cpu_shadow=np.zeros(
            (HEIGHT, 512), dtype="<u2"), quad_fresh=False, quad_count=0))

    # underlay presenter: palette pass reads idxTex; for CPU pages we upload
    # the shadow into a native texture and let the palette FS sample it
    ring = Ring()
    print("waiting for MAME (MIDV_LIVE=1 vunit.exe) ...")
    while not ring.try_attach():
        time.sleep(0.25)
        glfw.poll_events()
        if glfw.window_should_close(win):
            return
    print("attached to ring")

    run_pc = None
    run_quads = []
    pending = [None, None]   # newest COMPLETED-but-unrendered run per page
    visible = 0
    frames = scenes = quads = vram_spans = skipped = 0
    t0 = time.time()
    last_stat = t0
    last_snap = t0
    snap_n = 0

    def page_of(pc):
        return 1 if (pc & 4) else 0

    def complete_run():
        """Move the accumulating run to its page's pending slot. If an older
        completed run is still waiting there, it is superseded - each scene
        fully repaints its page, so rendering only the newest is lossless
        under backlog."""
        nonlocal run_quads, skipped
        if not run_quads:
            return
        pg = page_of(run_pc)
        if pending[pg] is not None:
            skipped += 1
        pending[pg] = (run_pc, run_quads)
        run_quads = []

    def render_pending():
        nonlocal scenes
        for pg in (0, 1):
            if pending[pg] is None:
                continue
            pc, quad_list = pending[pg]
            pending[pg] = None
            p = pages[pg]
            fdata, udata = build_vertices_fast(
                np.array(quad_list, dtype="<u2"), MARGIN, dilate2d=True)
            vbo_f = ctx.buffer(fdata.tobytes())
            vbo_u = ctx.buffer(udata.tobytes())
            vao = ctx.vertex_array(prog, [
                (vbo_f, "2f 2f 2f 2f 2f 4f 4f 4f",
                 "in_corner", "in_v0", "in_v1", "in_v2", "in_v3",
                 "in_uv01", "in_uv23", "in_uvBounds"),
                (vbo_u, "4u", "in_meta")])
            p["fbo"].use()
            ctx.viewport = (0, 0, fw, fh)
            tex2d.use(0)
            vao.render(moderngl.TRIANGLES)
            vao.release()
            vbo_f.release()
            vbo_u.release()
            p["quad_fresh"] = True
            p["quad_count"] = len(quad_list)
            scenes += 1

    while not glfw.window_should_close(win):
        # ---- drain the ring in emulation order ----
        for mtype, payload in ring.drain():
            if mtype == 1:        # QUAD
                frame, pc = struct.unpack_from("<IH", payload)
                if run_pc is not None and pc != run_pc:
                    complete_run()
                run_pc = pc
                run_quads.append(np.frombuffer(payload[8:40], dtype="<u2"))
                quads += 1
            elif mtype == 2:      # FLIP
                frame, oldpc, newpc = struct.unpack("<IHH", payload)
                complete_run()
                visible = 1 if (newpc & 1) else 0
            elif mtype == 3:      # PALETTE
                paltex.write(payload[4:])
            elif mtype == 4:      # TEXTURE
                tex2d.write(payload[4:])
            elif mtype == 5:      # VRAM span
                frame, off, count = struct.unpack_from("<III", payload)
                span = np.frombuffer(payload[12:12 + count * 2], dtype="<u2")
                pg = 1 if (off & 0x40000) else 0
                rel = off & 0x3ffff
                p = pages[pg]
                flat = p["cpu_shadow"].reshape(-1)
                # page stride is 512; shadow row length 512 -> direct map
                y0, x0 = divmod(rel, 512)
                if y0 < HEIGHT:
                    end = min(rel + count, HEIGHT * 512)
                    flat[rel:end] = span[:end - rel]
                    p["quad_fresh"] = False
                vram_spans += 1

        render_pending()      # at most one scene per page per present

        # ---- present the visible page ----
        p = pages[visible]
        ctx.screen.use()
        ctx.viewport = (0, 0, win_w, win_h)   # moderngl clear() respects the
        ctx.screen.clear()                    # viewport - reset it first
        if p["quad_fresh"] and p["quad_count"] >= 300:
            # 3D scene: full 16:9 (real geometry fills the margins)
            pprog["uCrop"].value = 0
            ctx.viewport = (0, 0, win_w, win_h)
            p["idx"].use(1)
        elif p["quad_fresh"]:
            # 2D quad screen (menus, high scores, logos - low quad count):
            # the margins hold texture garbage the game never meant to show.
            # Crop to the original 4:3, letterboxed.
            pprog["uCrop"].value = MARGIN * S
            cw = int(512 * PAR * (win_h / HEIGHT))
            ctx.viewport = ((win_w - cw) // 2, 0, cw, win_h)
            p["idx"].use(1)
        else:
            # CPU-drawn page: native 4:3, letterboxed in the 16:9 window
            pprog["uCrop"].value = 0
            cw = int(512 * PAR * (win_h / HEIGHT))
            ctx.viewport = ((win_w - cw) // 2, 0, cw, win_h)
            p["under"].write(p["cpu_shadow"].tobytes())
            p["under"].use(1)
        paltex.use(2)
        pvao.render(moderngl.TRIANGLES)
        glfw.swap_buffers(win)
        glfw.poll_events()
        frames += 1

        now = time.time()
        if args.stats and now - last_stat > 2:
            print(f"  {frames/(now-t0):5.1f} fps | scenes {scenes} "
                  f"(skipped {skipped}) | quads {quads} "
                  f"| vram spans {vram_spans} | dropped {ring.dropped}")
            last_stat = now
        if args.snap_dir and now - last_snap > 2:
            data = ctx.screen.read(components=3)
            img = np.frombuffer(data, dtype=np.uint8).reshape(win_h, win_w, 3)
            from PIL import Image
            Image.fromarray(np.flipud(img)).save(
                os.path.join(args.snap_dir, f"live_{snap_n:03d}.png"))
            snap_n += 1
            last_snap = now
        if args.seconds and now - t0 > args.seconds:
            break

    dt = time.time() - t0
    print(f"exit: {frames} frames in {dt:.1f}s ({frames/dt:.1f} fps), "
          f"{scenes} scenes, {quads} quads, {vram_spans} vram spans, "
          f"{ring.dropped} dropped")
    glfw.terminate()


if __name__ == "__main__":
    main()
