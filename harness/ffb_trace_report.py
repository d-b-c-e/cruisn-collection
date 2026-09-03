"""Summarize a force-feedback trace (rig/ffb_trace.csv from a support
bundle, written when FFB diagnostics are on) so a tester's "the wheel
goes crazy" turns into numbers.

The V-Unit games (USA, World, Off Road) write one signed byte per update
to the wheel motor, MAME exposes it as output "wheel" (0..255, two's
complement: 255 = -1). The force is a kick opposite to and proportional
to each wheel movement (a damper), decaying to zero within ~100 ms.

  python harness/ffb_trace_report.py rig/ffb_trace.csv
"""
import csv
import sys


def signed(v):
    return v - 256 if v > 127 else v


def report(path):
    rows = []
    game = "?"
    with open(path, encoding="utf-8", errors="replace") as f:
        for r in csv.reader(f):
            if len(r) >= 1 and r[0].startswith("# game"):
                game = r[0].split()[-1]
            if len(r) == 3 and r[0].isdigit():
                rows.append((int(r[0]), r[1], int(r[2])))
    print(f"trace: {path}  game {game}  {len(rows)} outputs")
    names = sorted(set(n for _, n, _ in rows))
    for n in names:
        if n != "wheel":
            vals = [v for _, m, v in rows if m == n]
            print(f"  {n:12s} {len(vals):6d} updates, values {sorted(set(vals))[:8]}")
    w = [(ms, signed(v)) for ms, n, v in rows if n == "wheel"]
    if not w:
        print("  wheel: no force output at all - the game never drove the "
              "motor (Exotica has none; V-Unit games: was a race running?)")
        return
    span = (w[-1][0] - w[0][0]) / 1000.0
    peak = max(abs(v) for _, v in w)
    big = sum(1 for _, v in w if abs(v) >= 64)
    flips = sum(1 for (_, a), (_, b) in zip(w, w[1:])
                if a and b and (a > 0) != (b > 0))
    # bursts: runs of updates less than 50 ms apart
    bursts, cur = [], [w[0]]
    for a, b in zip(w, w[1:]):
        if b[0] - a[0] < 50:
            cur.append(b)
        else:
            bursts.append(cur)
            cur = [b]
    bursts.append(cur)
    print(f"  wheel: {len(w)} updates over {span:.1f} s, peak |force| "
          f"{peak}/127, {big} updates at >= 64 (half of full), "
          f"{flips} direction flips")
    print(f"  {len(bursts)} bursts (kicks); per second: "
          f"{len(bursts) / span if span else 0:.1f}")
    if span and flips / span > 4 and peak >= 64:
        print("  VERDICT: sustained strong alternating kicks = the damper "
              "loop oscillating (wheel too strong for the game's force "
              "law). Lower FFB STRENGTH (30-40% on a direct-drive base) "
              "or set MIDV_FFB_CLAMP / the FFB PEAK LIMIT setting.")
    elif peak >= 100:
        print("  NOTE: near-full-strength kicks present - on a strong wheel "
              "lower FFB STRENGTH first.")
    else:
        print("  looks tame: forces small and infrequent.")
    print("  first bursts:")
    for b in bursts[:6]:
        print(f"    {b[0][0]:8d} ms  {len(b):3d} updates  "
              + " ".join(f"{v:+d}" for _, v in b[:14]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        report(p)
