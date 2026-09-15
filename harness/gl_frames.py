"""Compare completed GL frames; asynchronous legacy captures are not frame oracles."""
import argparse
import csv
import json
from pathlib import Path
import sys

from verification import image_signature, write_json


class IncompleteCaptureError(ValueError):
    def __init__(self, directory, rows, expected, actual):
        wanted, seen = set(expected), set(actual)
        self.capture_diagnostics = {
            'directory': str(Path(directory).resolve()),
            'expected_count': len(expected), 'captured_count': len(actual),
            'first_captured': actual[0] if actual else None,
            'last_captured': actual[-1] if actual else None,
            'missing_frames': sorted(wanted-seen), 'unexpected_frames': sorted(seen-wanted),
            'maximum_queued_bytes': max(int(r.get('queued_bytes', 0)) for r in rows),
            'dimensions': sorted({(int(r['width']), int(r['height'])) for r in rows}),
        }
        super().__init__(f'completed GL capture interval is incomplete or unexpected: '
                         f'{len(actual)}/{len(expected)} images; '
                         f'{len(wanted-seen)} missing, {len(seen-wanted)} unexpected')


def requested_frames(first, last, every, budget=None, *, stop_frame=None):
    """Native global-frame cadence; reject impossible requests before launch."""
    if not 0 <= first <= last or every < 1:
        raise ValueError('invalid GL capture interval or cadence')
    frames = range(first+(-first % every), last+1, every)
    if not frames:
        raise ValueError('no capture frames align with the requested interval and cadence')
    if budget is not None and len(frames) > budget:
        raise ValueError(f'GL capture budget {budget} cannot cover {len(frames)} requested images')
    if stop_frame is not None and frames[-1] >= stop_frame:
        raise ValueError('completed GL captures must precede the replay stop frame; '
                         'end capture earlier or extend the replay')
    return frames


def recorded_capture_request(run):
    """Recover explicit capture cadence from the actual isolated invocation.

    Archived absolute SNAP paths are never followed. Images remain under the
    supplied run/gl-snap. Dimensions come from validated completion receipts,
    not assumptions about monitor size or the renderer's window decoration.
    """
    invocation = json.loads((Path(run) / 'invocation.json').read_text(encoding='utf-8'))
    env = invocation.get('environment')
    if not isinstance(env, dict):
        raise ValueError('capture invocation requires an environment')
    enabled = [p for p in ('MIDV', 'MIDZ') if env.get(p+'_GL') == '1' and env.get(p+'_GL_SNAP')]
    if len(enabled) != 1:
        raise ValueError('capture invocation requires one active capture renderer')
    prefix = enabled[0]
    values = [env.get(prefix+'_GL_'+k) for k in ('SNAP_FIRST', 'SNAP_LAST', 'SNAP_EVERY', 'SNAP_MAX')]
    values.append(env.get('SNAP_STOP'))
    if any(not isinstance(v, str) or not v.isascii() or not v.isdecimal() for v in values):
        raise ValueError('capture invocation requires explicit numeric bounds, cadence, budget and stop')
    first, last, every, budget, stop = map(int, values)
    frames = requested_frames(first, last, every, budget, stop_frame=stop)
    return dict(renderer=prefix, first=first, last=last, every=every, budget=budget,
                stop_frame=stop, expected_frames=list(frames))


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
    if expected is not None:
        expected = list(expected)
        if list(frames) != expected:
            raise IncompleteCaptureError(directory, rows, expected, list(frames))
    return frames


def compare_completed_frames(reference, candidate, expected=None, details=False):
    if expected is not None:
        expected = tuple(expected)
    a, b = read_completed_frames(reference, expected), read_completed_frames(candidate, expected)
    if a.keys() != b.keys():
        raise ValueError("GL recordings cover different completed frames")
    different = [n for n in a if a[n] != b[n]]
    result = {"scope": "completed GL frame pixels", "passed": not different,
              "frames": len(a), "different_frames": different,
              "reference": str(Path(reference).resolve()), "candidate": str(Path(candidate).resolve())}
    result['size_mismatches']=[{'frame':n,'reference':a[n]['size'],'candidate':b[n]['size']}
                              for n in different if a[n]['size']!=b[n]['size']]
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
    ap.add_argument("--run-directories", action='store_true',
                    help="compare RUN/gl-snap using each RUN/invocation.json capture request")
    ap.add_argument("--every", type=int, default=1, help="capture global frame multiples of N within --frames (default1)")
    ap.add_argument("--details", action='store_true', help="count changed pixels and locate their bounds")
    ap.add_argument("--contact-sheet", type=Path, help="save first/peak/last changed images side by side")
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args(argv)
    result = {"passed": False}
    try:
        if args.every < 1 or (args.every != 1 and not args.frames):
            raise ValueError('--every must be positive and requires --frames')
        expected = None
        requests = None
        if args.run_directories:
            if args.frames or args.every != 1:
                raise ValueError('--run-directories reads cadence from invocations; do not override it')
            requests = [recorded_capture_request(p) for p in (args.reference, args.candidate)]
            if requests[0]['expected_frames'] != requests[1]['expected_frames']:
                raise ValueError('run invocations request different completed frames')
            expected = requests[0]['expected_frames']
            args.reference /= 'gl-snap'
            args.candidate /= 'gl-snap'
        elif args.frames:
            first, last = map(int, args.frames.split(":"))
            expected = requested_frames(first, last, args.every)
        result = compare_completed_frames(args.reference, args.candidate, expected,
                                          args.details or bool(args.contact_sheet))
        if requests is not None:
            result['capture_requests'] = requests
        if args.contact_sheet:
            contact_sheet(args.reference, args.candidate, result, args.contact_sheet)
            result['contact_sheet'] = str(args.contact_sheet.resolve())
    except (ValueError, OSError, KeyError) as exc:
        result['passed'] = False
        result["error"] = str(exc)
        if isinstance(exc, IncompleteCaptureError):
            result['capture_diagnostics'] = exc.capture_diagnostics
    write_json(args.report, result)
    print(("PASS" if result["passed"] else "FAIL") + f": {args.report}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
