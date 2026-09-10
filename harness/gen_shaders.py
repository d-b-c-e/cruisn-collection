"""Regenerate midvunit_gl_shaders.h from gpu/renderer.py (the shader source
of truth). Run from the cruisn-collection root after ANY shader change:

    python harness/gen_shaders.py

Emits classic escaped C string literals, NOT raw strings - genie's source
scanner (REGENIE=1 builds) cannot tokenize R"( )" and dies with
"unterminated character literal"."""
import os
import sys

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(POC, "gpu"), os.path.join(POC, "harness")]
import renderer as R  # noqa: E402
import zeus_renderer as Z  # noqa: E402
from zeus_depth import compatibility_fragment  # noqa: E402

HEADER = r"E:\Source\mame-src\src\mame\midway\midvunit_gl_shaders.h"
ZHEADER = r"E:\Source\mame-src\src\devices\video\zeus2_gl_shaders.h"


def cstr(prefix, name, src):
    out = [f"static const char *{prefix}_{name} ="]
    for ln in src.split("\n"):
        esc = ln.replace("\\", "\\\\").replace('"', '\\"')
        out.append(f'\t"{esc}\\n"')
    out[-1] += ";"
    return "\n".join(out) + "\n\n"


def main():
    body = "// GENERATED from cruisn-collection/gpu/renderer.py"
    body += " - regenerate with harness/gen_shaders.py, never hand-edit\n\n"
    for n in ("VS", "FS", "PAL_VS", "PAL_FS", "CPU_FS", "MENU_VS", "MENU_FS"):
        body += cstr("MVGL", n, getattr(R, n))
    with open(HEADER, "w", newline="\n") as f:
        f.write(body)
    print(f"wrote {HEADER} ({len(body)} bytes)")

    body = "// GENERATED from cruisn-collection/gpu/zeus_renderer.py"
    body += " (menu from gpu/renderer.py) - regenerate with"
    body += " harness/gen_shaders.py, never hand-edit\n\n"
    for n in ("VS", "FS", "PRESENT_VS", "PRESENT_FS"):
        body += cstr("MZGL", n, getattr(Z, n))
    body += cstr("MZGL", "DEPTH_COMPAT_FS", compatibility_fragment(Z.FS))
    for n in ("MENU_VS", "MENU_FS"):
        body += cstr("MZGL", n, getattr(R, n))
    with open(ZHEADER, "w", newline="\n") as f:
        f.write(body)
    print(f"wrote {ZHEADER} ({len(body)} bytes)")


if __name__ == "__main__":
    main()
