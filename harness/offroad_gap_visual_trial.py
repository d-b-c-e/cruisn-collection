"""Offline, non-product Off-Road left-gap pixel-fill comparison.

Replays the saved indexed page through the current palette shader. This is a
single-frame visual experiment, not an accepted geometry or shader fix.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import moderngl
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'gpu'))
sys.path.insert(0, str(ROOT / 'harness'))
import renderer as R
from screen_vunit_sky_gaps import candidates

HERE = ROOT / 'results/diagnostics/offroad-full-20260910'
RUN = HERE / 'left-gap-original-run/run'
RES = HERE / 'left-gap-resource-run/run'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
OUT = args.output
OUT.mkdir(parents=True, exist_ok=False)
WIDTH, HEIGHT = 2736, 1600
OUT_W, OUT_H = 2544, 1353
PREFIX = 'vunit-mirror-3120-page1-plane'
INDEX_PATH = RUN / (PREFIX + '0.bin')
MASK_PATH = RUN / (PREFIX + '1.bin')
PALETTE_PATH = RES / 'offroad-resource-3116-palettes.bin'
REFERENCE_PATH = RUN / 'gl-snap/mvgl_000.bmp'

index = np.fromfile(INDEX_PATH, dtype='<u2').reshape(HEIGHT, WIDTH)
tags = np.fromfile(MASK_PATH, dtype='u1').reshape(HEIGHT, WIDTH)
sky = (index >= 6912) & (index < 7168) & (tags == 1)
gap = candidates(sky, tags, 344, WIDTH - 344, 64)
assert int(gap.sum()) == 5841
columns = {}
for x in range(WIDTH):
    yy = np.flatnonzero(gap[:, x])
    if len(yy):
        assert np.array_equal(yy, np.arange(yy[0], yy[-1] + 1))
        columns[x] = (int(yy[0]), int(yy[-1] + 1))

ctx = moderngl.create_context(standalone=True, require=430)
program = ctx.program(vertex_shader=R.PAL_VS, fragment_shader=R.PAL_FS)
for name, value in dict(idxTex=1, palTex=2, maskTex=3,
                        uCrop=0, uCrt=1, uSrcH=400., uFillR=16,
                        uMargin=0, uHostLayers=1).items():
    program[name].value = value
palette = ctx.texture((256, 128), 1, PALETTE_PATH.read_bytes(), dtype='u4')
color = ctx.texture((OUT_W, OUT_H), 4, dtype='f1')
target = ctx.framebuffer([color])
vao = ctx.vertex_array(program, [])
palette.use(2)


def resolve(idx, mask):
    tex_index = ctx.texture((WIDTH, HEIGHT), 1, idx.tobytes(), dtype='u2')
    tex_mask = ctx.texture((WIDTH, HEIGHT), 1, mask.tobytes(), dtype='u1')
    tex_index.use(1)
    tex_mask.use(3)
    target.use()
    target.clear(0, 0, 0, 1)
    ctx.viewport = (67, 0, 2410, 1353)
    vao.render(moderngl.TRIANGLES, vertices=3)
    output = np.flipud(np.frombuffer(color.read(alignment=1), np.uint8)
                       .reshape(OUT_H, OUT_W, 4))[:, :, :3].copy()
    tex_index.release()
    tex_mask.release()
    return output


original = resolve(index, tags)
reference = np.asarray(Image.open(REFERENCE_PATH).convert('RGB'))
baseline_delta = np.max(np.abs(original.astype('i2') - reference.astype('i2')), axis=2)
if int((baseline_delta > 1).sum()) > OUT_W * OUT_H // 10000:
    raise ValueError('offline baseline differs too much from completed capture')
Image.fromarray(original).save(OUT / 'offline-baseline.png')

variants = {'baseline': original}
stats = {}
for method in ('nearest-edge', 'mirror-texture', 'ground-only', 'host-only'):
    changed_index = index.copy()
    changed_mask = tags.copy()
    for x, (lo, hi) in columns.items():
        for y in range(lo, hi):
            if method == 'ground-only':
                source_y = lo - 1
            elif method == 'host-only':
                source_y = hi
            else:
                use_ground = y - lo < hi - 1 - y
                if method == 'nearest-edge':
                    source_y = lo - 1 if use_ground else hi
                else:
                    source_y = lo - 1 - (y - lo) if use_ground else hi + (hi - 1 - y)
            changed_index[y, x] = index[source_y, x]
            changed_mask[y, x] = tags[source_y, x]
    image = resolve(changed_index, changed_mask)
    variants[method] = image
    diff = np.any(image != original, axis=2)
    stats[method] = {'changed_completed_pixels': int(diff.sum()),
                     'box': [int(np.where(diff)[1].min()), int(np.where(diff)[0].min()),
                             int(np.where(diff)[1].max()), int(np.where(diff)[0].max())]}
    Image.fromarray(image).save(OUT / (method + '.png'))

crop = (40, 450, 520, 1200)
names = list(variants)
canvas = Image.new('RGB', (480 * len(names), 780), 'black')
draw = ImageDraw.Draw(canvas)
for i, name in enumerate(names):
    canvas.paste(Image.fromarray(variants[name]).crop(crop), (i * 480, 30))
    draw.text((i * 480 + 8, 7), name, fill='white')
canvas.save(OUT / 'comparison-crop.png')

report = {'scope': 'offline single-frame pixel-fill comparison; no native/render fix',
          'frame': 3120, 'gap_indexed_pixels': int(gap.sum()),
          'gap_indexed_box': [0, 941, 163, 982],
          'baseline_completed_pixel_differences': int((baseline_delta > 0).sum()),
          'baseline_completed_pixel_differences_over_1': int((baseline_delta > 1).sum()),
          'max_baseline_channel_difference': int(baseline_delta.max()),
          'palette_shader_sha256': hashlib.sha256(R.PAL_FS.encode('utf-8')).hexdigest(),
          'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (INDEX_PATH, MASK_PATH, PALETTE_PATH, REFERENCE_PATH)},
          'variants': stats}
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
