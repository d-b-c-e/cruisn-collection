"""Live button monitor - press things on the wheel/stalk/shifter/pad and
every edge prints with device, index, and the MAME token it would map to.

Usage: python harness/button_monitor.py     (Ctrl+C to stop)

Built to answer "why doesn't the wizard see my Start button": glfw
reports the MOZA R12 Base with 132 buttons, so the old 32-button theory
is dead - this shows exactly what arrives (or doesn't) when you press it.
"""
import sys
import time

import glfw

if not glfw.init():
    sys.exit("glfw init failed")

prev = {}
names = {}


def buttons(jid):
    r = glfw.get_joystick_buttons(jid)
    if r is None:
        return ()
    if isinstance(r, tuple) and len(r) == 2 and not isinstance(r[0], int):
        ptr, n = r
        return tuple(ptr[i] for i in range(n))
    return tuple(r)


def hats(jid):
    r = glfw.get_joystick_hats(jid)
    if r is None:
        return ()
    if isinstance(r, tuple) and len(r) == 2 and not isinstance(r[0], int):
        ptr, n = r
        return tuple(ptr[i] for i in range(n))
    return tuple(r)


print("watching for button presses (Ctrl+C to stop)...")
for jid in range(16):
    if glfw.joystick_present(jid):
        nm = glfw.get_joystick_name(jid)
        if isinstance(nm, bytes):
            nm = nm.decode(errors="replace")
        names[jid] = nm
        print(f"  [{jid}] {nm}: {len(buttons(jid))} buttons, "
              f"{len(hats(jid))} hats")
print()

try:
    while True:
        glfw.poll_events()
        for jid in list(names):
            if not glfw.joystick_present(jid):
                continue
            cur = buttons(jid)
            was = prev.get(jid, cur)
            for i in range(min(len(cur), len(was))):
                if cur[i] and not was[i]:
                    n = i + 1
                    tok = (f"BUTTON{n}" if n <= 32
                           else f"ADDSW{n - 32}" if n <= 48
                           else "OTHER_SWITCH (unaddressable in MAME)")
                    print(f"DOWN  {names[jid]}  button {i} "
                          f"(MAME JOYCODE_x_{tok})")
                elif was[i] and not cur[i]:
                    print(f"  up  {names[jid]}  button {i}")
            prev[jid] = cur
            h = hats(jid)
            hw = prev.get(("h", jid), h)
            for i in range(min(len(h), len(hw))):
                if h[i] != hw[i]:
                    print(f"HAT   {names[jid]}  hat {i} -> {h[i]:#x}")
            prev[("h", jid)] = h
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nbye")
glfw.terminate()
