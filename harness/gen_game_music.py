"""Per-game menu music from the LaunchBox attract video snaps.

Extracts the audio from each game's Video Snap, loudness-normalizes it, and
writes rig/assets/menumusic-<rom>.mp3. The collection shell plays the track
for the highlighted game (menumusic-<rom>), falling back to the generic
menumusic.* when a per-game file is absent. Re-run any time; --url per game
overrides a snap with a downloaded track (uses make_music's yt-dlp path).

Usage:
  python harness/gen_game_music.py            # all four from video snaps
  python harness/gen_game_music.py crusnusa   # just one
"""
import os
import subprocess
import sys

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(POC, "rig", "assets")
VID = r"E:\Source\launchbox\Launchbox-Racing\Videos\Arcade"

# rom -> video-snap basename (attract audio source)
SNAP = {
    "crusnusa": "Cruis_n USA-01",
    "crusnwld": "Cruis_n World-01",
    "offroadc": "Off Road Challenge-01",
    "crusnexo": "Cruis_n Exotica-01",
}
# skip a few seconds of quiet lead-in per game (attract logos before music)
SKIP = {"crusnusa": 2.0, "crusnwld": 1.0, "offroadc": 2.0, "crusnexo": 1.0}


def build(rom):
    src = os.path.join(VID, SNAP[rom] + ".mp4")
    if not os.path.isfile(src):
        print(f"  {rom}: no video snap at {src} - skipped")
        return False
    out = os.path.join(ASSETS, f"menumusic-{rom}.mp3")
    os.makedirs(ASSETS, exist_ok=True)
    # -ss before -i seeks; loudnorm to a consistent level across games so
    # switching tracks doesn't jump volume; fade the tail 1.5 s so the loop
    # seam isn't a hard cut
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", src],
        capture_output=True, text=True).stdout.strip() or 0)
    skip = SKIP.get(rom, 1.0)
    body = max(4.0, dur - skip)
    fade_start = max(0.0, body - 1.5)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(skip), "-i", src,
         "-vn", "-ac", "2", "-ar", "44100",
         "-af", f"loudnorm=I=-18,afade=t=out:st={fade_start}:d=1.5",
         "-b:a", "192k", out], check=True)
    print(f"  {rom}: {SNAP[rom]}.mp4 ({dur:.0f}s) -> menumusic-{rom}.mp3")
    return True


def main():
    roms = sys.argv[1:] if len(sys.argv) > 1 else list(SNAP)
    print("extracting per-game menu music from attract video snaps:")
    ok = sum(build(r) for r in roms if r in SNAP)
    print(f"done: {ok}/{len(roms)} tracks")


if __name__ == "__main__":
    main()
