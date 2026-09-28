"""Check whether one wider completed capture exactly centers a narrower one.

This only checks saved BMP pixels. Replay reports must separately qualify input,
native motion, presentation, display ownership and shutdown.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(narrow_path, wide_path):
    with Image.open(narrow_path) as source, Image.open(wide_path) as target:
        if source.mode != 'RGB' or target.mode != 'RGB':
            raise ValueError('both completed BMPs must be RGB')
        narrow = source.copy()
        wide = target.copy()
    if wide.height != narrow.height or wide.width <= narrow.width:
        raise ValueError('wide capture must be wider at the same height')
    extra = wide.width - narrow.width
    if extra % 2:
        raise ValueError('side bars are not equal integer widths')
    offset = extra // 2
    center = wide.crop((offset, 0, offset+narrow.width, wide.height))
    left = wide.crop((0, 0, offset, wide.height))
    right = wide.crop((offset+narrow.width, 0, wide.width, wide.height))
    black = Image.new('RGB', (offset, wide.height))
    center_equal = ImageChops.difference(narrow, center).getbbox() is None
    left_black = ImageChops.difference(left, black).getbbox() is None
    right_black = ImageChops.difference(right, black).getbbox() is None
    return {'passed': center_equal and left_black and right_black,
            'narrow_size': list(narrow.size), 'wide_size': list(wide.size),
            'side_bar_width': offset, 'center_exact': center_equal,
            'left_bar_black': left_black, 'right_bar_black': right_black,
            'sha256': {'narrow_bmp': sha(narrow_path), 'wide_bmp': sha(wide_path)},
            'scope': 'Saved completed RGB pixels only; not a replay, GPU, physical-display or other-frame qualification.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--narrow', required=True, type=Path)
    ap.add_argument('--wide', required=True, type=Path)
    ap.add_argument('--report', required=True, type=Path)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite capture evidence')
    result = inspect(args.narrow, args.wide)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    if not result['passed']:
        raise ValueError('wide capture is not an exact centered copy with black bars')
    print('PASS exact centered capture,', result['side_bar_width'], 'black pixels per side')


if __name__ == '__main__':
    main()
