"""Compare completed GL frames; asynchronous legacy captures are not frame oracles."""
import argparse
import csv
from pathlib import Path
import sys

from verification import image_signature, write_json


def read_completed_frames(directory, expected=None):
    directory = Path(directory)
    with (directory / "captures.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or "completed_frame" not in rows[0]:
        raise ValueError("completed-frame GL captures required; legacy asynchronous images are insufficient")
    frames, previous, names = {}, -1, set()
    for row in rows:
        frame = int(row["completed_frame"])
        if frame <= previous or frame != int(row["last_received_frame"]):
            raise ValueError("GL frame fences are duplicated, unordered or inconsistent")
        if int(row["dropped_messages"]) != 0:
            raise ValueError("GL stream lost persistent rendering state")
        name = row["file"]
        if Path(name).name != name or name in ("", ".", ".."):
            raise ValueError("GL capture filename must be local to its directory")
        if name in names:
            raise ValueError("GL capture filename was reused; earlier frame pixels may be overwritten")
        names.add(name)
        signature = image_signature(directory / name)
        if signature["size"] != [int(row["width"]), int(row["height"])]:
            raise ValueError("GL image dimensions differ from the capture receipt")
        frames[frame] = signature
        previous = frame
    if expected is not None and list(frames) != list(expected):
        raise ValueError("completed GL capture interval is incomplete")
    return frames


def compare_completed_frames(reference, candidate, expected=None, details=False):
    a, b = read_completed_frames(reference, expected), read_completed_frames(candidate, expected)
    if a.keys() != b.keys():
        raise ValueError("GL recordings cover different completed frames")
    different = [n for n in a if a[n] != b[n]]
    result = {"scope": "completed GL frame pixels", "passed": not different,
              "frames": len(a), "different_frames": different}
    if details:
        import numpy as np
        from PIL import Image
        paths = [capture_paths(p) for p in (reference, candidate)]
        result['pixel_changes'] = []
        for frame in different:
            row = {'frame': frame, 'reference_size': a[frame]['size'],
                   'candidate_size': b[frame]['size']}
            if a[frame]['size'] == b[frame]['size']:
                arrays = []
                for files in paths:
                    with Image.open(files[frame]) as im:
                        arrays.append(np.asarray(im.convert('RGB')))
                mask = np.any(arrays[0] != arrays[1], axis=2)
                ys, xs = np.where(mask)
                row.update(changed_pixels=int(mask.sum()),
                    bounds_xyxy_exclusive=[int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1])
            else:
                row['size_mismatch'] = True
            result['pixel_changes'].append(row)
    return result


def capture_paths(directory):
    """Read paths only after read_completed_frames has validated the receipts."""
    directory = Path(directory)
    with (directory / 'captures.csv').open(newline='', encoding='utf-8') as stream:
        return {int(row['completed_frame']): directory / row['file'] for row in csv.DictReader(stream)}


def contact_sheet(reference, candidate, report, output):
    """Overview only: original captured pixels remain the comparison evidence."""
    from PIL import Image, ImageDraw, ImageOps
    paths = [capture_paths(p) for p in (reference, candidate)]
    changed = report.get('pixel_changes', [])
    if changed:
        peak = max(changed, key=lambda r: r.get('changed_pixels', 0))['frame']
        selected = sorted({changed[0]['frame'], peak, changed[-1]['frame']})
    else:
        selected = [next(iter(paths[0]))]
    cell_w, cell_h = 640, 420
    sheet = Image.new('RGB', (cell_w*2, cell_h*len(selected)), '#181818')
    draw = ImageDraw.Draw(sheet)
    for y, frame in enumerate(selected):
        for x, files in enumerate(paths):
            with Image.open(files[frame]) as image:
                preview = ImageOps.contain(image.convert('RGB'), (cell_w, cell_h-28))
                sheet.paste(preview, (x*cell_w+(cell_w-preview.width)//2, y*cell_h+28))
            draw.text((x*cell_w+8, y*cell_h+7),
                      f"{'Reference' if x == 0 else 'Candidate'} | completed frame {frame}", fill='white')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reference", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--frames", help="required inclusive FIRST:LAST capture interval")
    ap.add_argument("--every", type=int, default=1, help="capture spacing within --frames (default1)")
    ap.add_argument("--details", action='store_true', help="count changed pixels and locate their bounds")
    ap.add_argument("--contact-sheet", type=Path, help="save first/peak/last changed images side by side")
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args(argv)
    result = {"passed": False}
    try:
        if args.every < 1 or (args.every != 1 and not args.frames):
            raise ValueError('--every must be positive and requires --frames')
        expected = None
        if args.frames:
            first, last = map(int, args.frames.split(":"))
            if not 0 <= first <= last:
                raise ValueError("invalid frame interval")
            expected = range(first, last + 1, args.every)
        result = compare_completed_frames(args.reference, args.candidate, expected,
                                          args.details or bool(args.contact_sheet))
        if args.contact_sheet:
            contact_sheet(args.reference, args.candidate, result, args.contact_sheet)
            result['contact_sheet'] = str(args.contact_sheet.resolve())
    except (ValueError, OSError, KeyError) as exc:
        result['passed'] = False
        result["error"] = str(exc)
    write_json(args.report, result)
    print(("PASS" if result["passed"] else "FAIL") + f": {args.report}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
