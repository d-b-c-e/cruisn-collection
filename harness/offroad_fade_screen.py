"""Screen saved Off-Road scenes before spending a replay on distance fading.

This reconstructs geometry, not completed visibility. C31 depth words are not
integer distances or IEEE floats. A zero envelope count can rule out a useful
capture; a positive count still needs foreground/material/temporal evidence.
"""
import argparse
import json
import math
from pathlib import Path

from offroad_scene import scene
from scenery_c31 import F
from verification import sha256_file, write_json
from verify_offroad_future import Memory

FAR = 47296 * 3
WIDTH = 11824


def envelope_counts(objects):
    depths = []
    for obj in objects:
        if len(obj['quads']) != len(obj['depths']):
            raise ValueError('quad/depth cardinality')
        for words in obj['depths']:
            if len(words) != 4 or any(type(w) is not int or not 0 <= w < 2**32 for w in words):
                raise ValueError('four C31 depth words required')
            values = [F.load(w).value() for w in words]
            if any(not math.isfinite(z) or not 503 <= z < 63680*3 for z in values):
                raise ValueError('depth outside Off-Road projection contract')
            depths.append(values)
    return dict(quads=len(depths),
                fully_opaque=sum(max(z) <= FAR-WIDTH for z in depths),
                partial_envelope=sum(max(z) > FAR-WIDTH and min(z) < FAR for z in depths),
                fully_zero=sum(min(z) >= FAR for z in depths),
                minimum=min(map(min, depths)) if depths else None,
                maximum=max(map(max, depths)) if depths else None)


def screen(run, frame):
    run = Path(run)
    if type(frame) is not int or not 1 <= frame <= 20000:
        raise ValueError('bounded native frame required')
    paths = [run/'offroad-resource-rom.bin', run/f'offroad-resource-{frame}-ram.bin',
             run/f'offroad-resource-{frame}.json']
    if paths[0].stat().st_size != 0x1000000 or paths[1].stat().st_size != 0x80000 or paths[2].stat().st_size > 4096:
        raise ValueError('saved resource extent')
    metadata = json.loads(paths[2].read_text(encoding='utf-8'))
    if metadata.get('schema') != 1 or metadata.get('native_frame') != frame or metadata.get('frame') != frame:
        raise ValueError('saved scene identity')
    memory = Memory(paths[0].read_bytes(), paths[1].read_bytes())
    c2, o2 = scene(memory, 2, True, retain_depths=True)
    c3, o3 = scene(memory, 3, True, retain_depths=True)
    by_id = {o['id']: o for o in o3}
    if len(by_id) != len(o3) or [o for o in o3 if o['id'] in {x['id'] for x in o2}] != o2:
        raise ValueError('2x ordered geometry is not an exact 3x subset')
    ids2 = {o['id'] for o in o2}
    extra = [o for o in o3 if o['id'] not in ids2]
    all_counts = envelope_counts(o3)
    return dict(passed=True, frame=frame, far=FAR, width=WIDTH,
                sources={str(p): sha256_file(p) for p in paths},
                scene_2x=dict(c2), scene_3x=dict(c3), ordered_2x_subset_exact=True,
                all_3x=all_counts, additional_3x=envelope_counts(extra),
                envelope_present=bool(all_counts['partial_envelope'] or all_counts['fully_zero']),
                scope='Saved scalar geometry only. Positive envelope does not establish '
                      'on-screen coverage, current material ownership, completed visibility or fade benefit.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--frame', type=int, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('preserve the existing report')
    try:
        result = screen(args.run, args.frame)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = dict(passed=False, error=str(exc))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
