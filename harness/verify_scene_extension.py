"""Verify that an isolated widescreen experiment only adds off-screen quads.

Compare matched captures, not arbitrary frames from independently shifted runs.
Native GPU/index correctness is checked separately with gpu/renderer.py.
"""
import argparse
from collections import Counter
from pathlib import Path
import sys

import numpy as np
from verification import required_files, sha256_file, write_json
from run_capture import ARTIFACTS


def compare_quads(reference, candidate):
    a = Counter(q.tobytes() for q in reference)
    b = Counter(q.tobytes() for q in candidate)
    extra = b - a
    intrusions = 0
    for raw, count in extra.items():
        x = np.frombuffer(raw, "<u2")[2:10:2].view("<i2")
        if not (x.max() < 0 or x.min() > 511):
            intrusions += count
    position = 0
    for q in candidate:
        if position < len(reference) and q.tobytes() == reference[position].tobytes():
            position += 1
    return {"original_quads": int(len(reference)), "candidate_quads": int(len(candidate)),
            "removed_or_changed_quads": sum((a - b).values()), "added_quads": sum(extra.values()),
            "original_draw_order_preserved": position == len(reference),
            "added_quads_intersecting_native_x": intrusions}


def added_quad_coverage(reference, candidate, page_control, clip_right, clip_bottom, words):
    """Conservative native coverage of added primitives, using the CPU DDA.

    Ignore texture transparency and dithering to bound *possible* writes. This
    attributes changes spatially; it does not certify the new artwork or physics.
    Duplicate submissions count separately, just as in compare_quads().
    """
    from rasterize import render_quad
    remaining = Counter(q.tobytes() for q in reference)
    coverage = np.zeros(words, dtype=bool)
    pixels = np.zeros(words, dtype=np.uint16)
    for quad in candidate:
        key = quad.tobytes()
        if remaining[key]:
            remaining[key] -= 1
            continue
        flat = quad.copy()
        flat[0], flat[1] = 0, 1
        render_quad(flat, page_control, pixels, np.zeros(1, np.uint8),
                    clip_right, clip_bottom, cover=coverage)
    return coverage


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reference", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--object-visibility", action="store_true",
                    help="explicitly allow new native-edge primitives; require identical history, "
                         "unchanged original draws/resources and attribute every changed VRAM word")
    args = ap.parse_args(argv)
    report = {"schema": 1, "scope": "matched-state off-screen geometry extension", "passed": False}
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gpu"))
        from renderer import load_scene
        for path in (args.reference, args.candidate): required_files(path, ARTIFACTS)
        a, apc, ameta, ah = load_scene(str(args.reference))
        b, bpc, bmeta, bh = load_scene(str(args.candidate))
        report["geometry"] = compare_quads(a[ah:], b[bh:])
        report["same_frame_and_page"] = bool(ameta == bmeta and apc == bpc)
        hashes = [{name: sha256_file(path / name) for name in ARTIFACTS}
                  for path in (args.reference, args.candidate)]
        report["reference"] = {"path": str(args.reference.resolve()), "sha256": hashes[0]}
        report["candidate"] = {"path": str(args.candidate.resolve()), "sha256": hashes[1]}
        resources = ("videoram.bin", "textureram.bin", "paletteram.bin")
        report["unchanged_resources"] = {name: hashes[0][name] == hashes[1][name] for name in resources}
        g = report["geometry"]
        geometry_ok = (report["same_frame_and_page"]
            and g["added_quads"] > 0 and g["removed_or_changed_quads"] == 0
            and g["original_draw_order_preserved"])
        if args.object_visibility:
            report["scope"] = "matched-state object visibility extension; new native geometry explicitly allowed"
            report["same_previous_page_scene"] = bool(np.array_equal(a[:ah], b[:bh]))
            av = np.fromfile(args.reference / "videoram.bin", "<u2")
            bv = np.fromfile(args.candidate / "videoram.bin", "<u2")
            if av.shape != bv.shape: raise ValueError("VRAM sizes differ")
            cover = added_quad_coverage(a[ah:], b[bh:], bpc, *bmeta["visarea"], av.size)
            changed = av != bv
            unexplained = np.flatnonzero(changed & ~cover)
            report["native_attribution"] = {
                "changed_words": int(changed.sum()),
                "outside_added_coverage": int(len(unexplained)),
                "first_unexplained_addresses": unexplained[:20].tolist(),
                "limitation": "spatial attribution, not a visual-quality or physics-equivalence claim"}
            report["passed"] = (geometry_ok and report["same_previous_page_scene"]
                and report["unchanged_resources"]["textureram.bin"]
                and report["unchanged_resources"]["paletteram.bin"] and not len(unexplained))
        else:
            report["passed"] = (geometry_ok and all(report["unchanged_resources"].values())
                and g["added_quads_intersecting_native_x"] == 0)
    except (ValueError, OSError, AssertionError) as exc:
        report["error"] = str(exc)
    write_json(args.report, report)
    print("PASS" if report["passed"] else "FAIL", report.get("geometry", report.get("error")))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
