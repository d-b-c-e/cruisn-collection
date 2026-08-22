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
ART = os.environ.get(
    "CRUISN_ART",
    os.path.join(POC, "art") if run_rig.FROZEN
    else r"E:\Source\launchbox\Launchbox-Racing\Images\Arcade")
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
    # Zeus2 hardware, not V-Unit: runs through MAME's own renderer (flagged
    # NOT_WORKING/IMPERFECT upstream but play-tested daily on this rig);
    # the GL overlay is inert for it, run_rig gives it video d3d
    ("crusnexo", "CRUIS'N EXOTICA",
     os.path.join(ART, "Clear Logo", "North America", "Cruis_n Exotica-01.png"),
     os.path.join(ART, "Screenshot - Game Title", "Cruis_n Exotica-02.png")),
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


def glow_image(size=384):
    """Soft radial gold glow drawn behind the focused logo - the logos
    float free on the backdrop (no card frame), so focus reads as light.
    Alpha reaches exactly zero at the inscribed circle: a gaussian left
    ~4% alpha at the texture edge, which showed as a faint rectangle."""
    y, x = np.mgrid[0:size, 0:size].astype(float)
    c = (size - 1) / 2.0
    r = np.sqrt((x - c) ** 2 + (y - c) ** 2) / c
    img = np.zeros((size, size, 4), np.uint8)
    img[..., 0] = 255
    img[..., 1] = 205
    img[..., 2] = 90
    img[..., 3] = (np.clip(1.0 - r, 0.0, 1.0) ** 2.2 * 235).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


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
            "CRUIS'N  COLLECTION", h // 14,
            fill=(255, 224, 160, 255), glow=(255, 96, 32, 200)))
        self.glow = self.tex(glow_image())
        self.cards = []
        for rom, name, logo, shot in GAMES:
            # art is optional (LaunchBox library on the dev box); fall back
            # to generated text so a fresh install still has a full menu
            try:
                limg = Image.open(logo).convert("RGBA")
            except Exception:
                limg = text_image(name, 72, fill=(255, 214, 130, 255),
                                  glow=(255, 96, 32, 200))
            self.cards.append((self.tex(limg), limg.size, name))
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

    def draw_loading(self, name, t):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("LAUNCHING", self.h // 24, self.h * 0.42,
                         (0.8, 0.8, 0.85, 1.0))
        pulse = 0.65 + 0.35 * math.sin(t * 3.0)
        self.center_text(name, self.h // 14, self.h * 0.50,
                         (GOLD[0], GOLD[1], GOLD[2], pulse))

    def draw_wizard_begin(self, t):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("WHEEL / CONTROLLER SETUP", self.h // 20,
                         self.h * 0.28, (1.0, 0.85, 0.4, 1.0))
        self.center_text("YOU WILL MOVE OR PRESS EACH CONTROL IN TURN",
                         self.h // 34, self.h * 0.44)
        self.center_text("RELEASE EVERYTHING, THEN", self.h // 34,
                         self.h * 0.50)
        pulse = 0.65 + 0.35 * math.sin(t * 4.0)
        self.center_text("PRESS ENTER TO BEGIN", self.h // 16, self.h * 0.57,
                         (GOLD[0], GOLD[1], GOLD[2], pulse))
        self.center_text("ESC / BACKSPACE  CANCEL", self.h // 40,
                         self.h * 0.90, (0.8, 0.8, 0.85, 1.0))

    def draw_wizard(self, prompt, done, total, last, kind="button", cool=0.0):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("WHEEL / CONTROLLER SETUP", self.h // 20,
                         self.h * 0.28, (1.0, 0.85, 0.4, 1.0))
        hint = ("MOVE THE CONTROL FOR:" if kind == "axis"
                else "PRESS A BUTTON (OR KEYBOARD KEY) FOR:")
        self.center_text(hint, self.h // 34, self.h * 0.42)
        self.center_text(prompt, self.h // 16, self.h * 0.50,
                         (0.5, 1.0, 0.6, 1.0))
        if last:
            self.center_text(last, self.h // 40, self.h * 0.66,
                             (0.7, 0.7, 0.8, 1.0))
        if cool > 0.0:
            # cooldown after each bind: shrinking bar + release prompt
            self.center_text("RELEASE ALL CONTROLS...", self.h // 40,
                             self.h * 0.72, (1.0, 0.75, 0.3, 0.9))
            bw = self.w * 0.26 * min(cool, 1.0)
            self.rect(self.white, (self.w - bw) / 2, self.h * 0.770,
                      bw, self.h * 0.010,
                      (GOLD[0], GOLD[1], GOLD[2], 0.9))
        if kind == "button":
            self.center_text("BUTTONS ABOVE 32 CAN'T BE CAPTURED HERE - "
                             "ESC SKIPS (THEY STILL WORK IN-GAME)",
                             self.h // 48, self.h * 0.83,
                             (0.55, 0.55, 0.62, 1.0))
        self.center_text(f"{done} / {total}    ESC SKIP    BACKSPACE CANCEL",
                         self.h // 40, self.h * 0.90, (0.8, 0.8, 0.85, 1.0))

    def tex(self, img):
        t = self.ctx.texture(img.size, 4, img.tobytes())
        t.build_mipmaps()
        t.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        return t

    def footer_tex(self, msg, div=36):
        key = (msg, div)
        if key not in self.foot_cache:
            self.foot_cache[key] = self.tex(text_image(
                msg, self.h // div, fill=(210, 210, 220, 255)))
        return self.foot_cache[key]

    def rect(self, tex, x, y, w, h, tint=(1, 1, 1, 1)):
        tex.use(0)
        self.prog["uRect"].value = (float(x), float(y), float(w), float(h))
        self.prog["uTint"].value = tuple(map(float, tint))
        self.vao.render(moderngl.TRIANGLES)

    def draw(self, sel, crt, t, row=0):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14) / self.title.height * 1.0
        th = self.h / 14 * 1.9
        tw = self.title.width * th / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05, tw, th)

        n = len(self.cards)
        cw = self.w * (0.24 if n <= 3 else 0.19)
        ch = cw * 0.75
        gap = self.w * (0.045 if n <= 3 else 0.03)
        total = n * cw + (n - 1) * gap
        y0 = self.h * 0.26
        for i, (ltex, lsz, name) in enumerate(self.cards):
            x = (self.w - total) / 2 + i * (cw + gap)
            focused = (row == 0 and i == sel)
            s = 1.0 if focused else 0.84
            dim = 1.0 if focused else (0.62 if i == sel else 0.45)
            # clear logo floats free in its slot - no card frame; focus is
            # a pulsing radial glow behind it plus a slight scale-up
            lw = cw * 0.94 * s
            lh = lsz[1] * lw / lsz[0]
            maxlh = ch * 0.92 * s
            if lh > maxlh:
                lh, lw = maxlh, lsz[0] * maxlh / lsz[1]
            if focused:
                pulse = 0.50 + 0.28 * math.sin(t * 4.0)
                gw, gh = cw * 1.5, ch * 1.45
                self.rect(self.glow, x + (cw - gw) / 2, y0 + (ch - gh) / 2,
                          gw, gh, (1.0, 1.0, 1.0, pulse))
            self.rect(ltex, x + (cw - lw) / 2, y0 + (ch - lh) / 2,
                      lw, lh, (dim, dim, dim, 1))
        # SETTINGS row under the cards
        if row == 1:
            pulse = 0.6 + 0.4 * math.sin(t * 4.0)
            self.center_text("SETTINGS", self.h // 24, self.h * 0.80,
                             (GOLD[0], GOLD[1], GOLD[2], pulse))
        else:
            self.center_text("SETTINGS", self.h // 24, self.h * 0.80,
                             (0.55, 0.55, 0.62, 1.0))
        foot = self.footer_tex(
            "<  >  ^  v  NAVIGATE      ENTER / START  OK      ESC  QUIT")
        fh = self.h / 36 * 1.9
        fw = foot.width * fh / foot.height
        self.rect(foot, (self.w - fw) / 2, self.h * 0.905, fw, fh)
        # in-game hotkey legend (keys that live outside the wheel bindings)
        leg = self.footer_tex(
            "IN-GAME:   5 COIN    1 START    ESC MENU / QUIT    F9 CRT    "
            "= / - VOLUME    F12 FORCE QUIT", div=46)
        lh = self.h / 46 * 1.9
        lw = leg.width * lh / leg.height
        self.rect(leg, (self.w - lw) / 2, self.h * 0.955, lw, lh,
                  (0.75, 0.75, 0.8, 1.0))

    def draw_settings(self, ssel, crt, fill, t):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("SETTINGS", self.h // 18, self.h * 0.26,
                         (1.0, 0.85, 0.4, 1.0))
        items = [f"CRT EFFECTS      {'ON' if crt else 'OFF'}",
                 f"CRACK FILL      {'ON' if fill else 'OFF'}",
                 "CONTROLS SETUP  (WHEEL / PAD / KEYBOARD)", "BACK"]
        for i, label in enumerate(items):
            if i == ssel:
                pulse = 0.65 + 0.35 * math.sin(t * 4.0)
                col = (GOLD[0], GOLD[1], GOLD[2], pulse)
            else:
                col = (0.75, 0.75, 0.8, 1.0)
            self.center_text(label, self.h // 26, self.h * (0.42 + 0.10 * i), col)
        foot = self.footer_tex("^  v  NAVIGATE      ENTER  OK      ESC  BACK")
        fh = self.h / 36 * 1.9
        fw = foot.width * fh / foot.height
        self.rect(foot, (self.w - fw) / 2, self.h * 0.92, fw, fh)


class Audio:
    """Menu music (mci loop; build/replace via harness/make_music.py) +
    synth blips (winsound, plays alongside mci). All best-effort: missing
    files or a missing audio device silently disable sound."""

    def __init__(self):
        self.assets = os.path.join(POC, "rig", "assets")
        self.music = False
        self.ensure_blips()
        try:
            self._mci = ctypes.windll.winmm.mciSendStringW
        except Exception:
            self._mci = None

    def ensure_blips(self):
        """Synthesize the UI blips on first run (they live in gitignored
        rig/assets, so a fresh install has none)."""
        try:
            import wave
            os.makedirs(self.assets, exist_ok=True)

            def synth(path, freqs, length, decay, vol):
                if os.path.isfile(path):
                    return
                sr = 44100
                t = np.arange(int(sr * length)) / sr
                sig = sum(np.sin(2 * np.pi * f * t) * a for f, a in freqs)
                sig = sig * np.exp(-t * decay) * vol
                with wave.open(path, "w") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(sr)
                    w.writeframes((np.clip(sig, -1, 1) * 32000)
                                  .astype("<i2").tobytes())

            synth(os.path.join(self.assets, "nav.wav"),
                  [(880, 1.0)], 0.07, 60, 0.6)
            synth(os.path.join(self.assets, "select.wav"),
                  [(220, 1.0), (440, 0.5)], 0.25, 14, 0.7)
        except Exception:
            pass

    def mci(self, cmd):
        if self._mci:
            try:
                self._mci(cmd, None, 0, None)
            except Exception:
                pass

    def start_music(self):
        if self.music:
            return
        for ext in ("mp3", "wav"):
            m = os.path.join(self.assets, f"menumusic.{ext}")
            if os.path.isfile(m):
                self.mci(f'open "{m}" type mpegvideo alias menumusic')
                self.mci("play menumusic repeat")
                self.music = True
                return

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


# wheel/controller-setup wizard: (prompt, ini key, kind)
# kind "button": press a joystick button OR a keyboard key
# kind "axis":   move an axis (turn wheel / press pedal / tilt stick)
WIZARD_STEPS = [
    ("STEERING  (turn the wheel / tilt the stick)", "steer", "axis"),
    ("GAS  (press the pedal / trigger)",            "gas",   "axis"),
    ("BRAKE  (press the pedal / trigger)",          "brake", "axis"),
    ("COIN",      "coin",   "button"),
    ("START",     "start",  "button"),
    ("VIEW 1",    "view1",  "button"),
    ("VIEW 2",    "view2",  "button"),
    ("VIEW 3",    "view3",  "button"),
    ("RADIO",     "radio",  "button"),
    ("GEAR 1",    "gear1",  "button"),
    ("GEAR 2",    "gear2",  "button"),
    ("GEAR 3",    "gear3",  "button"),
    ("GEAR 4",    "gear4",  "button"),
]

# glfw key -> MAME KEYCODE token (wizard keyboard capture). Esc/Backspace
# are wizard controls and deliberately absent.
def _keycode_table():
    import glfw
    t = {}
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        t[getattr(glfw, f"KEY_{ch}")] = f"KEYCODE_{ch}"
    for d in "0123456789":
        t[getattr(glfw, f"KEY_{d}")] = f"KEYCODE_{d}"
    for i in range(1, 13):
        t[getattr(glfw, f"KEY_F{i}")] = f"KEYCODE_F{i}"
    t.update({
        glfw.KEY_SPACE: "KEYCODE_SPACE", glfw.KEY_ENTER: "KEYCODE_ENTER",
        glfw.KEY_TAB: "KEYCODE_TAB",
        glfw.KEY_LEFT: "KEYCODE_LEFT", glfw.KEY_RIGHT: "KEYCODE_RIGHT",
        glfw.KEY_UP: "KEYCODE_UP", glfw.KEY_DOWN: "KEYCODE_DOWN",
        glfw.KEY_LEFT_SHIFT: "KEYCODE_LSHIFT",
        glfw.KEY_RIGHT_SHIFT: "KEYCODE_RSHIFT",
        glfw.KEY_LEFT_CONTROL: "KEYCODE_LCONTROL",
        glfw.KEY_RIGHT_CONTROL: "KEYCODE_RCONTROL",
        glfw.KEY_LEFT_ALT: "KEYCODE_LALT",
        glfw.KEY_RIGHT_ALT: "KEYCODE_RALT",
        glfw.KEY_COMMA: "KEYCODE_COMMA", glfw.KEY_PERIOD: "KEYCODE_STOP",
        glfw.KEY_SLASH: "KEYCODE_SLASH", glfw.KEY_SEMICOLON: "KEYCODE_COLON",
        glfw.KEY_MINUS: "KEYCODE_MINUS", glfw.KEY_EQUAL: "KEYCODE_EQUALS",
    })
    return t


def load_config():
    cp = configparser.ConfigParser()
    cp.read(CFG)
    sec = cp["collection"] if "collection" in cp else {}
    return {"crt": str(sec.get("crt", "1")) == "1",
            "crackfill": str(sec.get("crackfill", "1")) == "1",
            "scale": int(sec.get("scale", 4)),
            "rom": sec.get("rom", "crusnusa")}


def save_config(state):
    cp = configparser.ConfigParser()
    cp.read(CFG)   # preserve other sections (wheelmap)
    cp["collection"] = {"crt": "1" if state["crt"] else "0",
                        "crackfill": "1" if state["crackfill"] else "0",
                        "scale": str(state["scale"]), "rom": state["rom"]}
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    with open(CFG, "w") as f:
        cp.write(f)


def save_wheelmap(bindings):
    """bindings: {ini_key: value_string} from the wizard. Value formats:
    'Device Name|btn:N', 'Device Name|axis:N:G' (G=1 for XInput gamepads),
    'KEYBOARD|key:KEYCODE_X'."""
    cp = configparser.ConfigParser()
    cp.read(CFG)
    cp["wheelmap"] = dict(bindings)
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
    ap.add_argument("--joydump", action="store_true",
                    help="print connected joysticks as JSON and exit "
                         "(support-bundle diagnostics)")
    args = ap.parse_args()
    if args.shot:
        render_shot(args.shot)
        return 0
    if args.joydump:
        import glfw
        import json
        glfw.init()
        out = []
        for jid in range(16):
            if not glfw.joystick_present(jid):
                continue
            name = glfw.get_joystick_name(jid)
            if isinstance(name, bytes):
                name = name.decode(errors="replace")
            b = glfw.get_joystick_buttons(jid)
            h = glfw.get_joystick_hats(jid)
            a = glfw.get_joystick_axes(jid)
            count = lambda r: (r[1] if isinstance(r, tuple) and len(r) == 2
                               and not isinstance(r[0], int) else len(r or ()))
            out.append({"jid": jid, "name": name, "buttons": count(b),
                        "hats": count(h), "axes": count(a),
                        "gamepad": bool(glfw.joystick_is_gamepad(jid))})
        glfw.terminate()
        print(json.dumps(out, indent=1))
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
    glfw.set_input_mode(win, glfw.CURSOR, glfw.CURSOR_HIDDEN)
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
    fg_stop = threading.Event()
    threading.Thread(target=run_rig.enforce_foreground,
                     args=(shell_hwnd, 10), kwargs={"stop": fg_stop},
                     daemon=True).start()

    def on_key(_, key, sc, action, mods):
        if action == glfw.PRESS:
            actions.append(key)

    glfw.set_key_callback(win, on_key)
    hat_prev = 0
    joy_prev = {}
    joy_seen = {}
    joy_lastdown = {}
    # joystick input is ignored for a moment after boot and after a game
    # returns: device enumeration (and the Moza waking from idle-sleep) can
    # report zeros before real state arrives, and that settle read as a
    # phantom press - the "boots straight into the last game" bug
    armed_at = time.time() + 1.5

    def joy_buttons(jid):
        """pyGLFW returns (LP_c_ubyte, count) - unpack to a tuple of ints."""
        r = glfw.get_joystick_buttons(jid)
        if r is None:
            return ()
        if isinstance(r, tuple) and len(r) == 2 and not isinstance(r[0], int):
            ptr, n = r
            return tuple(ptr[i] for i in range(n))
        return tuple(r)

    def joy_hat(jid):
        r = glfw.get_joystick_hats(jid)
        if r is None:
            return 0
        if isinstance(r, tuple) and len(r) == 2 and not isinstance(r[0], int):
            ptr, n = r
            return ptr[0] if n else 0
        return r[0] if len(r) else 0

    def joy_presses():
        """Button edges this frame across all joysticks. Returns (downs,
        ups): downs = [(jid, name, button)], ups = [(jid, button)]. A
        device's first second after it appears is silent: its initial reads
        can be zeros with the true held/toggle state arriving a few polls
        later, and that 0->1 settle must not count as a press."""
        downs, ups = [], []
        now = time.time()
        try:
            for jid in range(16):
                if not glfw.joystick_present(jid):
                    joy_prev.pop(jid, None)
                    joy_seen.pop(jid, None)
                    continue
                cur = joy_buttons(jid)
                joy_seen.setdefault(jid, now)
                prev = joy_prev.get(jid, cur)
                if now - joy_seen[jid] >= 1.0:
                    for i in range(min(len(cur), len(prev))):
                        if cur[i] and not prev[i]:
                            # a button that was down <0.6 s ago is a
                            # re-enumeration/wake glitch (latched toggles
                            # read 1->0->1), not a human press
                            if now - joy_lastdown.get((jid, i), 0.0) < 0.6:
                                continue
                            name = glfw.get_joystick_name(jid)
                            if isinstance(name, bytes):
                                name = name.decode(errors="replace")
                            downs.append((jid, name, i))
                        elif prev[i] and not cur[i]:
                            ups.append((jid, i))
                for i, v in enumerate(cur):
                    if v:
                        joy_lastdown[(jid, i)] = now
                joy_prev[jid] = cur
        except Exception:
            pass
        return downs, ups

    def joy_axes(jid):
        r = glfw.get_joystick_axes(jid)
        if r is None:
            return ()
        if isinstance(r, tuple) and len(r) == 2 and not isinstance(r[0], (int, float)):
            ptr, n = r
            return tuple(ptr[i] for i in range(n))
        return tuple(r)

    KEYCODES = _keycode_table()
    launch = None
    launching = None     # in-flight launch box (background thread)
    game_proc = None     # last vunit process, until teardown completes
    mode = "menu"        # menu | settings | wizard
    row = 0              # menu: 0 = game cards, 1 = SETTINGS
    ssel = 0             # settings: item index
    wiz_idx = 0
    wiz_bind = {}
    wiz_last = ""
    wiz_base = None      # axis baselines {jid: axes tuple}
    wiz_ready = False    # gate screen: capture starts on Enter, not entry
    wiz_cool = 0.0       # ignore-everything deadline after each bind/skip
    wiz_settle = None    # last axis sample while waiting for rest
    wiz_settle_t = 0.0
    ok_pending = {}      # (jid, btn) -> hat_changes count at press
    hat_changes = 0
    while not glfw.window_should_close(win):
        glfw.poll_events()
        presses, releases = joy_presses()
        if launching is not None:
            # boot in progress: the shell just shows LAUNCHING and stays deaf
            presses, releases = [], []
            actions.clear()

        # wheel hat -> arrow keys (menu + settings)
        if mode in ("menu", "settings"):
            armed = time.time() >= armed_at
            if game_proc is not None:
                # the previous vunit is still tearing down in the background:
                # when the FFB plugin finally releases DirectInput the wheel
                # re-enumerates and can fire phantom presses SECONDS after
                # the shell is back - hold joystick input until the process
                # is well and truly gone, then arm 2 s later
                if game_proc.poll() is None:
                    armed = False
                else:
                    game_proc = None
                    armed_at = time.time() + 2.0
                    armed = False
            try:
                for jid in range(16):
                    if not glfw.joystick_present(jid):
                        continue
                    hat = joy_hat(jid)
                    if hat != hat_prev:
                        hat_changes += 1
                        if armed:
                            for h, key in ((glfw.HAT_LEFT, glfw.KEY_LEFT),
                                           (glfw.HAT_RIGHT, glfw.KEY_RIGHT),
                                           (glfw.HAT_UP, glfw.KEY_UP),
                                           (glfw.HAT_DOWN, glfw.KEY_DOWN)):
                                if hat & h and not (hat_prev & h):
                                    actions.append(key)
                        hat_prev = hat
                    break
            except Exception:
                pass
            # any wheel button = OK, fired on RELEASE with no hat movement
            # in between: a d-pad reports as hat AND buttons (press-based OK
            # made hat navigation launch the selected card), and a latched
            # phantom press (shifter gear reappearing after re-enumeration)
            # never releases, so it can never fire
            if armed:
                for jid, name, btn in presses:
                    ok_pending[(jid, btn)] = hat_changes
                for jid, btn in releases:
                    hc = ok_pending.pop((jid, btn), None)
                    if hc is not None and hc == hat_changes:
                        actions.append(glfw.KEY_ENTER)
                        break
            else:
                ok_pending.clear()

        if mode == "wizard":
            now = time.time()
            if not wiz_ready:
                # gate screen: nothing is read until the player says go
                for key in actions:
                    if key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER,
                               glfw.KEY_SPACE):
                        wiz_ready = True
                        wiz_cool = now + 0.8
                        audio.blip("select")
                    elif key in (glfw.KEY_ESCAPE, glfw.KEY_BACKSPACE):
                        mode = "settings"
                        audio.blip("nav")
                actions.clear()
            elif now < wiz_cool:
                # cooldown after every bind/skip: swallow all input while
                # the previous control is released (the wheel springing
                # back to center must not bind the next step)
                actions.clear()
            else:
                step = WIZARD_STEPS[wiz_idx] if wiz_idx < len(WIZARD_STEPS) else None
                for key in actions:
                    if key == glfw.KEY_ESCAPE:          # skip this binding
                        audio.blip("nav")
                        wiz_idx += 1
                        wiz_base = wiz_settle = None
                        wiz_cool = now + 0.8
                    elif key == glfw.KEY_BACKSPACE:     # abort wizard
                        audio.blip("select")
                        mode = "settings"
                    elif step and step[2] == "button" and key in KEYCODES:
                        # keyboard remap: any mappable key binds this action
                        wiz_bind[step[1]] = f"KEYBOARD|key:{KEYCODES[key]}"
                        wiz_last = (f"{step[0]}  =  KEYBOARD  "
                                    f"{KEYCODES[key].replace('KEYCODE_', '')}")
                        audio.blip("nav")
                        wiz_idx += 1
                        wiz_base = wiz_settle = None
                        wiz_cool = now + 1.0
                        break
                actions.clear()
                if (mode == "wizard" and now >= wiz_cool
                        and wiz_idx < len(WIZARD_STEPS)):
                    label, ikey, kind = WIZARD_STEPS[wiz_idx]
                    if kind == "button" and presses:
                        jid, name, btn = presses[0]
                        wiz_bind[ikey] = f"{name}|btn:{btn}"
                        wiz_last = f"{label}  =  {name}  BUTTON {btn + 1}"
                        audio.blip("nav")
                        wiz_idx += 1
                        wiz_base = wiz_settle = None
                        wiz_cool = now + 1.0
                    elif kind == "axis":
                        cur = {}
                        try:
                            for jid in range(16):
                                if glfw.joystick_present(jid):
                                    cur[jid] = joy_axes(jid)
                        except Exception:
                            pass
                        if wiz_base is None:
                            # arm only once every axis has sat still for a
                            # full sample interval - a control still moving
                            # (wheel returning, pedal easing up) must never
                            # become the reference it is measured against
                            if wiz_settle is None or now - wiz_settle_t >= 0.35:
                                if wiz_settle is not None and all(
                                        abs(a - b) < 0.06
                                        for j, axes in cur.items()
                                        for a, b in zip(axes,
                                                        wiz_settle.get(j, axes))):
                                    wiz_base = cur
                                wiz_settle, wiz_settle_t = cur, now
                        else:
                            hit = None
                            for jid, axes in cur.items():
                                base = wiz_base.get(jid, axes)
                                for i in range(min(len(axes), len(base))):
                                    if abs(axes[i] - base[i]) > 0.55:
                                        hit = (jid, i)
                                        break
                                if hit:
                                    break
                            if hit:
                                jid, i = hit
                                name = glfw.get_joystick_name(jid)
                                if isinstance(name, bytes):
                                    name = name.decode(errors="replace")
                                gp = 1 if glfw.joystick_is_gamepad(jid) else 0
                                wiz_bind[ikey] = f"{name}|axis:{i}:{gp}"
                                wiz_last = f"{label.split('(')[0].strip()}  =  {name}  AXIS {i}"
                                audio.blip("nav")
                                wiz_idx += 1
                                wiz_base = wiz_settle = None
                                wiz_cool = now + 1.0
            if mode == "wizard" and wiz_idx >= len(WIZARD_STEPS):
                save_wheelmap(wiz_bind)
                audio.blip("select")
                mode = "settings"

        elif mode == "settings":
            for key in actions:
                if key in (glfw.KEY_UP, glfw.KEY_W):
                    ssel = (ssel - 1) % 4
                    audio.blip("nav")
                elif key in (glfw.KEY_DOWN, glfw.KEY_S):
                    ssel = (ssel + 1) % 4
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel in (0, 1):
                    k = "crt" if ssel == 0 else "crackfill"
                    state[k] = not state[k]
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_SPACE):
                    if ssel in (0, 1):
                        k = "crt" if ssel == 0 else "crackfill"
                        state[k] = not state[k]
                        save_config(state)
                        audio.blip("nav")
                    elif ssel == 2:
                        mode = "wizard"
                        wiz_idx = 0
                        wiz_bind = {}
                        wiz_last = ""
                        wiz_ready = False
                        wiz_base = wiz_settle = None
                        wiz_cool = 0.0
                        audio.blip("select")
                    else:
                        mode = "menu"
                        audio.blip("select")
                elif key == glfw.KEY_ESCAPE:
                    mode = "menu"
                    audio.blip("nav")
            actions.clear()

        else:   # menu
            for key in actions:
                if key in (glfw.KEY_LEFT, glfw.KEY_A):
                    if row == 0:
                        sel = (sel - 1) % len(GAMES)
                        audio.blip("nav")
                elif key in (glfw.KEY_RIGHT, glfw.KEY_D):
                    if row == 0:
                        sel = (sel + 1) % len(GAMES)
                        audio.blip("nav")
                elif key in (glfw.KEY_DOWN, glfw.KEY_UP,
                             glfw.KEY_W, glfw.KEY_S):
                    row = 1 - row
                    audio.blip("nav")
                elif key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_SPACE):
                    if row == 0:
                        launch = GAMES[sel][0]
                    else:
                        mode = "settings"
                        ssel = 0
                    audio.blip("select")
                elif key == glfw.KEY_ESCAPE:
                    glfw.set_window_should_close(win, True)
            actions.clear()

        ctx.clear(0, 0, 0, 1)
        t = time.time() % 3600
        if launching is not None:
            shell.draw_loading(launching["name"], t)
        elif mode == "wizard" and not wiz_ready:
            shell.draw_wizard_begin(t)
        elif mode == "wizard" and wiz_idx < len(WIZARD_STEPS):
            shell.draw_wizard(WIZARD_STEPS[wiz_idx][0], wiz_idx,
                              len(WIZARD_STEPS), wiz_last,
                              WIZARD_STEPS[wiz_idx][2],
                              max(0.0, wiz_cool - time.time()))
        elif mode == "settings":
            shell.draw_settings(ssel, state["crt"], state["crackfill"], t)
        else:
            shell.draw(sel, state["crt"], t, row)
        glfw.swap_buffers(win)

        if launch and launching is None:
            state["rom"] = launch
            save_config(state)
            fg_stop.set()   # the game owns the foreground now, stop fighting
            launching = {"name": next(g[1] for g in GAMES if g[0] == launch),
                         "result": None, "err": None, "done": False}

            def _do_launch(box=launching, rom=launch):
                # background thread: the shell keeps rendering LAUNCHING
                # instead of vanishing to the desktop while MAME boots
                try:
                    box["result"] = run_rig.launch_game_async(
                        rom=rom, scale=state["scale"],
                        windowed=args.windowed, crt=state["crt"],
                        crackfill=state["crackfill"])
                except BaseException as e:
                    box["err"] = str(e) or repr(e)
                box["done"] = True

            threading.Thread(target=_do_launch, daemon=True).start()
            launch = None

        if launching is not None and launching["done"]:
            if launching["err"] is not None:
                print("launch failed:", launching["err"])
                armed_at = time.time() + 1.0
                audio.blip("nav")
            else:
                proc, game_hwnd = launching["result"]
                game_proc = proc
                audio.stop_music()
                # the shell window stays alive and fullscreen BEHIND the
                # game for the whole session - no desktop flash on launch
                # or return. Watch the WINDOW, not the process: teardown
                # (FFB plugin exit races, WER dumps) drags for seconds
                # after the player Esc-quits, and the window can outlive
                # its message pump through that drag, so two consecutive
                # WM_NULL timeouts also mean "exiting". Keep pumping our
                # own queue so Windows never ghosts the hidden shell.
                unresp = 0
                while run_rig.u32.IsWindow(game_hwnd) and proc.poll() is None:
                    glfw.poll_events()
                    if run_rig.window_responding(game_hwnd):
                        unresp = 0
                    else:
                        unresp += 1
                        if unresp >= 2:
                            break
                    time.sleep(0.25)
                threading.Thread(target=proc.wait, daemon=True).start()
                # joystick states changed while we were blocked (buttons
                # pressed in-game) - rebaseline or the first poll back
                # reads them as fresh presses and instantly relaunches
                joy_prev.clear()
                joy_seen.clear()
                ok_pending.clear()
                hat_prev = 0
                actions.clear()
                armed_at = time.time() + 1.0
                # in-game CRT toggles (F9 / Esc menu) persist back: the GL
                # overlay writes its final state at teardown - without this
                # the SETTINGS row and the next launch drift from reality
                try:
                    txt = open(os.path.join(POC, "rig", "gl_state.txt")).read()
                    if "crt=" in txt:
                        newcrt = txt.split("crt=")[1][:1] == "1"
                        if newcrt != state["crt"]:
                            state["crt"] = newcrt
                            save_config(state)
                except OSError:
                    pass
                glfw.focus_window(win)
                audio.start_music()
                fg_stop = threading.Event()
                threading.Thread(target=run_rig.enforce_foreground,
                                 args=(shell_hwnd, 10),
                                 kwargs={"stop": fg_stop},
                                 daemon=True).start()
            launching = None

    audio.stop_music()
    save_config(state)
    glfw.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
