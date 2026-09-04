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
try:
    import rawjoy  # noqa: E402  (Raw Input HID: >32-button wizard capture)
except Exception:
    rawjoy = None

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

# ASPECT / WIDESCREEN presets: clean named choices over the raw margin
# width (per side, 0..86). None = 16:9 FULL (the default). Applies to all
# games. Left/right cycles this list; an out-of-preset value (advanced env
# override) still shows its number.
ASPECT_PRESETS = [("4:3 CLASSIC", 0), ("16:9 TRIMMED", 48), ("16:9 FULL", None)]


def ASPECT_LABEL(margin):
    for label, val in ASPECT_PRESETS:
        if val == margin:
            return label
    return f"< {margin} >"


def aspect_cycle(margin, forward):
    vals = [v for _, v in ASPECT_PRESETS]
    idx = vals.index(margin) if margin in vals else len(vals) - 1
    return vals[(idx + (1 if forward else -1)) % len(vals)]

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


# Per-game CMOS settings bytes (see harness/nvram_tool.py for the full
# map and how each was pinned; NO game checksums its settings). VOLUME is
# (file, [addresses], max_value); crusnusa's master volume byte isn't
# pinned yet so its row defers to the in-game = / - keys. crusnwld24
# shares crusnwld's layout (verified 2026-08-29).
VOLUME_CMOS = {
    "crusnwld": ("nvram", [0x9C], 255),
    "offroadc": ("nvram", [0x2FC], 255),
    "crusnexo": ("m48t35", [0x27], 30),
}
FREEPLAY_CMOS = {
    "crusnusa": ("nvram", [0x190, 0x195, 0x19A, 0x19F]),
    "crusnwld": ("nvram", [0x1AC]),
    "offroadc": ("nvram", [0x1CC]),
    "crusnexo": ("m48t35", [0x73]),
}


def cmos_read(rom, fname, addr):
    """One byte from the rig NVRAM, or None before the game's first boot."""
    try:
        with open(os.path.join(POC, "rig", "nvram", rom, fname), "rb") as f:
            f.seek(addr)
            b = f.read(1)
        return b[0] if b else None
    except OSError:
        return None


def cmos_write(rom, fname, addrs, val):
    path = os.path.join(POC, "rig", "nvram", rom, fname)
    try:
        with open(path, "rb") as f:
            data = bytearray(f.read())
        for a in addrs:
            data[a] = val & 0xFF
        with open(path, "wb") as f:
            f.write(data)
        return True
    except OSError:
        return False


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

    def text_at(self, s, px, x, y, tint=(1, 1, 1, 1), align="l"):
        tx = self.text_tex(s, px)
        th = px * 1.9
        tw = tx.width * th / tx.height
        self.rect(tx, x - (tw if align == "r" else 0), y, tw, th, tint)

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
        if "WORLD" in name.upper():
            # first boot on new hardware: the game demands a one-time
            # wheel/pedal calibration (its CMOS stores the ADC ranges)
            self.center_text("IF THE GAME ASKS TO CALIBRATE CONTROLS:  "
                             "PRESS F2 AND FOLLOW THE PROMPTS  (ONE TIME)",
                             self.h // 40, self.h * 0.64,
                             (0.75, 0.75, 0.8, 1.0))

    def draw_wizard_begin(self, t):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("WHEEL / CONTROLLER SETUP", self.h // 24,
                         self.h * 0.28, (1.0, 0.85, 0.4, 1.0))
        self.center_text("YOU WILL MOVE OR PRESS EACH CONTROL IN TURN",
                         self.h // 38, self.h * 0.44)
        self.center_text("RELEASE EVERYTHING, THEN", self.h // 38,
                         self.h * 0.50)
        pulse = 0.65 + 0.35 * math.sin(t * 4.0)
        self.center_text("PRESS ENTER TO BEGIN", self.h // 20, self.h * 0.57,
                         (GOLD[0], GOLD[1], GOLD[2], pulse))
        self.center_text("ESC  CANCEL", self.h // 44,
                         self.h * 0.90, (0.8, 0.8, 0.85, 1.0))

    def draw_wizard(self, prompt, done, total, last, kind="button", cool=0.0):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("WHEEL / CONTROLLER SETUP", self.h // 24,
                         self.h * 0.28, (1.0, 0.85, 0.4, 1.0))
        hint = ("MOVE THE CONTROL FOR:" if kind == "axis"
                else "PRESS A BUTTON (OR KEYBOARD KEY) FOR:")
        self.center_text(hint, self.h // 38, self.h * 0.42)
        self.center_text(prompt, self.h // 20, self.h * 0.50,
                         (0.5, 1.0, 0.6, 1.0))
        if last:
            self.center_text(last, self.h // 44, self.h * 0.66,
                             (0.7, 0.7, 0.8, 1.0))
        if cool > 0.0:
            # cooldown after each bind: shrinking bar + release prompt
            self.center_text("RELEASE ALL CONTROLS...", self.h // 44,
                             self.h * 0.72, (1.0, 0.75, 0.3, 0.9))
            bw = self.w * 0.26 * min(cool / 2.0, 1.0)
            self.rect(self.white, (self.w - bw) / 2, self.h * 0.765,
                      bw, self.h * 0.010,
                      (GOLD[0], GOLD[1], GOLD[2], 0.9))
        self.center_text(f"{done} / {total}    BACKSPACE SKIP    ESC CANCEL",
                         self.h // 44, self.h * 0.90, (0.8, 0.8, 0.85, 1.0))

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

    def draw(self, sel, crt, t, row=0, notice=""):
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
            "<  >  ^  v  / STEER  NAVIGATE      ENTER / GAS  OK      ESC  QUIT")
        fh = self.h / 36 * 1.9
        fw = foot.width * fh / foot.height
        self.rect(foot, (self.w - fw) / 2, self.h * 0.905, fw, fh)
        if notice:
            # transient status line (a failed launch's reason, a ROM
            # fallback) - the console print alone left players guessing
            self.center_text(notice, self.h // 40, self.h * 0.865,
                             (1.0, 0.55, 0.45, 1.0))
        # in-game hotkey legend (keys that live outside the wheel bindings)
        leg = self.footer_tex(
            "IN-GAME:   5 COIN    1 START    ESC MENU / QUIT    F9 CRT    "
            "= / - VOLUME    F2 TEST    9 SERVICE    F12 QUIT GAME    "
            "SHIFT+F12 QUIT ALL", div=46)
        lh = self.h / 46 * 1.9
        lw = leg.width * lh / leg.height
        self.rect(leg, (self.w - lw) / 2, self.h * 0.955, lw, lh,
                  (0.75, 0.75, 0.8, 1.0))

    def draw_settings(self, ssel, crt, fill, margin, ffb, mfill, trans,
                      scale, t, version="", notice="", clamp=0, diag=False,
                      invert=False):
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text("SETTINGS", self.h // 20, self.h * 0.26,
                         (1.0, 0.85, 0.4, 1.0))
        # global items only - per-game tuning lives in each game's submenu
        rows = [("CRT EFFECTS", "ON" if crt else "OFF"),
                ("CRACK FILL", "ON" if fill else "OFF"),
                ("ASPECT / WIDESCREEN", ASPECT_LABEL(margin)),
                ("MARGIN FILL", "ON" if mfill else "OFF"),
                ("FFB STRENGTH", f"< {ffb}% >"),
                ("FFB PEAK LIMIT", "< OFF >" if not clamp else f"< {clamp} >"),
                ("FFB DIRECTION", "< INVERTED >" if invert else "< NORMAL >"),
                ("FFB DIAGNOSTICS", "ON" if diag else "OFF"),
                ("INTERNAL SCALE", f"< {scale}X >"),
                ("TRANSMISSION", "< H-PATTERN SHIFTER >" if trans == "hpattern"
                 else "< SEQUENTIAL >"),
                ("CONTROLS SETUP", "WHEEL / PAD / KEYBOARD"),
                ("SAVE SUPPORT BUNDLE", "FOR BUG REPORTS"),
                ("CHECK FOR UPDATES", version),
                ("BACK", "")]
        x0, x1 = self.w * 0.30, self.w * 0.70
        px = self.h // 33
        for i, (name, value) in enumerate(rows):
            y = self.h * (0.33 + 0.040 * i)
            if i == ssel:
                pulse = 0.65 + 0.35 * math.sin(t * 4.0)
                col = (GOLD[0], GOLD[1], GOLD[2], pulse)
                vcol = col
            else:
                col = (0.75, 0.75, 0.8, 1.0)
                vcol = (0.55, 0.55, 0.62, 1.0)
            self.text_at(name, px, x0, y, col)
            if value:
                self.text_at(value, px, x1, y, vcol, align="r")
        hints = {
            2: "4:3 = ORIGINAL ARCADE      16:9 = FILLS A WIDE SCREEN      "
               "TRIMMED = 16:9 WITH CLEANER EDGES",
            3: "ON = STRETCH EDGE PIXELS INTO THE 16:9 SIDES (CAN SMEAR)"
               "      OFF = CLEAN EDGES, BLACK WHERE THE GAME DRAWS NOTHING",
            4: "FORCE-FEEDBACK STRENGTH:   0% = FFB OFF (A/B TEST FOR "
               "SPEED)      LOWER IF THE WHEEL FEELS TOO HARSH",
            5: "CAPS THE GAMES' FORCE KICKS (OF 127)      STOPS A STRONG "
               "WHEEL SLAMMING LEFT-RIGHT BY ITSELF      TRY 40 ON A "
               "DIRECT-DRIVE BASE",
            6: "WHICH WAY THE WHEEL PUSHES - BASES DIFFER.  FLIP IT IF THE WHEEL "
               "RUNS AWAY FROM CENTRE IN EXOTICA OR SHAKES HARD IN USA",
            7: "ON = RECORDS THE FORCES AND WHEEL POSITION WHILE YOU DRIVE "
               "(FOR A BUG REPORT)      THEN SAVE SUPPORT BUNDLE",
            11: "WRITES ONE ZIP WITH LOGS, SETTINGS, CONTROLLER LAYOUT AND "
                "THE FORCE TRACE - NEVER YOUR ROMS      A GAME WINDOW "
                "APPEARS FOR ABOUT 10 S",
            8: "RENDER RESOLUTION: 4X = SHARPEST (2048 X 1600 INTERNAL)      "
               "LOWER IF A GAME STUTTERS ON YOUR GPU      TAKES EFFECT AT "
               "THE NEXT LAUNCH",
            9: "H-PATTERN = GEAR SHIFTER (GEARS 1-4)      SEQUENTIAL = "
               "SHIFT UP / DOWN PADDLES (EXOTICA: PADDLES DRIVE A VIRTUAL "
               "4-SPEED SHIFTER)",
            10: "BINDS THE CONTROLS FOR THE CURRENT TRANSMISSION MODE      "
               "SKIPPED STEPS KEEP THEIR SAVED BINDING",
            12: "LOOKS FOR A NEWER RELEASE ON GITHUB AND INSTALLS IT      "
               "YOUR ROMS, SETTINGS AND BINDINGS ARE KEPT",
        }
        if notice:
            self.center_text(notice, self.h // 40, self.h * 0.895,
                             (1.0, 0.85, 0.4, 1.0))
        elif ssel in hints:
            self.center_text(hints[ssel], self.h // 48, self.h * 0.895,
                             (0.65, 0.65, 0.72, 1.0))
        foot = self.footer_tex("^  v  NAVIGATE      ENTER  OK      ESC  BACK")
        fh = self.h / 36 * 1.9
        fw = foot.width * fh / foot.height
        self.rect(foot, (self.w - fw) / 2, self.h * 0.92, fw, fh)

    def draw_game_menu(self, gsel, title, rows, hint, t):
        """Per-game submenu: PLAY + the game's own tuning (the user's
        2026-08-29 design - selecting a card opens this instead of
        launching; ENTER-ENTER still fast-paths into the game)."""
        self.ctx.enable(moderngl.BLEND)
        self.rect(self.bg, 0, 0, self.w, self.h)
        tw = self.title.width * (self.h / 14 * 1.9) / self.title.height
        self.rect(self.title, (self.w - tw) / 2, self.h * 0.05,
                  tw, self.h / 14 * 1.9)
        self.center_text(title, self.h // 20, self.h * 0.24,
                         (1.0, 0.85, 0.4, 1.0))
        x0, x1 = self.w * 0.30, self.w * 0.70
        px = self.h // 33
        for i, (name, value) in enumerate(rows):
            y = self.h * (0.34 + 0.072 * i)
            if i == gsel:
                pulse = 0.65 + 0.35 * math.sin(t * 4.0)
                col = (GOLD[0], GOLD[1], GOLD[2], pulse)
                vcol = col
            else:
                col = (0.75, 0.75, 0.8, 1.0)
                vcol = (0.55, 0.55, 0.62, 1.0)
            self.text_at(name, px, x0, y, col)
            if value:
                self.text_at(value, px, x1, y, vcol, align="r")
        if hint:
            self.center_text(hint, self.h // 48, self.h * 0.86,
                             (0.65, 0.65, 0.72, 1.0))
        foot = self.footer_tex(
            "^  v  NAVIGATE      <  >  ADJUST      ENTER  OK      ESC  BACK")
        fh = self.h / 36 * 1.9
        fw = foot.width * fh / foot.height
        self.rect(foot, (self.w - fw) / 2, self.h * 0.92, fw, fh)


class ForzaKeeper:
    """Keeps the SimHub dash alive between games.

    SimHub freezes on the last received values when a telemetry stream
    stops (standard behavior) - so an exited game left the dash stuck on
    whatever was last sent. Whenever no game is running, this emits zeroed
    Forza packets (speed 0, rpm 0, gear 1) at 10 Hz to the same target the
    games use ([telemetry] forza in collection.ini), so gauges rest at zero
    in the launcher and snap back to zero the moment a game exits - crashes
    included. Inert when no forza target is configured."""

    def __init__(self):
        import socket
        import struct
        self.game_active = threading.Event()
        self.targets = []
        try:
            cp = configparser.ConfigParser()
            cp.read(CFG)
            v = cp.get("telemetry", "forza", fallback="").strip()
            if v.lower() in ("1", "on", "true", "yes"):
                v = "127.0.0.1:5300"
            for part in v.split(","):
                part = part.strip()
                if not part:
                    continue
                host, _, port = part.partition(":")
                self.targets.append((host or "127.0.0.1", int(port or "5300")))
        except Exception:
            self.targets = []
        if not self.targets:
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._struct = struct
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        ms = 0
        pkt = bytearray(324)
        self._struct.pack_into("<i", pkt, 0, 1)   # IsRaceOn: dash stays live
        # engine constants MUST match the game's packets - an "all zero"
        # packet (EngineMaxRpm=0) is degenerate and can wedge SimHub's
        # session/normalization state so it ignores the real stream after
        self._struct.pack_into("<f", pkt, 8, 7500.0)   # EngineMaxRpm
        self._struct.pack_into("<f", pkt, 12, 700.0)   # EngineIdleRpm
        pkt[319] = 1                              # gear 1 (0 shows reverse)
        pkt[323] = 0x4B                           # 'K' marker in the pad byte
                                                  # (diagnostics: forza_probe
                                                  # tags these rows "keeper")
        while True:
            if not self.game_active.is_set():
                ms = (ms + 100) & 0xFFFFFFFF
                self._struct.pack_into("<I", pkt, 4, ms)
                for tgt in self.targets:
                    try:
                        self._sock.sendto(bytes(pkt), tgt)
                    except OSError:
                        pass
            time.sleep(0.1)


class Audio:
    """Menu music (mci loop; build/replace via harness/make_music.py) +
    synth blips (winsound, plays alongside mci). All best-effort: missing
    files or a missing audio device silently disable sound."""

    def __init__(self):
        self.assets = os.path.join(POC, "rig", "assets")
        self.music = False
        self.cur_rom = None
        self.ensure_blips()
        try:
            self._mci = ctypes.windll.winmm.mciSendStringW
        except Exception:
            self._mci = None
        # music runs on one worker thread driven toward a target, so ramps
        # never block rendering and rapid card-nav coalesces to the latest
        self._target = ("stop", 0.0)     # ("play", rom) | ("stop", fade)
        self._target_seq = 0
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._music_loop, daemon=True)
        self._worker.start()

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

    def _track_for(self, rom):
        """Per-game menumusic-<rom>.* if present, else the generic
        menumusic.*; None if neither exists."""
        for stem in (f"menumusic-{rom}", "menumusic"):
            for ext in ("mp3", "wav"):
                m = os.path.join(self.assets, f"{stem}.{ext}")
                if os.path.isfile(m):
                    return m
        return None

    def start_music(self, rom=None):
        """Request the loop play `rom`'s track (or generic). Non-blocking;
        the worker cross-fades. Rapid calls coalesce to the last rom."""
        with self._lock:
            self._target = ("play", rom)
            self._target_seq += 1

    def stop_music(self, fade=0.0):
        """Request stop, optionally fading out first (launch transition)."""
        with self._lock:
            self._target = ("stop", fade)
            self._target_seq += 1

    def _ramp(self, lo, hi, seconds, seq):
        """Volume ramp lo->hi over `seconds`, aborting if superseded."""
        if not self._mci:
            return
        steps = max(1, int(seconds / 0.03))
        for i in range(1, steps + 1):
            if self._target_seq != seq:
                return   # a newer request arrived - drop this ramp
            v = int(lo + (hi - lo) * i / steps)
            self.mci(f"setaudio menumusic volume to {v}")
            time.sleep(seconds / steps)

    def _music_loop(self):
        """Drive the loop toward the latest requested target."""
        while True:
            with self._lock:
                kind, arg = self._target
                seq = self._target_seq
            if kind == "play":
                rom = arg
                if not self.music:
                    track = self._track_for(rom)
                    if track:
                        self.mci(f'open "{track}" type mpegvideo alias menumusic')
                        self.mci("setaudio menumusic volume to 0")
                        self.mci("play menumusic repeat")
                        self.music = True
                        self.cur_rom = rom
                        self._ramp(0, 1000, 0.4, seq)
                elif rom != self.cur_rom:
                    track = self._track_for(rom)
                    if track:
                        self._ramp(1000, 0, 0.22, seq)
                        if self._target_seq == seq:
                            self.mci("stop menumusic")
                            self.mci("close menumusic")
                            self.mci(f'open "{track}" type mpegvideo alias menumusic')
                            self.mci("setaudio menumusic volume to 0")
                            self.mci("play menumusic repeat")
                            self.cur_rom = rom
                            self._ramp(0, 1000, 0.28, seq)
            elif kind == "stop" and self.music:
                if arg > 0.0:
                    self._ramp(1000, 0, arg, seq)
                self.mci("stop menumusic")
                self.mci("close menumusic")
                self.music = False
                self.cur_rom = None
            time.sleep(0.03)

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
# The shift steps are mode-filtered at wizard entry: the TRANSMISSION
# setting decides whether gear1-4 (H-pattern) or shiftup/shiftdn
# (sequential paddles) are asked - the inactive mode's steps are hidden
# and its saved bindings kept (save_wheelmap merges).
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
    ("SHIFT UP  (paddle)",   "shiftup", "button"),
    ("SHIFT DOWN  (paddle)", "shiftdn", "button"),
    ("VOLUME UP",      "volup",   "button"),
    ("VOLUME DOWN",    "voldn",   "button"),
    ("TEST MENU  (operator settings)",    "test",    "button"),
    ("SERVICE CREDIT",                    "service", "button"),
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
    mg = str(sec.get("margin", "")).strip()

    # steering is PER-GAME (the games' native response shapes differ - the
    # V-Unit trio is lazy-centered, Exotica is not, so one global curve
    # cannot feel right everywhere). Keys: steersens_<rom>/steercurve_<rom>.
    # Legacy global steersens/steercurve migrate to the V-Unit games only
    # (the finding that motivated the split: curve 70 fixed V-Unit but made
    # Exotica twitchy - Exotica starts linear).
    def _num(key):
        v = str(sec.get(key, "")).strip()
        return int(v) if v.lstrip("-").isdigit() else None
    sens, curve = {}, {}
    for rom, _, _, _ in GAMES:
        sens[rom] = _num(f"steersens_{rom}")
        curve[rom] = _num(f"steercurve_{rom}")
    for rom in list(sens):
        # pre-v0.3.3 values were MAME "sensitivity" units (default 25)
        # and never affected a wheel; the key is a percent gain now
        if sens[rom] is not None and not 50 <= sens[rom] <= 300:
            sens[rom] = None
    legacy_s, legacy_c = _num("steersens"), _num("steercurve")
    for rom in ("crusnusa", "crusnwld", "offroadc"):
        if sens[rom] is None and legacy_s is not None:
            sens[rom] = legacy_s
        if curve[rom] is None and legacy_c is not None:
            curve[rom] = legacy_c

    # TRANSMISSION mode: which shifter style the games use and the wizard
    # binds. When the key is absent (configs from before the setting),
    # infer it the way the old apply_wheelmap arbitration did, so
    # paddle-only rigs stay sequential across the upgrade.
    tr = str(sec.get("transmission", "")).strip().lower()
    if tr not in ("hpattern", "sequential"):
        wm = cp["wheelmap"] if "wheelmap" in cp else {}
        hpat = all(g in wm for g in ("gear1", "gear2", "gear3", "gear4"))
        seq = "shiftup" in wm and "shiftdn" in wm
        tr = "sequential" if (seq and not hpat) else "hpattern"

    ffb = _num("ffb")
    return {"crt": str(sec.get("crt", "1")) == "1",
            "transmission": tr,
            "crackfill": str(sec.get("crackfill", "1")) == "1",
            "marginfill": str(sec.get("marginfill", "0")) == "1",
            "steersens": sens,
            "steercurve": curve,
            "margin": int(mg) if mg.isdigit() else None,
            "ffb": 50 if ffb is None else max(0, min(100, ffb)),   # 50: a direct-drive base at 100 fights itself
            "scale": int(sec.get("scale", 4)),
            # FFB PEAK LIMIT: 0 = off, else cap of the force kicks (of 127)
            "ffbclamp": int(sec.get("ffbclamp", 0) or 0),
            "ffbinvert": int(sec.get("ffb_invert", 0) or 0),
            # which World ROM set the CRUIS'N WORLD card boots. Default is
            # crusnwld24 (rev 2.4): the LAST revision with transmission
            # select - 2.5's factory ROMs are labeled "automatic" and
            # dropped the manual option entirely (why the shifter never
            # unlocked despite correct CONF/DIP config). Set world_rom =
            # crusnwld to go back to rev 2.5.
            "world_rom": (sec.get("world_rom") or "crusnwld24").strip(),
            "rom": sec.get("rom", "crusnusa")}


def save_config(state):
    cp = configparser.ConfigParser()
    cp.read(CFG)   # preserve other sections (wheelmap)
    sec = {"crt": "1" if state["crt"] else "0",
           "crackfill": "1" if state["crackfill"] else "0",
           "marginfill": "1" if state.get("marginfill", True) else "0",
           "margin": ("" if state["margin"] is None
                      else str(state["margin"])),
           "ffb": str(state.get("ffb", 100)),
           "transmission": state.get("transmission", "hpattern"),
           "scale": str(state["scale"]), "rom": state["rom"],
           "ffbclamp": str(state.get("ffbclamp", 0)),
           "ffb_invert": str(state.get("ffbinvert", 0)),
           "world_rom": state.get("world_rom", "crusnwld24")}
    for rom, _, _, _ in GAMES:
        sv = state["steersens"].get(rom)
        cv = state["steercurve"].get(rom)
        sec[f"steersens_{rom}"] = "" if sv is None else str(sv)
        sec[f"steercurve_{rom}"] = "" if cv is None else str(cv)
    # MERGE into the section: keys the shell does not own (ffb_diag,
    # exotica_gl, gamepatch_<rom>, anything a user or tool adds) must
    # survive a save - replacing the section wiped them at every launch
    if not cp.has_section("collection"):
        cp.add_section("collection")
    for k, v in sec.items():
        cp.set("collection", k, v)
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    with open(CFG, "w") as f:
        cp.write(f)


def save_wheelmap(bindings):
    """bindings: {ini_key: value_string} from the wizard. Value formats:
    'Device Name|btn:N', 'Device Name|axis:N:G' (G=1 for XInput gamepads),
    'KEYBOARD|key:KEYCODE_X'. MERGES into the existing [wheelmap]: steps
    the wizard didn't show (the inactive transmission mode's) and steps
    skipped with BACKSPACE keep their previous binding, so switching
    transmission modes never costs the other mode's binds."""
    cp = configparser.ConfigParser()
    cp.read(CFG)
    merged = dict(cp["wheelmap"]) if "wheelmap" in cp else {}
    merged.update(bindings)
    cp["wheelmap"] = merged
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


def update_step(upd):
    """SETTINGS -> CHECK FOR UPDATES, one Enter per stage: check -> (newer)
    download -> install. `upd` is shared with the main loop, which shows
    upd["msg"] and quits once upd["stage"] == "applied"."""
    import threading
    import updater

    def say(msg, secs=20):
        upd["msg"] = msg.upper()[:120]
        upd["until"] = time.time() + secs

    stage = upd.get("stage", "idle")
    if stage in ("checking", "downloading", "applied"):
        return
    if stage == "available":
        if not updater.frozen():
            say("running from source - update with git pull")
            return
        upd["stage"] = "downloading"

        def dl():
            try:
                info = upd["info"]
                last = [-1]

                def prog(done, total):
                    pct = int(done * 100 / total) if total else 0
                    if pct != last[0]:
                        last[0] = pct
                        say(f"downloading {info['tag']}... {pct}%", 60)
                z = updater.download(info, progress=prog)
                say("installing - the launcher will close and reopen", 60)
                updater.apply(z)
                upd["stage"] = "applied"
            except Exception as e:
                upd["stage"] = "idle"
                say(f"update failed: {e}", 30)
        threading.Thread(target=dl, daemon=True).start()
        return
    upd["stage"] = "checking"
    say("checking github...", 30)

    def chk():
        try:
            info = updater.check()
            upd["info"] = info
            if info["newer"]:
                upd["stage"] = "available"
                say(f"{info['tag']} available ({info['size'] / 1e6:.0f} MB)"
                    " - press enter again to download and install", 60)
            else:
                upd["stage"] = "idle"
                say(f"up to date ({updater.current_version()})")
        except Exception as e:
            upd["stage"] = "idle"
            say(str(e), 30)
    threading.Thread(target=chk, daemon=True).start()


def toggle_diag(upd):
    """SETTINGS -> FFB DIAGNOSTICS: flips the motor-write log + force trace flag
    (rig/collection.ini ffb_diag, applied at the next launch)."""
    on = not run_rig.ffb_diag_enabled()
    try:
        run_rig.set_ffb_diag(on)
        upd["msg"] = ("FFB DIAGNOSTICS ON - DRIVE A MINUTE, THEN SAVE SUPPORT BUNDLE"
                      if on else "FFB DIAGNOSTICS OFF")
    except Exception as e:
        upd["msg"] = f"COULD NOT SWITCH FFB DIAGNOSTICS: {e}".upper()[:120]
    upd["until"] = time.time() + 8


def bundle_step(upd):
    """SETTINGS -> SAVE SUPPORT BUNDLE: build the zip in the background
    (a game window appears for ~10 s for the emulator's input dump) and
    show where it landed."""
    import threading
    if upd.get("bundling"):
        return
    upd["bundling"] = True
    upd["msg"] = "BUILDING SUPPORT BUNDLE - A GAME WINDOW APPEARS FOR ABOUT 10 S..."
    upd["until"] = time.time() + 60

    def work():
        try:
            import support_bundle
            out = support_bundle.bundle(progress=lambda m: None)
            upd["msg"] = f"SUPPORT BUNDLE SAVED: {out}".upper()[:120]
            upd["until"] = time.time() + 30
            try:
                os.startfile(os.path.dirname(out))   # show the folder
            except Exception:
                pass
        except Exception as e:
            upd["msg"] = f"SUPPORT BUNDLE FAILED: {e}".upper()[:120]
            upd["until"] = time.time() + 20
        upd["bundling"] = False
    threading.Thread(target=work, daemon=True).start()


GAME_ALIASES = {
    "usa": "crusnusa", "crusnusa": "crusnusa",
    "world": "crusnwld", "crusnwld": "crusnwld", "crusnwld24": "crusnwld",
    "offroad": "offroadc", "offroadc": "offroadc", "orc": "offroadc",
    "exotica": "crusnexo", "crusnexo": "crusnexo",
}


def resolve_game_alias(name):
    """Card rom for a --game argument (usa/world/offroad/exotica or the
    MAME names); None when unknown."""
    return GAME_ALIASES.get((name or "").strip().lower())


def direct_launch(card, windowed=False):
    """--game: run one game with the launcher's saved settings and no shell
    window at all (frontends: LaunchBox, Stream Deck, shortcuts). Returns
    the process exit code; Esc-menu Exit / F12 end the game and this
    process alike."""
    state = load_config()
    real_rom = (state.get("world_rom", "crusnwld24")
                if card == "crusnwld" else card)
    if card == "crusnwld":
        real_rom, note = run_rig.resolve_world_rom(real_rom)
        if note:
            print(note, file=sys.stderr)
    boot_note = run_rig.boot_rom_note(real_rom)
    if boot_note:
        print(f"{card}: {boot_note}", file=sys.stderr)
        return 2
    proc, _hwnd = run_rig.launch_game_async(
        rom=real_rom, scale=int(state.get("scale", 4)), windowed=windowed,
        crt=state["crt"], crackfill=state["crackfill"],
        steersens=state["steersens"].get(card),
        steercurve=state["steercurve"].get(card),
        margin=state["margin"], ffb=state.get("ffb", 100),
        marginfill=state.get("marginfill", True),
        ffbclamp=state.get("ffbclamp", 0))
    gaks = ctypes.windll.user32.GetAsyncKeyState
    while proc.poll() is None and run_rig.u32.IsWindow(_hwnd):
        # Shift+F12 = quit (same key as in the launcher); WM_CLOSE is the
        # clean path (forces released, NVRAM written)
        if (gaks(0x7B) & 0x8000) and (gaks(0x10) & 0x8000):
            ctypes.windll.user32.PostMessageW(
                ctypes.c_void_p(_hwnd), 0x0010, 0, 0)
        time.sleep(0.25)
    rc = run_rig.wait_or_kill(proc)   # a hung teardown must not keep the wheel
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", metavar="NAME",
                    help="launch one game directly, no launcher screen: "
                         "usa, world, offroad, exotica (or MAME names)")
    ap.add_argument("--shot", metavar="PNG",
                    help="render one offscreen frame and exit")
    ap.add_argument("--windowed", action="store_true",
                    help="pass through to the game launch")
    ap.add_argument("--joydump", action="store_true",
                    help="print connected joysticks as JSON and exit "
                         "(support-bundle diagnostics)")
    args = ap.parse_args()
    if args.game:
        card = resolve_game_alias(args.game)
        if not card:
            sys.exit(f"unknown game {args.game!r} - use usa, world, "
                     f"offroad or exotica")
        return direct_launch(card, windowed=args.windowed)
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
    keeper = ForzaKeeper()   # zeroes the SimHub dash whenever no game runs
    audio.start_music(GAMES[sel][0])
    music_sel = sel   # track highlight changes to switch the per-game loop

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

    def cread(rom, fname, addr):
        key = (rom, fname, addr)
        if key not in cmos_cache:
            cmos_cache[key] = cmos_read(rom, fname, addr)
        return cmos_cache[key]

    def cwrite(rom, fname, addrs, val):
        if cmos_write(rom, fname, addrs, val):
            for a in addrs:
                cmos_cache[(rom, fname, a)] = val & 0xFF
            return True
        return False

    def cmos_rom(card):
        """The rom whose NVRAM the card's CMOS rows target (World follows
        the configured revision - 2.4 shares 2.5's byte layout)."""
        return (state.get("world_rom", "crusnwld24")
                if card == "crusnwld" else card)

    SENS_HINT = ("HOW FAR YOU TURN FOR FULL LOCK:   ABOVE 100% = FULL LOCK "
                 "WITH LESS TURNING      BELOW 100% = MORE TURNING NEEDED")
    CURVE_HINT = ("RESPONSE SHAPE:   BELOW 100 = MORE BITE NEAR CENTER "
                  "(FIXES LAZY-CENTER STEERING)      "
                  "ABOVE 100 = SOFTER CENTER")
    VOL_HINT = ("GAME MASTER VOLUME - SAVED INTO THE GAME'S OWN SETTINGS "
                "MEMORY, SAME AS THE OPERATOR MENU")
    FP_HINT = ("ON = NO COINS NEEDED      OFF = COIN PER CREDIT "
               "(KEY 5 / BOUND COIN BUTTON)")
    VER_HINT = ("2.4 = LAST REVISION WITH MANUAL TRANSMISSION      "
                "2.5 = FINAL REVISION, AUTOMATIC ONLY")

    def game_rows(card):
        """(id, label, value, hint) rows for the per-game submenu."""
        rows = [("play", "PLAY", "", "")]
        sv = state["steersens"].get(card)
        rows.append(("sens", "STEERING SENSITIVITY",
                     "GAME DEFAULT (100%)" if sv is None else f"< {sv}% >",
                     SENS_HINT))
        cv = state["steercurve"].get(card)
        rows.append(("curve", "STEERING CURVE",
                     "LINEAR (OFF)" if cv is None else f"< {cv} >",
                     CURVE_HINT))
        rom = cmos_rom(card)
        # no VOLUME row for games whose master byte isn't pinned (USA):
        # a row that can only point at the in-game = / - keys isn't a
        # setting. Pin the byte in VOLUME_CMOS and the row appears.
        if card in VOLUME_CMOS:
            fname, addrs, vmax = VOLUME_CMOS[card]
            v = cread(rom, fname, addrs[0])
            rows.append(("volume", "VOLUME",
                         "AFTER FIRST PLAY" if v is None
                         else f"< {round(v * 100 / vmax)}% >", VOL_HINT))
        fname, addrs = FREEPLAY_CMOS[card]
        v = cread(rom, fname, addrs[0])
        rows.append(("freeplay", "FREE PLAY",
                     "AFTER FIRST PLAY" if v is None
                     else f"< {'ON' if v else 'OFF'} >", FP_HINT))
        if card == "crusnwld":
            wr = state.get("world_rom", "crusnwld24")
            rows.append(("version", "GAME REVISION",
                         "< 2.4 (MANUAL+AUTO) >" if wr == "crusnwld24"
                         else "< 2.5 (AUTO ONLY) >", VER_HINT))
        rows.append(("back", "BACK", "", ""))
        return rows

    # -- steering-wheel / gas menu navigation (uses the wizard's axis
    # bindings from [wheelmap]; nothing here reads axes in wizard mode) --
    def parse_navspec():
        cp = configparser.ConfigParser()
        cp.read(CFG)
        out = {}
        if "wheelmap" in cp:
            for k in ("steer", "gas", "brake"):
                v = cp["wheelmap"].get(k, "")
                if "|" in v and "axis:" in v.split("|", 1)[1]:
                    dev, spec = v.split("|", 1)
                    parts = spec.split(":")
                    try:
                        out[k] = (dev, int(parts[1]),
                                  parts[3] if len(parts) > 3 else None)
                    except (ValueError, IndexError):
                        pass
        return out

    nav_spec = parse_navspec()
    nav_state = {"dir": 0, "next": 0.0, "gas": False}

    def nav_jid(dev):
        for jid in range(16):
            if glfw.joystick_present(jid):
                n = glfw.get_joystick_name(jid)
                if isinstance(n, bytes):
                    n = n.decode(errors="replace")
                if n == dev:
                    return jid
        return None

    def nav_axis(k):
        sp = nav_spec.get(k)
        if not sp:
            return None, None
        jid = nav_jid(sp[0])
        if jid is None:
            return None, None
        axes = joy_axes(jid)
        if sp[1] >= len(axes):
            return None, None
        return axes[sp[1]], sp[2]

    def nav_events(vertical):
        """Key events from steering (LEFT/RIGHT on the card row, UP/DOWN
        in vertical menus, with hysteresis + auto-repeat) and gas (OK on
        press edge; honors the wizard's recorded pedal direction so
        center-resting pedals don't read as held)."""
        evs = []
        now = time.time()
        try:
            v, _ = nav_axis("steer")
            if v is not None:
                d = nav_state["dir"]
                if d != 0 and v * d < 0.3:
                    d = 0
                fire = False
                if d == 0:
                    d = 1 if v > 0.5 else (-1 if v < -0.5 else 0)
                    if d != 0:
                        nav_state["next"] = now + 0.45
                        fire = True
                elif now >= nav_state["next"]:
                    nav_state["next"] = now + 0.28
                    fire = True
                if fire:
                    if vertical:
                        evs.append(glfw.KEY_DOWN if d > 0 else glfw.KEY_UP)
                    else:
                        evs.append(glfw.KEY_RIGHT if d > 0
                                   else glfw.KEY_LEFT)
                nav_state["dir"] = d
            v, sgn = nav_axis("gas")
            if v is not None:
                if sgn == "neg":
                    v = -v
                pressed = (v > 0.55 if sgn in ("pos", "neg")
                           else abs(v) > 0.6)
                if pressed and not nav_state["gas"]:
                    evs.append(glfw.KEY_ENTER)
                    nav_state["gas"] = True
                elif nav_state["gas"] and (
                        v < 0.3 if sgn in ("pos", "neg") else abs(v) < 0.3):
                    nav_state["gas"] = False
        except Exception:
            pass
        return evs

    KEYCODES = _keycode_table()
    launch = None
    launching = None     # in-flight launch box (background thread)
    notice = ""          # transient menu status line
    notice_until = 0.0
    upd = {"stage": "idle", "msg": "", "until": 0.0, "info": None}
    try:
        import updater
        upd_version = updater.current_version().upper()
    except Exception:
        upd_version = ""
    game_proc = None     # last vunit process, until teardown completes
    mode = "menu"        # menu | game | settings | wizard
    row = 0              # menu: 0 = game cards, 1 = SETTINGS
    ssel = 0             # settings: item index
    gsel = 0             # game submenu: item index
    cmos_cache = {}      # (rom, fname, addr) -> byte (invalidated on write)
    wiz_idx = 0
    wiz_bind = {}
    wiz_steps = WIZARD_STEPS   # mode-filtered at wizard entry
    wiz_last = ""
    wiz_base = None      # axis baselines {jid: axes tuple}
    wiz_ready = False    # gate screen: capture starts on Enter, not entry
    wiz_cool = 0.0       # ignore-everything deadline after each bind/skip
    wiz_settle = None    # last axis sample while waiting for rest
    wiz_settle_t = 0.0
    ok_pending = {}      # (jid, btn) -> hat_changes count at press
    hat_changes = 0
    rawlis = None        # Raw Input HID listener, wizard-scoped (>32 buttons)
    while not glfw.window_should_close(win):
        glfw.poll_events()
        presses, releases = joy_presses()
        if launching is not None:
            # boot in progress: the shell just shows LAUNCHING and stays deaf
            presses, releases = [], []
            actions.clear()

        # wheel hat -> arrow keys (menu + settings)
        if mode in ("menu", "settings", "game"):
            armed = time.time() >= armed_at
            if game_proc is not None:
                # the previous vunit is still tearing down in the background:
                # when the exiting emulator releases DirectInput the wheel
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
                nav_state["dir"] = 0
                nav_state["gas"] = True   # ignore a gas already held
            if armed:
                for ev in nav_events(not (mode == "menu" and row == 0)):
                    actions.append(ev)

        if mode == "wizard":
            now = time.time()
            # drain the raw HID queue every iteration; only the armed
            # button-step branch below consumes it, everything else
            # discards so stale presses can never fire later
            rawp = rawlis.get_presses() if rawlis is not None else []
            if not wiz_ready:
                # gate screen: nothing is read until the player says go
                for key in actions:
                    if key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER,
                               glfw.KEY_SPACE):
                        wiz_ready = True
                        wiz_cool = now + 1.8
                        audio.blip("select")
                    elif key == glfw.KEY_ESCAPE:
                        mode = "settings"
                        audio.blip("nav")
                actions.clear()
            elif now < wiz_cool:
                # cooldown after every bind/skip: swallow all input while
                # the previous control is released (the wheel springing
                # back to center must not bind the next step)
                actions.clear()
            else:
                step = wiz_steps[wiz_idx] if wiz_idx < len(wiz_steps) else None
                for key in actions:
                    if key == glfw.KEY_BACKSPACE:       # skip this binding
                        audio.blip("nav")
                        wiz_idx += 1
                        wiz_base = wiz_settle = None
                        wiz_cool = now + 1.8
                    elif key == glfw.KEY_ESCAPE:        # cancel wizard
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
                        wiz_cool = now + 2.0
                        break
                actions.clear()
                if (mode == "wizard" and now >= wiz_cool
                        and wiz_idx < len(wiz_steps)):
                    label, ikey, kind = wiz_steps[wiz_idx]
                    if kind == "button" and (presses or rawp):
                        # glfw first (its device names are proven against
                        # MAME's mapdevice); Raw Input HID covers buttons
                        # glfw misses (>32, split HID collections, ...)
                        if presses:
                            jid, name, btn = presses[0]
                        else:
                            name, btn = rawp[0]
                        wiz_bind[ikey] = f"{name}|btn:{btn}"
                        wiz_last = f"{label}  =  {name}  BUTTON {btn + 1}"
                        audio.blip("nav")
                        wiz_idx += 1
                        wiz_base = wiz_settle = None
                        wiz_cool = now + 2.0
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
                                # store the press DIRECTION too: pedals that
                                # rest at center (Moza) need a half-axis
                                # binding or MAME reads rest as 50% pressed
                                base = wiz_base.get(jid, cur[jid])
                                sgn = ("pos" if cur[jid][i] - base[i] > 0
                                       else "neg")
                                wiz_bind[ikey] = f"{name}|axis:{i}:{gp}:{sgn}"
                                wiz_last = f"{label.split('(')[0].strip()}  =  {name}  AXIS {i}"
                                audio.blip("nav")
                                wiz_idx += 1
                                wiz_base = wiz_settle = None
                                wiz_cool = now + 2.0
            if mode == "wizard" and wiz_idx >= len(wiz_steps):
                save_wheelmap(wiz_bind)
                nav_spec = parse_navspec()   # steering/gas nav follows
                audio.blip("select")
                mode = "settings"
        if rawlis is not None and mode != "wizard":
            rawlis.stop()
            rawlis = None

        elif mode == "settings":
            for key in actions:
                if key in (glfw.KEY_UP, glfw.KEY_W):
                    ssel = (ssel - 1) % 14
                    audio.blip("nav")
                elif key in (glfw.KEY_DOWN, glfw.KEY_S):
                    ssel = (ssel + 1) % 14
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel in (0, 1):
                    k = "crt" if ssel == 0 else "crackfill"
                    state[k] = not state[k]
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 2:
                    state["margin"] = aspect_cycle(
                        state["margin"], key == glfw.KEY_RIGHT)
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 3:
                    state["marginfill"] = not state.get("marginfill", True)
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 4:
                    # FFB overall strength, 0..100% in 10% steps
                    step = 10 if key == glfw.KEY_RIGHT else -10
                    state["ffb"] = max(0, min(100, state.get("ffb", 100) + step))
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 5:
                    # FFB PEAK LIMIT: OFF, 100, 80, 60, 40, 30 (cap of 127)
                    steps = [0, 100, 80, 60, 40, 30]
                    cur = int(state.get("ffbclamp", 0))
                    i = steps.index(cur) if cur in steps else 0
                    i = (i + (1 if key == glfw.KEY_RIGHT else -1)) % len(steps)
                    state["ffbclamp"] = steps[i]
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 6:
                    state["ffbinvert"] = 0 if state.get("ffbinvert", 0) else 1
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 7:
                    toggle_diag(upd)
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 8:
                    # internal render scale 2x-4x (GPU load ~ scale^2);
                    # applies at the next launch
                    step = 1 if key == glfw.KEY_RIGHT else -1
                    state["scale"] = max(2, min(4, int(state.get("scale", 4))
                                                + step))
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and ssel == 9:
                    state["transmission"] = (
                        "sequential"
                        if state.get("transmission", "hpattern") == "hpattern"
                        else "hpattern")
                    save_config(state)
                    audio.blip("nav")
                elif key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_SPACE):
                    if ssel in (0, 1):
                        k = "crt" if ssel == 0 else "crackfill"
                        state[k] = not state[k]
                        save_config(state)
                        audio.blip("nav")
                    elif ssel == 3:
                        state["marginfill"] = not state.get("marginfill", True)
                        save_config(state)
                        audio.blip("nav")
                    elif ssel == 9:
                        state["transmission"] = (
                            "sequential"
                            if state.get("transmission",
                                         "hpattern") == "hpattern"
                            else "hpattern")
                        save_config(state)
                        audio.blip("nav")
                    elif ssel in (2, 4, 5, 8):
                        audio.blip("nav")   # adjust with < > arrows
                    elif ssel == 12:
                        audio.blip("nav")
                        update_step(upd)
                    elif ssel == 11:
                        audio.blip("nav")
                        bundle_step(upd)
                    elif ssel == 7:
                        toggle_diag(upd)
                        audio.blip("nav")
                    elif ssel == 6:
                        state["ffbinvert"] = 0 if state.get("ffbinvert", 0) else 1
                        audio.blip("nav")
                    elif ssel == 10:
                        mode = "wizard"
                        wiz_idx = 0
                        wiz_bind = {}
                        wiz_last = ""
                        wiz_ready = False
                        wiz_base = wiz_settle = None
                        wiz_cool = 0.0
                        # the wizard only asks for the ACTIVE transmission
                        # mode's shift steps; the other mode's saved binds
                        # survive (save_wheelmap merges)
                        skipk = ({"shiftup", "shiftdn"}
                                 if state.get("transmission",
                                              "hpattern") == "hpattern"
                                 else {"gear1", "gear2", "gear3", "gear4"})
                        wiz_steps = [s for s in WIZARD_STEPS
                                     if s[1] not in skipk]
                        if rawjoy is not None and rawlis is None:
                            try:
                                rawlis = rawjoy.RawButtonListener()
                            except Exception:
                                rawlis = None
                        audio.blip("select")
                    else:
                        mode = "menu"
                        audio.blip("select")
                elif key == glfw.KEY_ESCAPE:
                    mode = "menu"
                    audio.blip("nav")
            actions.clear()
            if mode != "settings":
                # G6 forensics: settings closed - by which key?
                print(f"settings closed (keys={actions!r} mode={mode})",
                      flush=True)

        elif mode == "game":
            card = GAMES[sel][0]
            grows = game_rows(card)
            gsel = min(gsel, len(grows) - 1)
            for key in actions:
                if key in (glfw.KEY_UP, glfw.KEY_W):
                    gsel = (gsel - 1) % len(grows)
                    audio.blip("nav")
                elif key in (glfw.KEY_DOWN, glfw.KEY_S):
                    gsel = (gsel + 1) % len(grows)
                    audio.blip("nav")
                else:
                    rid = grows[gsel][0]
                    enter = key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER,
                                    glfw.KEY_SPACE)
                    lr = key in (glfw.KEY_LEFT, glfw.KEY_RIGHT)
                    if key == glfw.KEY_ESCAPE or (enter and rid == "back"):
                        mode = "menu"
                        audio.blip("nav")
                    elif enter and rid == "play":
                        launch = card
                        mode = "menu"
                        audio.blip("select")
                    elif lr and rid == "sens":
                        step = 10 if key == glfw.KEY_RIGHT else -10
                        cur = state["steersens"].get(card)
                        nxt = (100 if cur is None else cur) + step
                        state["steersens"][card] = (None if nxt == 100
                                                    else max(50, min(nxt, 300)))
                        save_config(state)
                        audio.blip("nav")
                    elif lr and rid == "curve":
                        step = 10 if key == glfw.KEY_RIGHT else -10
                        cur = state["steercurve"].get(card)
                        nxt = (100 if cur is None else cur) + step
                        state["steercurve"][card] = (None if nxt == 100
                                                     else max(50, min(nxt, 200)))
                        save_config(state)
                        audio.blip("nav")
                    elif lr and rid == "volume" and card in VOLUME_CMOS:
                        fname, addrs, vmax = VOLUME_CMOS[card]
                        rom = cmos_rom(card)
                        cur = cread(rom, fname, addrs[0])
                        if cur is not None:
                            step = max(1, round(vmax / 10))
                            if key == glfw.KEY_LEFT:
                                step = -step
                            cwrite(rom, fname, addrs,
                                   max(0, min(vmax, cur + step)))
                        audio.blip("nav")
                    elif (lr or enter) and rid == "freeplay":
                        fname, addrs = FREEPLAY_CMOS[card]
                        rom = cmos_rom(card)
                        cur = cread(rom, fname, addrs[0])
                        if cur is not None:
                            cwrite(rom, fname, addrs, 0 if cur else 1)
                        audio.blip("nav")
                    elif (lr or enter) and rid == "version":
                        state["world_rom"] = (
                            "crusnwld" if state.get("world_rom",
                                                    "crusnwld24")
                            == "crusnwld24" else "crusnwld24")
                        save_config(state)
                        cmos_cache.clear()
                        audio.blip("nav")
                    elif enter:
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
                        # open the per-game submenu (PLAY highlighted, so
                        # ENTER-ENTER still fast-paths into the game)
                        mode = "game"
                        gsel = 0
                        cmos_cache.clear()
                    else:
                        mode = "settings"
                        ssel = 0
                    audio.blip("select")
                elif key == glfw.KEY_ESCAPE:
                    glfw.set_window_should_close(win, True)
            actions.clear()
            # highlighting a different game card cross-fades its attract loop
            if row == 0 and sel != music_sel:
                music_sel = sel
                audio.start_music(GAMES[sel][0])

        ctx.clear(0, 0, 0, 1)
        t = time.time() % 3600
        if launching is not None:
            shell.draw_loading(launching["name"], t)
        elif mode == "wizard" and not wiz_ready:
            shell.draw_wizard_begin(t)
        elif mode == "wizard" and wiz_idx < len(wiz_steps):
            shell.draw_wizard(wiz_steps[wiz_idx][0], wiz_idx,
                              len(wiz_steps), wiz_last,
                              wiz_steps[wiz_idx][2],
                              max(0.0, wiz_cool - time.time()))
        elif mode == "settings":
            if upd["stage"] == "applied":
                glfw.set_window_should_close(win, True)   # updater takes over
            shell.draw_settings(ssel, state["crt"], state["crackfill"],
                                state["margin"], state.get("ffb", 100),
                                state.get("marginfill", True),
                                state.get("transmission", "hpattern"),
                                int(state.get("scale", 4)), t,
                                version=upd_version,
                                notice=upd["msg"] if time.time() < upd["until"]
                                else "", clamp=int(state.get("ffbclamp", 0)),
                                diag=run_rig.ffb_diag_enabled(),
                                invert=bool(state.get("ffbinvert", 0)))
        elif mode == "game":
            grows = game_rows(GAMES[sel][0])
            gsel = min(gsel, len(grows) - 1)
            shell.draw_game_menu(gsel, GAMES[sel][1],
                                 [(r[1], r[2]) for r in grows],
                                 grows[gsel][3], t)
        else:
            shell.draw(sel, state["crt"], t, row,
                       notice if time.time() < notice_until else "")
        glfw.swap_buffers(win)

        if launch and launching is None:
            # a pedal that reads pressed with nobody's foot on it (a Moza
            # load-cell brake comes up latched at full until pressed once)
            # makes the game burn out in 2nd gear with the tyres squealing
            # - refuse to launch until it has been pressed and released
            stuck = None
            for pedal in ("brake", "gas"):
                try:
                    v, sgn = nav_axis(pedal)
                except Exception:
                    v, sgn = None, None
                if v is None:
                    continue
                if sgn == "neg":
                    v = -v
                if (v > 0.55) if sgn in ("pos", "neg") else (abs(v) > 0.6):
                    stuck = pedal
            if stuck:
                notice = (f"{stuck.upper()} PEDAL READS PRESSED - PRESS IT "
                          "FULLY AND RELEASE, THEN LAUNCH AGAIN")
                notice_until = time.time() + 8
                audio.blip("nav")
                launch = None
                continue
            state["rom"] = launch
            save_config(state)
            fg_stop.set()   # the game owns the foreground now, stop fighting
            keeper.game_active.set()   # hand the telemetry stream to the game
            # fade the menu music out as the LAUNCHING screen comes up and
            # MAME boots (instead of an abrupt cut when the game appears)
            audio.stop_music(fade=1.2)
            launching = {"name": next(g[1] for g in GAMES if g[0] == launch),
                         "result": None, "err": None, "done": False}

            # the World card boots the configured revision (settings keys
            # and art stay keyed to the crusnwld card identity)
            real_rom = (state.get("world_rom", "crusnwld24")
                        if launch == "crusnwld" else launch)
            if launch == "crusnexo":
                # STEERING WHEEL POWER (operator adjustment, 1-10, default 5)
                # at 10: the game's own motor level; FFB STRENGTH scales it
                try:
                    if cmos_read("crusnexo", "m48t35", 0xC7) not in (None, 10):
                        cmos_write("crusnexo", "m48t35", [0xC7], 10)
                except Exception:
                    pass
            if launch == "crusnwld":
                real_rom, note = run_rig.resolve_world_rom(real_rom)
                if note:
                    print(note)
                    notice, notice_until = note.upper(), time.time() + 12
            boot_note = run_rig.boot_rom_note(real_rom)
            if boot_note:
                # MAME would abort at boot anyway - say why up front
                print(boot_note)
                notice = (GAMES[sel][1] + " " + boot_note).upper()[:110]
                notice_until = time.time() + 15
                launch = None
                audio.blip("nav")

            def _do_launch(box=launching, rom=real_rom, card=launch):
                # background thread: the shell keeps rendering LAUNCHING
                # instead of vanishing to the desktop while MAME boots
                try:
                    box["result"] = run_rig.launch_game_async(
                        rom=rom, scale=state["scale"],
                        windowed=args.windowed, crt=state["crt"],
                        crackfill=state["crackfill"],
                        steersens=state["steersens"].get(card),
                        steercurve=state["steercurve"].get(card),
                        margin=state["margin"], ffb=state.get("ffb", 100),
                        ffbclamp=state.get("ffbclamp", 0),
                        marginfill=state.get("marginfill", True))
                except BaseException as e:
                    box["err"] = str(e) or repr(e)
                box["done"] = True

            threading.Thread(target=_do_launch, daemon=True).start()
            launch = None

        if launching is not None and launching["done"]:
            if launching["err"] is not None:
                print("launch failed:", launching["err"])
                notice = ("COULDN'T START " + launching["name"] + ":  "
                          + str(launching["err"])).upper()[:110]
                notice_until = time.time() + 15
                keeper.game_active.clear()   # resume zeroing the dash
                armed_at = time.time() + 1.0
                audio.blip("nav")
            else:
                proc, game_hwnd = launching["result"]
                game_proc = proc
                audio.stop_music()   # already faded at launch; ensure closed
                # the shell window stays alive and fullscreen BEHIND the
                # game for the whole session - no desktop flash on launch
                # or return. Watch the WINDOW, not the process: teardown
                # (exit races, WER dumps) drags for seconds
                # after the player Esc-quits, and the window can outlive
                # its message pump through that drag, so two consecutive
                # WM_NULL timeouts also mean "exiting". Keep pumping our
                # own queue so Windows never ghosts the hidden shell.
                unresp = 0
                quit_all = False
                gaks = ctypes.windll.user32.GetAsyncKeyState
                while run_rig.u32.IsWindow(game_hwnd) and proc.poll() is None:
                    glfw.poll_events()
                    # Shift+F12 = quit the game AND the launcher (plain F12
                    # is the overlay's quit-to-launcher). WM_CLOSE is the
                    # clean path (forces released, NVRAM written).
                    if (gaks(0x7B) & 0x8000) and (gaks(0x10) & 0x8000):
                        quit_all = True
                        ctypes.windll.user32.PostMessageW(
                            ctypes.c_void_p(game_hwnd), 0x0010, 0, 0)
                    if run_rig.window_responding(game_hwnd):
                        unresp = 0
                    else:
                        unresp += 1
                        if unresp >= 2:
                            break
                    time.sleep(0.25)
                # make sure the process is really gone: a teardown that
                # hangs keeps the wheel's FFB device - the next game steers
                # but has no FFB. The emulator's own FFB releases the force
                # in its exit notifier; the OS drops it if the process dies.
                threading.Thread(target=run_rig.wait_or_kill, args=(proc,),
                                 daemon=True).start()
                keeper.game_active.clear()   # game gone: zero the dash again
                # joystick states changed while we were blocked (buttons
                # pressed in-game) - rebaseline or the first poll back
                # reads them as fresh presses and instantly relaunches
                joy_prev.clear()
                joy_seen.clear()
                ok_pending.clear()
                hat_prev = 0
                actions.clear()
                armed_at = time.time() + 1.0
                if quit_all:
                    glfw.set_window_should_close(win, True)
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
                audio.start_music(GAMES[sel][0])
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
