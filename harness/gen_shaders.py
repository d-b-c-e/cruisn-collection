"""Regenerate midvunit_gl_shaders.h from gpu/renderer.py (the shader source
of truth). Run from the cruisn-poc root after ANY shader change:

    python harness/gen_shaders.py

Emits classic escaped C string literals, NOT raw strings - genie's source
scanner (REGENIE=1 builds) cannot tokenize R"( )" and dies with
"unterminated character literal"."""
import os
import sys

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(POC, "gpu"), os.path.join(POC, "harness")]
import renderer as R  # noqa: E402

HEADER = r"E:\Source\mame-src\src\mame\midway\midvunit_gl_shaders.h"


def cstr(name, src):
    out = [f"static const char *MVGL_{name} ="]
    for ln in src.split("\n"):
        esc = ln.replace("\\", "\\\\").replace('"', '\\"')
        out.append(f'\t"{esc}\\n"')
    out[-1] += ";"
    return "\n".join(out) + "\n\n"


def main():
    body = "// GENERATED from cruisn-poc/gpu/renderer.py"
    body += " - regenerate with harness/gen_shaders.py, never hand-edit\n\n"
    for n in ("VS", "FS", "PAL_VS", "PAL_FS", "MENU_VS", "MENU_FS"):
        body += cstr(n, getattr(R, n))
    with open(HEADER, "w", newline="\n") as f:
        f.write(body)
    print(f"wrote {HEADER} ({len(body)} bytes)")


if __name__ == "__main__":
    main()
