"""CMOS/NVRAM tuning workflow - the "squeeze quality out of settings"
system. The games keep operator settings (coinage, free play, attract/game
volume, difficulty) in battery-backed CMOS, which we already ship as
fixtures/nvram-<rom>/ seeds. This tool locates and bakes them:

  snapshot <rom>   copy the rig's current NVRAM aside
  diff <rom>       show byte-level changes vs the latest snapshot
  bake <rom>       copy the rig's current NVRAM into fixtures/nvram-<rom>/
                   (the seed every fresh install boots from)

Flow to bake a setting for all future installs:
  1. python harness/nvram_tool.py snapshot offroadc
  2. boot the game, change EXACTLY ONE thing in the service menu (F2),
     exit the game cleanly
  3. python harness/nvram_tool.py diff offroadc   -> the changed bytes
  4. repeat 1-3 per setting to map them; when the rig NVRAM has all
     settings the way the collection should ship (coinage 1/1 or free
     play, volume up, ...): python harness/nvram_tool.py bake <rom>

ROMs are never modified - the legal bright line stays intact. Note for
public release: steering calibration also lives in this CMOS and is
wheel-specific; map its bytes (same flow) so bake can exclude them.
"""
import os
import shutil
import sys
import time

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIG_NVRAM = os.path.join(POC, "rig", "nvram")
SNAP_ROOT = os.path.join(POC, "rig", "nvram-snapshots")


# CMOS byte map, established 2026-08-26 by single-byte persistence
# experiments (change one byte, boot headless, verify it survives):
# NO GAME GUARDS ITS SETTINGS WITH A CHECKSUM - byte pokes are safe.
#   crusnwld  nvram   0x93C = master volume (user's service-menu 11 = 0x0B)
#   offroadc  nvram   0x7BC and 0x92C = the two volume fields (menu wrote
#                     both to 0x32; exact master-vs-minimum split TBD)
#   crusnexo  m48t35  0x27 = volume-region byte (min-volume session hit it)
#   crusnusa  nvram   0x200/0x205/0x20A/0x20F = 4x mirrored volume-region
#                     field (service menu writes all four; the game accepts
#                     a lone change - write all four to stay tidy)
# Free play (pinned 2026-08-29 by flipping candidates off and diffing the
# attract screen videoram against the free-play-ON reference):
#   crusnwld  nvram   0x1AC = free play (0=coins, 1=free)
#   offroadc  nvram   0x1CC = free play (0=coins, 1=free)
#   crusnexo  m48t35  0x73 = free play (pinned 2026-08-29, same method via
#                     lua-snapshot diffs; only reactive candidate of six)
#   crusnusa  pending the user's F2 toggle diff.
# RTC/counters churn at 0x7FF9+ (exotica) and scattered words - ignore.


def poke(rom, fname, addr, val):
    """Set one byte in the rig NVRAM (with a timestamped snapshot first)."""
    snapshot(rom)
    path = os.path.join(RIG_NVRAM, rom, fname)
    with open(path, "rb") as f:
        data = bytearray(f.read())
    old = data[addr]
    data[addr] = val & 0xFF
    with open(path, "wb") as f:
        f.write(data)
    print(f"{rom}/{fname} 0x{addr:X}: 0x{old:02X} -> 0x{val & 0xFF:02X}")


def latest_snapshot(rom):
    root = os.path.join(SNAP_ROOT, rom)
    if not os.path.isdir(root):
        return None
    snaps = sorted(os.listdir(root))
    return os.path.join(root, snaps[-1]) if snaps else None


def snapshot(rom):
    src = os.path.join(RIG_NVRAM, rom)
    if not os.path.isdir(src):
        sys.exit(f"no rig NVRAM for {rom} ({src})")
    dst = os.path.join(SNAP_ROOT, rom, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copytree(src, dst, dirs_exist_ok=True)
    print(f"snapshotted {src} -> {dst}")


def diff(rom):
    snap = latest_snapshot(rom)
    if snap is None:
        sys.exit(f"no snapshot for {rom} - run snapshot first")
    cur = os.path.join(RIG_NVRAM, rom)
    print(f"diff vs {snap}")
    any_change = False
    for name in sorted(os.listdir(cur)):
        a_path = os.path.join(snap, name)
        b_path = os.path.join(cur, name)
        if not os.path.isfile(a_path):
            print(f"  {name}: NEW file")
            any_change = True
            continue
        a = open(a_path, "rb").read()
        b = open(b_path, "rb").read()
        if len(a) != len(b):
            print(f"  {name}: size {len(a)} -> {len(b)}")
            any_change = True
            continue
        run = None
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                if run is None:
                    run = i
            elif run is not None:
                print(f"  {name} @ {run:#06x}..{i - 1:#06x}: "
                      f"{a[run:i].hex()} -> {b[run:i].hex()}")
                any_change = True
                run = None
        if run is not None:
            print(f"  {name} @ {run:#06x}..{len(a) - 1:#06x}: "
                  f"{a[run:].hex()} -> {b[run:].hex()}")
            any_change = True
    if not any_change:
        print("  (no changes)")


def bake(rom):
    src = os.path.join(RIG_NVRAM, rom)
    dst = os.path.join(POC, "fixtures", f"nvram-{rom}")
    if not os.path.isdir(src):
        sys.exit(f"no rig NVRAM for {rom}")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    print(f"baked {src} -> {dst} (commit fixtures/ to ship it)")


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("snapshot", "diff", "bake"):
        sys.exit(__doc__)
    {"snapshot": snapshot, "diff": diff, "bake": bake}[sys.argv[1]](sys.argv[2])


if __name__ == "__main__":
    main()
