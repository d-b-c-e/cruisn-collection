"""Compare the STOCK Cruis'n force feedback against ours, as algorithms.

Why this can work at all: the FFB Arcade Plugin reads MAME's `wheel_motor`
output, and so do we. Both sides therefore see the *same input signal* - the
signed motor byte the arcade code wrote - and differ only in what they do with
it. That makes a real comparison possible instead of two sets of impressions.

    stock : E:\\Games\\Reference\\crusnusa-stock  (MAME 0.286 + plugin 2.0.0.53)
            needs Logging=1 in FFBPlugin.ini  ->  FFBlog.txt
    ours  : the fork, with [collection] ffb_diag = 1
            ->  rig/ffb_trace.csv, 'wheel' rows (input) + 'shaped' rows (output)

The two runs are DIFFERENT DRIVES, so they cannot be aligned in time. What is
compared instead is the transfer function: for a given input byte, what force
does each side end up sending? Both sides smooth, so only samples where the
input has been steady for a while are used - otherwise you are measuring filter
lag, not the mapping.

Usage
-----
    python harness/ffb_compare.py                       # default locations
    python harness/ffb_compare.py --stock <FFBlog.txt> --ours <ffb_trace.csv>
    python harness/ffb_compare.py --dump-unparsed       # show lines it skipped

If the stock parser finds nothing, run with --dump-unparsed and look at what
the plugin actually wrote; its log vocabulary includes 'got value:' and
'Max Force: %d'. The parser is deliberately loose and easy to extend.
"""
import argparse
import collections
import os
import re
import sys

DEFAULT_STOCK = r"E:\Games\Reference\crusnusa-stock\FFBlog.txt"
DEFAULT_OURS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "rig", "ffb_trace.csv")

# What the stock plugin ships for Cruis'n USA, read straight out of its INI.
# These are the numbers our profile is being judged against.
STOCK_PARAMS = {
    "PowerModeCrusnUSA": 0,
    "FeedbackLengthCrusnUSA": 500,
    "MinForceCrusnUSA": 0,
    "MaxForceCrusnUSA": 70,
    "AlternativeMaxForceLeftCrusnUSA": -70,
    "AlternativeMaxForceRightCrusnUSA": 70,
    "EnableForceSpringEffectCrusnUSA": 1,
    "ForceSpringStrengthCrusnUSA": 72,
}


def parse_stock(path, keep_unparsed=False):
    """Pull (input, output) pairs out of the plugin's FFBlog.txt.

    The plugin logs 'got value: N' for what it read. Any number that follows on
    a nearby line is treated as a candidate force. Loose on purpose: the exact
    shape of this log is not documented and is worth eyeballing once.
    """
    got = []
    unparsed = []
    pending = None
    num = re.compile(r"-?\d+")
    try:
        lines = open(path, "r", errors="replace").read().splitlines()
    except OSError as e:
        return None, [], "cannot read %s (%s)" % (path, e)

    for ln in lines:
        t = ln.strip()
        if not t:
            continue
        m = re.match(r"(?i)got value:\s*(-?\d+)", t)
        if m:
            pending = int(m.group(1))
            continue
        m = re.match(r"(?i)max force:\s*(-?\d+)", t)
        if m and pending is not None:
            got.append((pending, int(m.group(1))))
            pending = None
            continue
        if pending is not None and num.fullmatch(t):
            got.append((pending, int(t)))
            pending = None
            continue
        if keep_unparsed and not t.startswith(("DLLMAIN", "process name", "dll process",
                                               "loading", "library", "creating", "Before",
                                               "After", "default centering")):
            unparsed.append(t)
    return got, unparsed, None


def parse_ours(path):
    """'wheel' rows are the input byte; 'shaped' rows are what we sent."""
    wheel, shaped = [], []
    try:
        lines = open(path, "r", errors="replace").read().splitlines()
    except OSError as e:
        return None, None, "cannot read %s (%s)" % (path, e)
    for ln in lines:
        if not ln or ln[0] == "#" or ln.startswith("ms,"):
            continue
        f = ln.split(",")
        if len(f) != 3:
            continue
        try:
            ms, name, val = int(f[0]), f[1], int(f[2])
        except ValueError:
            continue
        if name == "wheel":
            raw = val & 0xFF
            wheel.append((ms, raw - 256 if raw > 127 else raw))
        elif name == "shaped":
            shaped.append((ms, val))
    return wheel, shaped, None


def steady_pairs(wheel, shaped, settle_ms=200):
    """Input -> output, using only samples where the input has been steady.

    Both sides low-pass, so a sample taken right after a change measures the
    filter, not the mapping. Waiting settle_ms after the last input change is
    what makes the two comparable.
    """
    out = collections.defaultdict(list)
    if not wheel or not shaped:
        return out
    wi = 0
    cur, since = wheel[0][1], wheel[0][0]
    for ms, level in shaped:
        while wi + 1 < len(wheel) and wheel[wi + 1][0] <= ms:
            wi += 1
            if wheel[wi][1] != cur:
                cur, since = wheel[wi][1], wheel[wi][0]
        if ms - since >= settle_ms:
            out[cur].append(level)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stock", default=DEFAULT_STOCK)
    ap.add_argument("--ours", default=DEFAULT_OURS)
    ap.add_argument("--settle-ms", type=int, default=200)
    ap.add_argument("--dump-unparsed", action="store_true")
    a = ap.parse_args()

    print("STOCK vs OURS - Cruis'n USA force feedback")
    print("=" * 62)
    print("The plugin and the fork both read MAME's wheel_motor output, so the")
    print("input signal is identical by construction and only the algorithms differ.")
    print()

    print("Stock plugin parameters, from its own FFBPlugin.ini:")
    for k, v in STOCK_PARAMS.items():
        print("  %-34s %s" % (k, v))
    print()
    print("  Read that as: force is scaled into 0..70% of the device, symmetric")
    print("  left and right, WITH a 72% centring spring running alongside.")
    print()

    stock, unparsed, err = parse_stock(a.stock, a.dump_unparsed)
    print("-" * 62)
    if err:
        print("stock log: %s" % err)
        print("           drive the reference install first:")
        print("             cd E:\\Games\\Reference\\crusnusa-stock && .\\mame.exe crusnusa")
    else:
        print("stock log: %d (input, force) pairs from %s" % (len(stock), a.stock))
        if stock:
            ins = [p[0] for p in stock]
            outs = [p[1] for p in stock]
            print("           input  %d..%d      force %d..%d" %
                  (min(ins), max(ins), min(outs), max(outs)))
        else:
            print("           nothing parsed. Is Logging=1 set, and has it been driven?")
            print("           re-run with --dump-unparsed to see what it actually wrote.")
        if a.dump_unparsed and unparsed:
            print("\n  first 25 unparsed lines:")
            for u in unparsed[:25]:
                print("    %s" % u)

    wheel, shaped, err = parse_ours(a.ours)
    print("-" * 62)
    if err:
        print("our trace: %s" % err)
        print("           set [collection] ffb_diag = 1 and drive.")
        return 1
    print("our trace: %d input rows, %d output rows from %s" %
          (len(wheel), len(shaped), a.ours))
    if not shaped:
        print("           no 'shaped' rows - this trace predates the toolkit conversion.")
        print("           Drive again with the current build to get our output side.")
        return 1

    pairs = steady_pairs(wheel, shaped, a.settle_ms)
    print("           %d distinct steady input values (settled >= %d ms)" %
          (len(pairs), a.settle_ms))
    print()
    print("OUR transfer function, steady state")
    print("  %8s %10s %10s %8s" % ("byte", "median", "as % full", "n"))
    for b in sorted(pairs):
        v = sorted(pairs[b])
        med = v[len(v) // 2]
        print("  %8d %10d %9.1f%% %8d" % (b, med, 100.0 * med / 32767.0, len(v)))

    if stock:
        print()
        print("STOCK transfer function, all samples")
        agg = collections.defaultdict(list)
        for i, o in stock:
            agg[i].append(o)
        print("  %8s %10s %8s" % ("input", "median", "n"))
        for b in sorted(agg):
            v = sorted(agg[b])
            print("  %8d %10d %8d" % (b, v[len(v) // 2], len(v)))
        print()
        print("Compare the two tables by input value. A constant ratio is a gain")
        print("difference and is trivially fixable; a different SHAPE is not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
