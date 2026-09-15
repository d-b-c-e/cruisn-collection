"""Screen saved Exotica samples before spending a replay on distance changes.

Serialized distance bands establish geometry presence, not completed visibility.
Earlier admission can affect later original replacements even when the current
future/waiting sample has no third band; this tool does not assess that history.
"""
import argparse
import json
from pathlib import Path
import struct


def bands(raw):
    if len(raw) % 44 or len(raw) > 32768 * 44:
        raise ValueError('invalid instance stream size')
    result = {str(i): dict(instances=0, quads=0) for i in (1, 2, 3)}
    end = 0
    identities = set()
    for row in struct.iter_unpack('<11I', raw):
        entry, source, band, first, count = row[0], row[1], row[5], row[9], row[10]
        if (not entry or not source or (entry, source) in identities or band not in (1, 2, 3)
                or first != end or count > 131072 or first + count > 131072):
            raise ValueError('invalid instance identity, band or quad order')
        identities.add((entry, source))
        result[str(band)]['instances'] += 1
        result[str(band)]['quads'] += count
        end += count
    return result


def sample(run, frame):
    if not 1800 <= frame <= 16000:
        raise ValueError('sample frame out of range')
    stages = {}
    for kind in ('host', 'handover'):
        prefix = Path(run) / f'exotica-{kind}-{frame}'
        raw = Path(str(prefix) + '-instances.bin').read_bytes()
        counts = bands(raw)
        quad_bytes = Path(str(prefix) + '-quads.bin').stat().st_size
        if quad_bytes != sum(v['quads'] for v in counts.values()) * 260:
            raise ValueError('instance and quad counts differ')
        stages[kind] = counts
    third = sum(v['3']['quads'] for v in stages.values())
    return dict(frame=frame, stages=stages, third_band_quads=third,
                sample_contains_third_band=third > 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--frames', type=int, nargs='+', required=True)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--require-third-band', action='store_true',
                        help='fail selection when no sampled future/waiting polygon occupies band3')
    args = parser.parse_args()
    if not 1 <= len(args.frames) <= 32 or len(set(args.frames)) != len(args.frames):
        parser.error('choose 1..32 distinct snapshot frames')
    samples = [sample(args.run, frame) for frame in args.frames]
    present = any(s['sample_contains_third_band'] for s in samples)
    report = dict(schema=1, run=str(args.run), samples=samples,
                  selection_passed=present or not args.require_third_band,
                  scope='Saved future/waiting geometry only. Presence is not completed visibility; absence does not exclude an earlier admission effect on later original replacements.')
    text = json.dumps(report, indent=2) + '\n'
    if args.report:
        args.report.write_text(text, encoding='utf-8')
    print(text, end='')
    return 0 if report['selection_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
