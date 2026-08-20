"""V-Unit Cruis'n Collection - fullscreen game-select shell.

wanszai-style launcher over the POC's rig: a borderless-fullscreen menu with
clear-logo cards for Cruis'n USA / Cruis'n World / Off Road Challenge, built
on the same glfw + moderngl stack as the GPU renderer. Selecting a game hides
the shell and calls run_rig.launch_game() (blocking); when the game exits
(Esc) the shell returns. Settings persist in rig/collection.ini.

Keys: Left/Right (or A/D) select - Enter/Space launch - C toggles the CRT
pass for the next launch (F9 toggles live in-game) - Esc quits the shell.
A wheel/joystick can nav too: hat left/right or paddle buttons select, any
of the first face buttons launches.

Usage: python harness/collection.py [--shot out.png] [--windowed]
  --shot renders one frame of the menu offscreen to a PNG and exits
  (automation/preview; no window, no input).
"""
import argparse
import configparser
import ctypes
import math
import os
import sys
import threading
import time

import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_rig  # noqa: E402  (importable launcher; also win32 focus helpers)

POC = run_rig.POC
ART = r"E:\Source\launchbox\Launchbox-Racing\Images\Arcade"
CFG = os.path.join(POC, "rig", "collection.ini")

GAMES = [
    ("crusnusa", "CRUIS'N USA",
     os.path.join(ART, "Clear Logo", "Cruis_n USA-01.png"),
     os.path.join(ART, "Screenshot - Game Title", "Cruis_n USA-01.jpg")),
    ("crusnwld", "CRUIS'N WORLD",
     os.path.join(ART, "Clear Logo", "Cruis_n World-01.png"),
     os.path.join(ART, "Screenshot - Game Title", "Cruis_n World-01.png")),
    ("offroadc", "OFF ROAD CHALLENGE",
     os.path.join(ART, "Clear Logo", "Off Road Challenge-01.png"),
     os.path.join(ART, "Screenshot - Game Title", "Off Road Challenge-01.png")),
]

GOLD = (1.0, 0.78, 0.22, 1.0)

VS = """
#version 430
uniform vec4 uRect;      // x, y, w, h in pixels, y-down from top-left
uniform vec2 uScreen;
in vec2 in_pos;          // unit quad
out vec2 t;
void main() {
    t = in_pos;
    vec2 p = uRect.xy + in_pos * uRect.zw;
    gl_Position = vec4(p.x / uScreen.x * 2.0 - 1.0,
                       1.0 - p.y / uScreen.y * 2.0, 0.0, 1.0);
}
"""

FS = """
#version 430
uniform sampler2D tex;
uniform vec4 uTint;
in vec2 t;
out vec4 color;
void main() { color = texture(tex, t) * uTint; }
"""


def load_font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", n), size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_image(text, size, names=("bahnschrift.ttf", "arialbd.ttf"),
               fill=(255, 255, 255, 255), glow=None):
    font = load_font(names, size)
    pad = size // 2
    box = font.getbbox(text)
    w, h = box[2] - box[0] + 2 * pad, box[3] - box[1] + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if glow:
        d.text((pad - box[0], pad - box[1]), text, font=font, fill=glow)
        img = img.filter(ImageFilter.GaussianBlur(size / 10))
        d = ImageDraw.Draw(img)
    d.text((pad - box[0], pad - box[1]), text, font=font, fill=fill)
    return img


def background_image(w, h):
    """Static backdrop: deep asphalt gradient + horizon glow + vignette."""
    y = np.linspace(0.0, 1.0, h)[:, None]
    x = np.linspace(-1.0, 1.0, w)[None, :]
    top = np.array([8, 10, 24], float)
    bot = np.array([30, 14, 40], float)
    img = np.zeros((h, w, 3)) \
        + top[None, None, :] * (1 - y[..., None]) + bot[None, None, :] * y[..., None]
    glow = np.exp(-((y - 0.62) ** 2) / 0.012) * np.exp(-(x ** 2) / 0.9)
    img += glow[..., None] * np.array([70, 28, 60], float)[None, None, :]
    vig = 1.0 - 0.35 * (x ** 2 + (2 * y - 1) ** 2)[..., None] * 0.5
    img *= np.clip(vig, 0.0, 1.0)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


class Shell:
    def __init__(self, ctx, w, h):
        self.ctx = ctx
        self.w, self.h = w, h
        self.prog = ctx.program(vertex_shader=VS, fragment_shader=FS)
        self.prog["uScreen"].value = (float(w), float(h))
        quad = np.array([0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1], dtype="f4")
        self.vao = ctx.vertex_array(
            self.prog, [(ctx.buffer(quad.tobytes()), "2f", "in_pos")])
        self.white = self.tex(Image.new("RGBA", (2, 2), (255, 255, 255, 255)))
        self.bg = self.tex(background_image(w, h))
        self.title = self.tex(text_image(
            "V-UNIT  CRUIS'N  COLLECTION", h // 14,
            fill=(255, 224, 160, 255), glow=(255, 96, 32, 200)))
        self.cards = []
        for rom, name, logo, shot in GAMES:
            simg = Image.open(shot).convert("RGBA")
            limg = Image.open(logo).convert("RGBA")
            self.cards.append((self.tex(simg), simg.size,
                               self.tex(limg), limg.size, name))
        self.foot_cache = {}
        self.text_cache = {}

    def text_tex(self, s, px):
        key = (s, px)
        if key not in self.text_cache:
            self.text_cache[key] = self.tex(text_image(s, px))
        return self.text_cache[key]

    def center_text(self, s, px, y, tint=(1, 1, 1, 1)):
        tx = self.text_tex(s, px)
        th = px * 1.9
        tw = tx.width * th / tx.height
        self.rect(tx, (self.w - tw) / 2, y, tw, th, tint)

    def draw_wizard(self, prompt, done, total, last):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("WHEEL SETUP", self.h // 20, self.h * 0.28,
                         (1.0, 0.85, 0.4, 1.0))
        self.center_text(f"PRESS A WHEEL BUTTON FOR:", self.h // 34, self.h * 0.42)
        self.center_text(prompt, self.h // 12, self.h * 0.50,
                         (0.5, 1.0, 0.6, 1.0))
        if last:
            self.center_text(last, self.h // 40, self.h * 0.66,
                             (0.7, 0.7, 0.8, 1.0))
        self.center_text(f"{done} / {total}    ESC SKIP    BACKSPACE CANCEL",
                         self.h // 40, self.h * 0.90, (0.8, 0.8, 0.85, 1.0))

    def tex(self, img):
        t = self.ctx.texture(img.size, 4, img.tobytes())
        t.build_mipmaps()
        t.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        return t

    def footer_tex(self, crt):
        if crt not in self.foot_cache:
            msg = ("<  >  SELECT      ENTER / START  LAUNCH      "
                   f"C  CRT: {'ON' if crt else 'OFF'}      "
                   "S  WHEEL SETUP      ESC  QUIT")
            self.foot_cache[crt] = self.tex(text_image(
                msg, self.h // 36, fill=(210, 210, 220, 255)))
        return self.foot_cache[crt]

    def rect(self, tex, x, y, w, h, tint=(1, 1, 1, 1)):
        tex.use(0)
        self.prog["uRect"].value = (float(x), float(y), float(w), float(h))
        self.prog["uTint"].value = tuple(map(float, tint))
        self.vao.render(moderngl.TRIANGLES)

    def draw(self, sel, crt, t):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14) / self.title.height * 1.0
        th = self.h / 14 * 1.9
        tw = self.title.width * th / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05, tw, th)

        cw = self.w * 0.24
        ch = cw * 0.75
        gap = self.w * 0.045
        total = 3 * cw + 2 * gap
        y0 = self.h * 0.28
        for i, (stex, ssz, ltex, lsz, name) in enumerate(self.cards):
            x = (self.w - total) / 2 + i * (cw + gap)
            s = 1.0 if i == sel else 0.88
            dim = 1.0 if i == sel else 0.45
            ew, eh = cw * s, ch * s
            ex, ey = x + (cw - ew) / 2, y0 + (ch - eh) / 2
            if i == sel:
                pulse = 0.75 + 0.25 * math.sin(t * 4.0)
                b = self.h * 0.008
                self.rect(self.white, ex - b, ey - b, ew + 2 * b, eh + 2 * b,
                          (GOLD[0], GOLD[1], GOLD[2], pulse))
            self.rect(self.white, ex, ey, ew, eh, (0, 0, 0, 1))
            self.rect(stex, ex, ey, ew, eh, (dim, dim, dim, 1))
            # clear logo on its own line below the card
            lw = ew * 0.85
            lh = lsz[1] * lw / lsz[0]
            maxlh = self.h * 0.13 * s
            if lh > maxlh:
                lh, lw = maxlh, lsz[0] * maxlh / lsz[1]
            self.rect(ltex, ex + (ew - lw) / 2, y0 + ch + self.h * 0.035,
                      lw, lh, (dim, dim, dim, 1))
        foot = self.footer_tex(crt)
        fh = self.h / 36 * 1.9
        fw = foot.width * fh / foot.height
        self.rect(foot, (self.w - fw) / 2, self.h * 0.90, fw, fh)


class Audio:
    """Menu music (mci, loops an extracted video-snap track) + synth blips
    (winsound, plays alongside mci). All best-effort: missing files or a
    missing audio device silently disable sound."""

    def __init__(self):
        self.assets = os.path.join(POC, "rig", "assets")
        self.music = False
        try:
            self._mci = ctypes.windll.winmm.mciSendStringW
        except Exception:
            self._mci = None

    def mci(self, cmd):
        if self._mci:
            try:
                self._mci(cmd, None, 0, None)
            except Exception:
                pass

    def start_music(self):
        m = os.path.join(self.assets, "menumusic.wav")
        if os.path.isfile(m) and not self.music:
            self.mci(f'open "{m}" type mpegvideo alias menumusic')
            self.mci("play menumusic repeat")
            self.music = True

    def stop_music(self):
        if self.music:
            self.mci("stop menumusic")
            self.mci("close menumusic")
            self.music = False

    def blip(self, name):
        try:
            import winsound
            f = os.path.join(self.assets, f"{name}.wav")
            if os.path.isfile(f):
                winsound.PlaySound(f, winsound.SND_FILENAME | winsound.SND_ASYNC
                                   | winsound.SND_NODEFAULT)
        except Exception:
            pass


# wheel-setup wizard: (prompt label, collection.ini key, MAME port type)
WIZARD_STEPS = [
    ("COIN",      "coin",   "COIN1"),
    ("START",     "start",  "START1"),
    ("VIEW 1",    "view1",  "P1_BUTTON1"),
    ("VIEW 2",    "view2",  "P1_BUTTON2"),
    ("VIEW 3",    "view3",  "P1_BUTTON3"),
    ("RADIO",     "radio",  "P1_BUTTON4"),
    ("GEAR 1",    "gear1",  "P1_BUTTON5"),
    ("GEAR 2",    "gear2",  "P1_BUTTON6"),
    ("GEAR 3",    "gear3",  "P1_BUTTON7"),
    ("GEAR 4",    "gear4",  "P1_BUTTON8"),
]


def load_config():
    cp = configparser.ConfigParser()
    cp.read(CFG)
    sec = cp["collection"] if "collection" in cp else {}
    return {"crt": str(sec.get("crt", "1")) == "1",
            "scale": int(sec.get("scale", 4)),
            "rom": sec.get("rom", "crusnusa")}


def save_config(state):
    cp = configparser.ConfigParser()
    cp.read(CFG)   # preserve other sections (wheelmap)
    cp["collection"] = {"crt": "1" if state["crt"] else "0",
                        "scale": str(state["scale"]), "rom": state["rom"]}
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    with open(CFG, "w") as f:
        cp.write(f)


def save_wheelmap(bindings):
    """bindings: {ini_key: (device_name, button_index)} from the wizard."""
    cp = configparser.ConfigParser()
    cp.read(CFG)
    cp["wheelmap"] = {k: f"{dev}|{btn}" for k, (dev, btn) in bindings.items()}
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    with open(CFG, "w") as f:
        cp.write(f)


def render_shot(path):
    state = load_config()
    sel = next((i for i, g in enumerate(GAMES) if g[0] == state["rom"]), 0)
    w, h = 1920, 1080
    ctx = moderngl.create_context(standalone=True, require=430)
    fbo = ctx.framebuffer(color_attachments=[ctx.texture((w, h), 4)])
    fbo.use()
    ctx.viewport = (0, 0, w, h)
    shell = Shell(ctx, w, h)
    fbo.clear()
    shell.draw(sel, state["crt"], 0.4)
    img = np.frombuffer(fbo.read(components=4), dtype=np.uint8)
    Image.fromarray(np.flipud(img.reshape(h, w, 4))[:, :, :3].copy()).save(path)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", metavar="PNG",
                    help="render one offscreen frame and exit")
    ap.add_argument("--windowed", action="store_true",
                    help="pass through to the game launch")
    args = ap.parse_args()
    if args.shot:
        render_shot(args.shot)
        return 0

    import glfw
    if not glfw.init():
        sys.exit("glfw init failed")
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.DECORATED, glfw.FALSE)
    glfw.window_hint(glfw.AUTO_ICONIFY, glfw.FALSE)
    mon = glfw.get_primary_monitor()
    mode = glfw.get_video_mode(mon)
    w, h = mode.size.width, mode.size.height
    mx, my = glfw.get_monitor_pos(mon)
    win = glfw.create_window(w, h, "V-Unit Cruis'n Collection", None, None)
    glfw.set_window_pos(win, mx, my)
    glfw.make_context_current(win)
    glfw.swap_interval(1)
    ctx = moderngl.create_context()
    ctx.viewport = (0, 0, w, h)
    shell = Shell(ctx, w, h)

    state = load_config()
    sel = next((i for i, g in enumerate(GAMES) if g[0] == state["rom"]), 0)
    actions = []
    audio = Audio()
    audio.start_music()

    # a Stream Deck launch has no foreground rights; claim them for the shell
    shell_hwnd = int(glfw.get_win32_window(win))
    threading.Thread(target=run_rig.enforce_foreground,
                     args=(shell_hwnd, 10), daemon=True).start()

    def on_key(_, key, sc, action, mods):
        if action == glfw.PRESS:
            actions.append(key)

    glfw.set_key_callback(win, on_key)
    hat_prev = 0
    joy_prev = {}

    def joy_presses():
        """New button presses this frame across all joysticks:
        [(jid, name, button_index), ...]"""
        out = []
        try:
            for jid in range(4):
                if not glfw.joystick_present(jid):
                    joy_prev.pop(jid, None)
                    continue
                b = glfw.get_joystick_buttons(jid)
                cur = tuple(b) if b is not None else ()
                prev = joy_prev.get(jid, cur)
                for i in range(min(len(cur), len(prev))):
                    if cur[i] and not prev[i]:
                        name = glfw.get_joystick_name(jid)
                        if isinstance(name, bytes):
                            name = name.decode(errors="replace")
                        out.append((jid, name, i))
                joy_prev[jid] = cur
        except Exception:
            pass
        return out

    launch = None
    mode = "menu"
    wiz_idx = 0
    wiz_bind = {}
    wiz_last = ""
    while not glfw.window_should_close(win):
        glfw.poll_events()
        presses = joy_presses()
        # hat nav (menu only)
        if mode == "menu":
            try:
                for jid in range(4):
                    if not glfw.joystick_present(jid):
                        continue
                    hats = glfw.get_joystick_hats(jid)
                    hat = hats[0] if hats is not None and len(hats) else 0
                    if hat & glfw.HAT_LEFT and not (hat_prev & glfw.HAT_LEFT):
                        actions.append(glfw.KEY_LEFT)
                    if hat & glfw.HAT_RIGHT and not (hat_prev & glfw.HAT_RIGHT):
                        actions.append(glfw.KEY_RIGHT)
                    hat_prev = hat
                    break
            except Exception:
                pass
            if presses:
                actions.append(glfw.KEY_ENTER)

        if mode == "wizard":
            for key in actions:
                if key == glfw.KEY_ESCAPE:          # skip this binding
                    audio.blip("nav")
                    wiz_idx += 1
                elif key == glfw.KEY_BACKSPACE:     # abort wizard
                    audio.blip("select")
                    mode = "menu"
            actions.clear()
            if mode == "wizard" and presses:
                jid, name, btn = presses[0]
                wiz_bind[WIZARD_STEPS[wiz_idx][1]] = (name, btn)
                wiz_last = f"{WIZARD_STEPS[wiz_idx][0]}  =  {name}  BUTTON {btn + 1}"
                audio.blip("nav")
                wiz_idx += 1
            if mode == "wizard" and wiz_idx >= len(WIZARD_STEPS):
                save_wheelmap(wiz_bind)
                audio.blip("select")
                mode = "menu"
        else:
            for key in actions:
                if key in (glfw.KEY_LEFT, glfw.KEY_A):
                    sel = (sel - 1) % len(GAMES)
                    audio.blip("nav")
                elif key in (glfw.KEY_RIGHT, glfw.KEY_D):
                    sel = (sel + 1) % len(GAMES)
                    audio.blip("nav")
                elif key == glfw.KEY_C:
                    state["crt"] = not state["crt"]
                    save_config(state)
                    audio.blip("nav")
                elif key == glfw.KEY_S:
                    mode = "wizard"
                    wiz_idx = 0
                    wiz_bind = {}
                    wiz_last = ""
                    audio.blip("select")
                elif key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_SPACE):
                    launch = GAMES[sel][0]
                    audio.blip("select")
                elif key == glfw.KEY_ESCAPE:
                    glfw.set_window_should_close(win, True)
            actions.clear()

        ctx.clear(0, 0, 0, 1)
        if mode == "wizard" and wiz_idx < len(WIZARD_STEPS):
            shell.draw_wizard(WIZARD_STEPS[wiz_idx][0], wiz_idx,
                              len(WIZARD_STEPS), wiz_last)
        else:
            shell.draw(sel, state["crt"], time.time() % 3600)
        glfw.swap_buffers(win)

        if launch:
            state["rom"] = launch
            save_config(state)
            audio.stop_music()
            glfw.hide_window(win)
            try:
                proc, game_hwnd = run_rig.launch_game_async(
                    rom=launch, scale=state["scale"],
                    windowed=args.windowed, crt=state["crt"])
                # watch the WINDOW, not the process: teardown (FFB plugin
                # exit races, WER dumps) drags for seconds after the player
                # Esc-quits - reappear the instant the game window dies and
                # let the process finish dying in the background
                while run_rig.u32.IsWindow(game_hwnd) and proc.poll() is None:
                    time.sleep(0.25)
                threading.Thread(target=proc.wait, daemon=True).start()
            except SystemExit as e:
                print("launch failed:", e)
            launch = None
            glfw.show_window(win)
            glfw.focus_window(win)
            audio.start_music()
            threading.Thread(target=run_rig.enforce_foreground,
                             args=(shell_hwnd, 10), daemon=True).start()

    audio.stop_music()
    save_config(state)
    glfw.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
