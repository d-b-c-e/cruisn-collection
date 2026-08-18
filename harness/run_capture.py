"""Run the patched vunit build with quad logging + state dump enabled.

Same cleanroom setup as run_oracle.py (seeded NVRAM, explicit inis,
unthrottled, headless), plus:
    MIDV_QUADLOG          -> results/capture/quads.bin
    MIDV_STATEDUMP_FRAME  -> dump videoram/texram/palram at that frame
    MIDV_STATEDUMP_DIR    -> results/capture/

A snapshot is also taken at the dump frame so the state dump can be
cross-checked against what MAME itself displayed.
"""
import io
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VUNIT = sys.argv[1] if len(sys.argv) > 1 else r"E:\Source\mame-src\vunit.exe"
ROM = "crusnusa"
ROMPATH = r"E:\Source\launchbox\Launchbox-Racing\Emulators\mame286\roms"
DUMP_FRAME = int(sys.argv[2]) if len(sys.argv) > 2 else 2400
SUFFIX = f"-{DUMP_FRAME}" if len(sys.argv) > 2 else ""

cap = os.path.join(POC, "results", "capture" + SUFFIX)
if os.path.isdir(cap):
    shutil.rmtree(cap)
run = os.path.join(cap, "run")
ini = os.path.join(run, "ini")
for d in (ini, os.path.join(run, "snap"), os.path.join(run, "cfg")):
    os.makedirs(d, exist_ok=True)

seed = os.path.join(POC, "fixtures", f"nvram-{ROM}")
os.makedirs(os.path.join(run, "nvram"), exist_ok=True)
shutil.copytree(seed, os.path.join(run, "nvram", ROM))

with io.open(os.path.join(ini, "mame.ini"), "w") as f:
    f.write("skip_gameinfo 1\n")
with io.open(os.path.join(ini, "ui.ini"), "w") as f:
    f.write("skip_warnings 1\n")

cmd = [
    VUNIT, ROM,
    "-inipath", ini,
    "-rompath", ROMPATH,
    "-nvram_directory", os.path.join(run, "nvram"),
    "-cfg_directory", os.path.join(run, "cfg"),
    "-snapshot_directory", os.path.join(run, "snap"),
    "-autoboot_script", os.path.join(POC, "lua", "snap.lua"),
    "-autoboot_delay", "0",
    "-seconds_to_run", str(DUMP_FRAME // 57 + 30),   # backstop past the Lua exit
    "-nothrottle", "-video", "none", "-sound", "none",
    "-skip_gameinfo", "-snapview", "native",
]
env = dict(
    os.environ,
    SNAP_FRAMES=str(DUMP_FRAME),
    MIDV_QUADLOG=os.path.join(cap, "quads.bin"),
    # Lua exits right after its snapshot at DUMP_FRAME, and that snapshot's
    # screen_update still sees frame_number() == DUMP_FRAME-1 - so a gate at
    # DUMP_FRAME never fires before exit. Dump two frames early instead; the
    # comparison target is the dump itself, so alignment with the snapshot
    # PNG is cosmetic.
    MIDV_STATEDUMP_FRAME=str(DUMP_FRAME - 2),
    MIDV_STATEDUMP_DIR=cap,
)
print(f"capture: {os.path.basename(VUNIT)} {ROM} -> {cap}")
t0 = time.time()
p = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                   cwd=os.path.dirname(VUNIT), env=env)
print(f"exit={p.returncode}  {time.time()-t0:.1f}s")
if p.returncode != 0:
    sys.stdout.write(p.stdout[-3000:] + "\n" + p.stderr[-3000:] + "\n")
    sys.exit(1)

for name in ("quads.bin", "videoram.bin", "textureram.bin",
             "paletteram.bin", "meta.txt"):
    path = os.path.join(cap, name)
    ok = os.path.isfile(path)
    print(f"  {name:<16} {'%.1f MB' % (os.path.getsize(path)/1e6) if ok else 'MISSING'}")

snapdir = os.path.join(run, "snap", ROM)
if os.path.isdir(snapdir):
    for s in sorted(os.listdir(snapdir)):
        shutil.copy2(os.path.join(snapdir, s),
                     os.path.join(cap, f"mame-snapshot-{s}"))
        print(f"  mame snapshot    {s}")
print(io.open(os.path.join(cap, "meta.txt")).read().strip()
      if os.path.isfile(os.path.join(cap, "meta.txt")) else "no meta!")
