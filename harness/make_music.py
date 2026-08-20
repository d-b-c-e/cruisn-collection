"""Menu-music pipeline: YouTube URL -> trimmed, normalized shell loop.

Downloads bestaudio via yt-dlp, cuts the head off (default 17 s - skip an
intro), loudness-normalizes, and writes rig/assets/menumusic.wav, which the
collection shell loops. Re-run any time to change the track.

Usage: python harness/make_music.py <url> [--skip 17] [--duration N]
"""
import argparse
import os
import subprocess
import sys
import tempfile

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(POC, "rig", "assets", "menumusic.mp3")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--skip", type=float, default=17.0,
                    help="seconds to trim from the start (default 17)")
    ap.add_argument("--duration", type=float, default=0,
                    help="optional max length in seconds (0 = to the end)")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "src.m4a")
        subprocess.run([sys.executable, "-m", "yt_dlp", "-q",
                        "-f", "bestaudio", "-o", src, args.url], check=True)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-ss", str(args.skip), "-i", src]
        if args.duration:
            cmd += ["-t", str(args.duration)]
        cmd += ["-vn", "-ac", "2", "-ar", "44100",
                "-af", "loudnorm=I=-18", "-b:a", "192k", OUT]
        subprocess.run(cmd, check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", OUT],
                         capture_output=True, text=True).stdout.strip()
    print(f"wrote {OUT}: {float(dur or 0):.0f}s")


if __name__ == "__main__":
    sys.exit(main())
