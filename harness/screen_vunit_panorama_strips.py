"""Find structurally repeated original V-Unit backdrop-strip candidates.

This is a conservative saved-DMA screen for V-Unit margin safety experiments,
not a renderer classifier. Matching a strip does not prove its material is
background or that overwriting it is safe in another frame/course.
"""
import argparse
import hashlib
import json
from pathlib import Path

from vunit_display_scene import load


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def signed(value):
    value = int(value)
    return value - 65536 if value >= 32768 else value


def candidate(ordinal, quad):
    q = [int(v) for v in quad]
    x = [signed(q[i]) for i in (2, 4, 6, 8)]
    y = [signed(q[i]) for i in (3, 5, 7, 9)]
    left, right, top, bottom = min(x), max(x), min(y), max(y)
    corners = {(left, top), (right, top), (left, bottom), (right, bottom)}
    if (q[0] != 0x100 or len(corners) != 4 or
            set(zip(x, y)) != corners or
            not all(x[i] == x[(i + 1) % 4] or y[i] == y[(i + 1) % 4]
                    for i in range(4)) or
            not 200 <= right - left <= 300 or
            not 100 <= bottom - top <= 280 or top > 240 or bottom > 400):
        return None
    return dict(ordinal=ordinal, left=left, right=right, top=top, bottom=bottom,
                pixdata=q[1], texture_base=q[14], texture_low_byte=q[14] & 255)


def strips(quads):
    found = []
    group = []

    def finish():
        if len(group) < 3 or group[-1]['right'] - group[0]['left'] < 512:
            return
        found.append(dict(ordinals=[item['ordinal'] for item in group],
                          extent=[group[0]['left'], group[0]['top'],
                                  group[-1]['right'], group[0]['bottom']],
                          pixdata=group[0]['pixdata'],
                          texture_low_byte=group[0]['texture_low_byte'],
                          texture_bases=[item['texture_base'] for item in group]))

    for ordinal, quad in enumerate(quads):
        item = candidate(ordinal, quad)
        adjacent = (item is not None and group and
                    all(item[key] == group[-1][key] for key in
                        ('top', 'bottom', 'pixdata', 'texture_low_byte')) and
                    abs(item['left'] - group[-1]['right']) <= 2)
        if group and not adjacent:
            finish()
            group = []
        if item is not None:
            group.append(item)
    if group:
        finish()
    return found


def screen(runs):
    result = []
    for run in runs:
        run = Path(run)
        scene = load(run)
        raw = run.parent / 'report.json'
        report = json.loads(raw.read_text(encoding='utf-8')) if raw.is_file() else None
        result.append(dict(run=str(run.resolve()),
                           completed_frame=scene.report['completed_frame'],
                           original_dma_quads=len(scene.current),
                           strips=strips(scene.current),
                           raw_replay_passed=report.get('passed') if report else None,
                           raw_replay_error=report.get('error') if report else None,
                           sha256={'original_dma': sha(run / 'capture/quads.bin'),
                                   'mirror_receipt': sha(run / 'vunit-mirror.json'),
                                   'raw_report': sha(raw)
                                   if report else None}))
    return dict(schema=1, analysis_completed=True,
                scope='Selected saved original DMA only. Axis-aligned consecutive '
                '3+-tile panorama candidates; no texture pixels, depth, host '
                'compositing, completed CRT image or cross-course safety proof.',
                runs=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, action='append', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite panorama-strip screen')
    result = screen(args.run)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('SCREEN', len(result['runs']), 'scenes',
          sum(len(item['strips']) for item in result['runs']), 'candidate strips')


if __name__ == '__main__':
    main()
