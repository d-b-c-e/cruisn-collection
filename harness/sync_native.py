"""Check/copy project-owned native helpers into the separately committed MAME tree."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mame", type=Path, default=Path(r"E:\Source\mame-src"))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    source = ROOT / "native" / "hud_speed_filter.h"
    target = args.mame / "src" / "mame" / "midway" / "cruisn" / source.name
    expected = source.read_bytes().replace(b"\r\n", b"\n")
    actual = target.read_bytes().replace(b"\r\n", b"\n") if target.exists() else None
    if actual == expected:
        print("project native helpers match")
        return 0
    if args.write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(expected)
        print(f"updated {target}")
        return 0
    print(f"native helper differs or is missing: {target}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
