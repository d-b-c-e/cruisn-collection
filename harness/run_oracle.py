"""Determinism oracle for Cruis'n USA under MAME's software rasterizer.

Runs the same headless attract-mode capture twice in cleanroom conditions -
fresh nvram/cfg, explicit ini path, unthrottled, no audio/video output - and
compares the pixels of every snapshot pair. Identical pixels prove the attract
sequence is a reproducible frame source, which is what makes MAME usable as a
pixel-exact reference ("oracle") for a replacement renderer later.

Usage:
    python run_oracle.py [--mame PATH] [--rom NAME] [--frames 300,600,...]

Exit code 0 = deterministic (all pairs identical), 1 = mismatch or failure.
"""
import argparse
import hashlib
import io
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MAME = r"E:\Source\launchbox\Launchbox-Racing\Emulators\mame286\mame.exe"
DEFAULT_ROMPATH = r"E:\Source\launchbox\Launchbox-Racing\Emulators\mame286\roms"
LUA = os.path.join(POC, "lua", "snap.lua")


def pixel_hash(png_path):
    """Hash decoded pixels, not file bytes - PNG text chunks may differ."""
    from PIL import Image
    with Image.open(png_path) as im:
        return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()


def one_run(tag, args, workdir):
    run = os.path.join(workdir, tag)
    ini = os.path.join(run, "ini")
    snaps = os.path.join(run, "snap")
    for d in (ini, snaps, os.path.join(run, "nvram"), os.path.join(run, "cfg")):
        os.makedirs(d, exist_ok=True)

    # Seed calibrated NVRAM so boot goes to attract mode instead of parking on
    # the first-run "CALIBRATE CONTROLS - hit Enter" screen. Both runs get a
    # copy of the same fixture, so determinism is unaffected.
    seed = os.path.join(POC, "fixtures", f"nvram-{args.rom}")
    if os.path.isdir(seed):
        shutil.copytree(seed, os.path.join(run, "nvram", args.rom))

    # skip_gameinfo is a core option, skip_warnings a UI one - different files.
    with io.open(os.path.join(ini, "mame.ini"), "w") as f:
        f.write("skip_gameinfo 1\n")
    with io.open(os.path.join(ini, "ui.ini"), "w") as f:
        f.write("skip_warnings 1\n")

    cmd = [
        args.mame, args.rom,
        "-inipath", ini,
        "-rompath", args.rompath,
        "-nvram_directory", os.path.join(run, "nvram"),
        "-cfg_directory", os.path.join(run, "cfg"),
        "-snapshot_directory", snaps,
        "-autoboot_script", LUA,
        "-autoboot_delay", "0",
        "-seconds_to_run", str(args.max_seconds),   # backstop if Lua never exits
        "-nothrottle", "-video", "none", "-sound", "none",
        "-skip_gameinfo",
        # Raw 512x400 screen only - no bezel artwork compositing. The oracle
        # compares what the RENDERER produced, not the presentation layer.
        "-snapview", "native",
    ]
    env = dict(os.environ, SNAP_FRAMES=args.frames)
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                       cwd=os.path.dirname(args.mame), env=env)
    dt = time.time() - t0

    game_dir = os.path.join(snaps, args.rom)
    shots = sorted(os.listdir(game_dir)) if os.path.isdir(game_dir) else []
    print(f"  [{tag}] exit={p.returncode}  {dt:.1f}s  snapshots={len(shots)}")
    if p.returncode not in (0,) or not shots:
        sys.stdout.write(p.stdout[-2000:] + "\n" + p.stderr[-2000:] + "\n")
    return [os.path.join(game_dir, s) for s in shots]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mame", default=DEFAULT_MAME)
    ap.add_argument("--rom", default="crusnusa")
    ap.add_argument("--rompath", default=DEFAULT_ROMPATH)
    ap.add_argument("--frames", default="300,600,900,1200,1800,2400,3000,3600")
    ap.add_argument("--max-seconds", type=int, default=120)
    ap.add_argument("--keep", action="store_true",
                    help="keep run dirs (default: removed on success)")
    args = ap.parse_args()

    workdir = os.path.join(POC, "results", "oracle-runs")
    if os.path.isdir(workdir):
        shutil.rmtree(workdir)

    frame_list = args.frames.split(",")
    print(f"oracle: {args.rom} @ frames {args.frames}")
    a = one_run("a", args, workdir)
    b = one_run("b", args, workdir)

    if len(a) != len(b) or not a:
        print(f"FAIL: snapshot counts differ or empty ({len(a)} vs {len(b)})")
        return 1

    ok = True
    print(f"\n  {'frame':>6}  {'run A':<16} {'run B':<16} verdict")
    for i, (pa, pb) in enumerate(zip(a, b)):
        ha, hb = pixel_hash(pa), pixel_hash(pb)
        match = ha == hb
        ok &= match
        frame = frame_list[i] if i < len(frame_list) else "?"
        print(f"  {frame:>6}  {ha[:16]} {hb[:16]} "
              f"{'identical' if match else '*** MISMATCH ***'}")

    if ok:
        # Preserve one copy of the frames as the reference set.
        ref = os.path.join(POC, "results", "reference-frames")
        if os.path.isdir(ref):
            shutil.rmtree(ref)
        os.makedirs(ref)
        for i, pa in enumerate(a):
            frame = frame_list[i] if i < len(frame_list) else str(i)
            shutil.copy2(pa, os.path.join(ref, f"frame_{int(frame):05d}.png"))
        if not args.keep:
            shutil.rmtree(workdir)
        print(f"\nPASS: attract mode is deterministic. "
              f"Reference frames -> results/reference-frames/")
        return 0

    print("\nFAIL: runs differ - attract mode is NOT a usable oracle as-is")
    return 1


if __name__ == "__main__":
    sys.exit(main())
