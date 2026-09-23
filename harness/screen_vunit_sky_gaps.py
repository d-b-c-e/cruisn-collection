"""Find possible sky openings bracketed by auxiliary scenery and original ground.

Uses verified V-Unit indexed mirrors and same-run original DMA. This is a
triage screen, not an image fix or evidence that every candidate is defective.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from vunit_display_scene import load as load_original_scene
from vunit_original_mirror import verify as verify_mirror


SKY_TEXBASE = {'offroadc': 0x7f, 'crusnusa': 0x56,
               'crusnwld': 0xc5, 'crusnwld24': 0xc5}


def candidates(sky, tags, left, right, max_gap):
    if (sky.shape != tags.shape or sky.ndim != 2 or
            not 0 <= left <= right <= sky.shape[1] or max_gap < 1):
        raise ValueError('invalid gap-screen geometry')
    height, width = sky.shape
    result = np.zeros((height, width), dtype=bool)
    auxiliary = (tags & 4) != 0
    for x in list(range(left)) + list(range(right, width)):
        edges = np.flatnonzero(np.diff(np.r_[False, sky[:, x], False].astype('i1')))
        for low, high in edges.reshape(-1, 2):
            if (low < 1 or high >= height or high - low > max_gap or
                    not auxiliary[high, x] or tags[low - 1, x] != 1 or sky[low - 1, x]):
                continue
            result[low:high, x] = True
    return result


def ordinary_extensions(sky, tags, left, right, max_gap):
    """Sky between two ordinary materials; meaningful only beside a host gap."""
    if (sky.shape != tags.shape or sky.ndim != 2 or
            not 0 <= left <= right <= sky.shape[1] or max_gap < 1):
        raise ValueError('invalid gap-screen geometry')
    height, width = sky.shape
    result = np.zeros((height, width), dtype=bool)
    for x in list(range(left)) + list(range(right, width)):
        edges = np.flatnonzero(np.diff(np.r_[False, sky[:, x], False].astype('i1')))
        for low, high in edges.reshape(-1, 2):
            if (low < 1 or high >= height or high - low > max_gap or
                    tags[low - 1, x] != 1 or sky[low - 1, x] or
                    tags[high, x] != 1 or sky[high, x]):
                continue
            result[low:high, x] = True
    return result


def connected_envelopes(host_gap, ordinary):
    if host_gap.shape != ordinary.shape or host_gap.ndim != 2:
        raise ValueError('invalid connected gap masks')
    remaining = set(zip(*np.where(host_gap | ordinary)))
    output = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        xmin = xmax = start[1]
        ymin = ymax = start[0]
        host_pixels = other_pixels = 0
        while stack:
            y, x = stack.pop()
            xmin, xmax = min(xmin, x), max(xmax, x)
            ymin, ymax = min(ymin, y), max(ymax, y)
            if host_gap[y, x]:
                host_pixels += 1
            else:
                other_pixels += 1
            for point in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        if host_pixels:
            output.append(dict(pixels=host_pixels + other_pixels,
                               host_bounded_pixels=host_pixels,
                               adjoining_ordinary_pixels=other_pixels,
                               box=list(map(int, (xmin, ymin, xmax, ymax)))))
    output.sort(key=lambda item: (-item['pixels'], item['box']))
    return output


def components(mask):
    remaining = set(zip(*np.where(mask)))
    output = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        ymin = ymax = start[0]
        xmin = xmax = start[1]
        count = 0
        while stack:
            y, x = stack.pop()
            count += 1
            ymin, ymax = min(ymin, y), max(ymax, y)
            xmin, xmax = min(xmin, x), max(xmax, x)
            for pair in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if pair in remaining:
                    remaining.remove(pair)
                    stack.append(pair)
        output.append(dict(pixels=count, box=list(map(int, (xmin, ymin, xmax, ymax)))))
    output.sort(key=lambda item: (-item['pixels'], item['box']))
    return output


def screen(case, max_gap_coarse=16):
    case = Path(case)
    if not 1 <= max_gap_coarse <= 32:
        raise ValueError('gap span must be 1..32 coarse pixels')
    report_path = case / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('passed') is not True:
        raise ValueError('gap screen requires a passing replay')
    rom = json.loads((Path(report['case']) / 'case.json').read_text(encoding='utf-8'))['rom']
    if rom not in SKY_TEXBASE:
        raise ValueError('gap screen requires a supported V-Unit ROM')
    run = case / 'run'
    mirror = verify_mirror(report['vunit_original_mirror'], run)
    journal = run / 'capture/quads.bin'
    if hashlib.sha256(journal.read_bytes()).hexdigest() != report['capture']['sha256']['quads.bin']:
        raise ValueError('original DMA journal differs from replay receipt')
    scene = load_original_scene(run)
    if scene.report['visible_page'] != mirror['visible_page']:
        raise ValueError('original DMA and indexed page differ')
    invocation = run / 'invocation.json'
    env = json.loads(invocation.read_text(encoding='utf-8'))['environment']
    scale, margin, native_height = (int(env[key]) for key in
        ('MIDV_GL_SCALE', 'MIDV_GL_MARGIN', 'MIDV_GL_HEIGHT'))
    if (not 1 <= scale <= 6 or not 0 < margin <= 256 or
            native_height not in (400, 401) or
            mirror['width'] != (512 + 2 * margin) * scale or
            mirror['height'] != native_height * scale):
        raise ValueError('unqualified indexed page geometry')
    sky_palettes = set()
    for quad in scene.current:
        words = [int(value) for value in quad]
        xs = [words[i] - 65536 if words[i] >= 32768 else words[i]
              for i in (2, 4, 6, 8)]
        if ((words[0] & 0x300) == 0x100 and
                (words[14] & 255) == SKY_TEXBASE[rom] and max(xs) - min(xs) > 200):
            sky_palettes.add(words[1])
    if not sky_palettes:
        raise ValueError('no qualified current backdrop command')
    width, height, page = (mirror[key] for key in ('width', 'height', 'visible_page'))
    prefix = f'vunit-mirror-{mirror["frame"]}-page{page}-plane'
    index_path, mask_path = (run / (prefix + str(n) + '.bin') for n in (0, 1))
    index = np.fromfile(index_path, dtype='<u2').reshape(height, width)
    tags = np.fromfile(mask_path, dtype='u1').reshape(height, width)
    sky = np.zeros((height, width), dtype=bool)
    for palette in sky_palettes:
        sky |= (index >= palette) & (index < palette + 256)
    sky &= tags == 1
    margin_fine = margin * scale
    found = candidates(sky, tags, margin_fine, width - margin_fine,
                       max_gap_coarse * scale)
    regions = components(found)
    adjacent = ordinary_extensions(sky, tags, margin_fine, width - margin_fine,
                                   max_gap_coarse * scale)
    envelopes = connected_envelopes(found, adjacent)
    return dict(case=str(case.resolve()), rom=rom, completed_frame=mirror['frame'],
                visible_page=page, width=width, height=height,
                sky_palettes=sorted(sky_palettes), max_gap_coarse=max_gap_coarse,
                total_pixels=int(found.sum()), components=len(regions),
                largest=regions[:20],
                connected_envelopes=envelopes[:20],
                connected_envelope_pixels=sum(item['pixels'] for item in envelopes),
                source_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in (report_path, invocation, index_path, mask_path,
                                            journal)},
                scope='Possible sky intervals in 16:9 margins with auxiliary above and '
                      'non-sky original below, plus only ordinary sky intervals connected '
                      'to them; saved-frame screen only. No visual repair or '
                      'cross-game acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases', nargs='+', type=Path)
    parser.add_argument('--max-gap-coarse', type=int, default=16)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite gap-screen evidence')
    result = dict(schema=1, passed=True,
                  cases=[screen(case, args.max_gap_coarse) for case in args.cases])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    for item in result['cases']:
        print(item['rom'], item['completed_frame'], item['total_pixels'],
              item['components'], item['largest'][:2])


if __name__ == '__main__':
    main()
