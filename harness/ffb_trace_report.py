"""Summarize a force-feedback trace (rig/ffb_trace.csv from a support
bundle, written when FFB diagnostics are on) so a tester's "the wheel
goes crazy" turns into numbers.

The V-Unit games (USA, World, Off Road) write one signed byte per update
to the wheel motor, MAME exposes it as output "wheel" (0..255, two's
complement: 255 = -1). The force is a kick opposite to and proportional
to each wheel movement (a damper), decaying to zero within ~100 ms.

  python harness/ffb_trace_report.py rig/ffb_trace.csv

Rows "wheelpos" (added 2026-09-03) carry the steering INPUT the game read
(0..255, centre 128) whenever it changed - the other half of the force
loop, so a Fanatec-style oscillation shows up as the wheel swinging in
step with the kicks. A PNG plot of the last 20 s is written next to the
csv (also shipped in the support bundle).
"""
import csv
import sys


def signed(v):
    return v - 256 if v > 127 else v


def oscillation(pos):
    """pos: [(ms, 0..255)] wheel position samples. Returns (peak-to-peak
    counts, swings per second, seconds analysed) over the busiest 10 s."""
    if len(pos) < 8:
        return 0, 0.0, 0.0
    t0, t1 = pos[0][0], pos[-1][0]
    span = (t1 - t0) / 1000.0
    if span <= 0:
        return 0, 0.0, 0.0
    # slide a 10 s window, keep the one with the most direction reversals
    best = (0, 0.0)
    i = 0
    for j in range(len(pos)):
        while pos[j][0] - pos[i][0] > 10000:
            i += 1
        seg = pos[i:j + 1]
        if len(seg) < 6:
            continue
        vals = [v for _, v in seg]
        pp = max(vals) - min(vals)
        rev = sum(1 for a, b, c in zip(vals, vals[1:], vals[2:])
                  if (b - a) * (c - b) < 0 and abs(b - a) > 3 and abs(c - b) > 3)
        secs = max(0.001, (seg[-1][0] - seg[0][0]) / 1000.0)
        if rev / secs > best[1]:
            best = (pp, rev / secs)
    return best[0], best[1] / 2.0, min(10.0, span)   # two reversals = one swing


def plot(path, rows, pos, out_png):
    """Force (signed) and wheel position over the last 20 s, as a PNG - no
    plotting library needed in the frozen build."""
    from PIL import Image, ImageDraw
    W, H = 1400, 420
    im = Image.new("RGB", (W, H), (18, 18, 24)); d = ImageDraw.Draw(im)
    w = [(ms, signed(v)) for ms, n, v in rows if n == "wheel"]
    if not w and not pos:
        return None
    t1 = max([ms for ms, _ in w] + [ms for ms, _ in pos]); t0 = max(0, t1 - 20000)
    def X(ms): return 60 + (ms - t0) * (W - 80) / max(1, (t1 - t0))
    d.line([(60, H // 2), (W - 20, H // 2)], fill=(70, 70, 80))
    d.text((6, H // 2 - 6), "0", fill=(160, 160, 170))
    d.text((6, 8), "force +127", fill=(255, 150, 80)); d.text((6, H - 20), "force -127", fill=(255, 150, 80))
    d.text((W - 260, 8), "wheel position (0..255, centre 128)", fill=(90, 200, 255))
    ppos = [(X(ms), H - (v / 255.0) * (H - 20) - 10) for ms, v in pos if ms >= t0]
    if len(ppos) > 1: d.line(ppos, fill=(90, 200, 255), width=2)
    pf = [(X(ms), H // 2 - v * (H // 2 - 10) / 127.0) for ms, v in w if ms >= t0]
    if len(pf) > 1: d.line(pf, fill=(255, 150, 80), width=2)
    d.text((60, H - 12), f"last {min(20.0, (t1 - t0) / 1000.0):.0f} s of {path.split(chr(92))[-1].split('/')[-1]}", fill=(160, 160, 170))
    im.save(out_png)
    return out_png


def report(path, png=None):
    rows = []
    pos = []
    game = "?"
    with open(path, encoding="utf-8", errors="replace") as f:
        for r in csv.reader(f):
            if len(r) >= 1 and r[0].startswith("# game"):
                game = r[0].split()[-1]
            if len(r) == 3 and r[0].isdigit():
                if r[1] == "wheelpos":
                    pos.append((int(r[0]), int(r[2])))
                else:
                    rows.append((int(r[0]), r[1], int(r[2])))
    print(f"trace: {path}  game {game}  {len(rows)} outputs, {len(pos)} wheel-position samples")
    if pos:
        pp, swings, secs = oscillation(pos)
        deg = pp / 255.0 * 270.0
        print(f"  wheel position: peak-to-peak {pp} counts (~{deg:.0f} deg of a 270 deg wheel) in the busiest "
              f"10 s, {swings:.1f} swings/s")
        if swings >= 2.0 and pp >= 40:
            print("  VERDICT (wheel): the wheel itself is oscillating - the classic force/position "
                  "loop. Lower FFB STRENGTH or set ffb_slew / FFB PEAK LIMIT.")
        elif pp < 15:
            print("  wheel barely moved in the trace - forces were not moving it (or hands held it)")
    if png:
        out = plot(path, rows, pos, png)
        if out:
            print(f"  plot: {out}")
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
        report(p, png=p.rsplit(".", 1)[0] + ".png")
