"""Screen one loaded Off-Road ground strip against the saved El Paso gap.

This is an offline source/raster experiment, not a live renderer policy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import moderngl
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'gpu'))
import renderer as R

from analyze_vunit_margin_gap import PACKET, analyze, projected_box
from offroad_scene import scene
from offroad_sections import sections
from screen_vunit_sky_gaps import candidates
from verify_offroad_future import Memory, allocated_pool
from vunit_display_scene import load as load_original

HERE = ROOT / 'results/diagnostics/offroad-full-20260910'
MATCHED = HERE / 'left-gap-matched-run'
ORIGINAL = HERE / 'left-gap-original-run'
RESOURCE = HERE / 'left-gap-resource-run'
LOADED_SOURCE = 0xec320e
NEAR_SOURCE = 0xec31ed
HOST_SOURCE = 0xec4080


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allocated_match(descriptor, allocation):
    owners = allocation.get(descriptor['words'][6], [])
    return len(owners) == 1 and owners[0][5] & 0x7fffffff == descriptor['words'][5] and all(
        owners[0][i] == descriptor['words'][i] for i in (*range(6, 9), *range(11, 21)))


def render_quads(quads, texture_bytes):
    ctx = moderngl.create_context(standalone=True, require=430)
    program = ctx.program(vertex_shader=R.VS, fragment_shader=R.FS)
    for key, value in dict(uCanvas=(684., 400.), uScale=4, uClipRight=683,
                           texram=0, texMask=len(texture_bytes)-1, uDbgQuadId=0,
                           uBgMargin=0, uClipW=684).items():
        program[key].value = value
    texture = ctx.texture((4096, len(texture_bytes)//4096), 1, texture_bytes, dtype='u1')
    texture.use(0)
    floats, words = R.build_vertices(np.asarray(quads, dtype='<u2'), 86, dilate2d=True)
    words[:, 2] |= 8
    float_buffer, word_buffer = ctx.buffer(floats.tobytes()), ctx.buffer(words.tobytes())
    vao = ctx.vertex_array(program, [
        (float_buffer, '2f 2f 2f 2f 2f 4f 4f 4f', 'in_corner', 'in_v0', 'in_v1',
         'in_v2', 'in_v3', 'in_uv01', 'in_uv23', 'in_uvBounds'),
        (word_buffer, '4u', 'in_meta')])
    index = ctx.texture((2736, 1600), 1, dtype='u2')
    mask = ctx.texture((2736, 1600), 1, dtype='u1')
    target = ctx.framebuffer([index, mask])
    target.use()
    target.clear()
    ctx.viewport = (0, 0, 2736, 1600)
    vao.render(moderngl.TRIANGLES)
    # The saved indexed mirror and GL readback are both bottom-up. The usual
    # presentation flip would compare the wrong rows here.
    result = (np.frombuffer(index.read(alignment=1), '<u2').reshape(1600, 2736).copy(),
              np.frombuffer(mask.read(alignment=1), 'u1').reshape(1600, 2736).copy())
    for resource in (target, index, mask, vao, float_buffer, word_buffer, texture, program):
        resource.release()
    ctx.release()
    return result


def resolve(index, tags, palette_bytes):
    ctx = moderngl.create_context(standalone=True, require=430)
    program = ctx.program(vertex_shader=R.PAL_VS, fragment_shader=R.PAL_FS)
    for key, value in dict(idxTex=1, palTex=2, maskTex=3, uCrop=0, uCrt=1,
                           uSrcH=400., uFillR=16, uMargin=0, uHostLayers=1).items():
        program[key].value = value
    indices = ctx.texture((2736, 1600), 1, index.tobytes(), dtype='u2')
    masks = ctx.texture((2736, 1600), 1, tags.tobytes(), dtype='u1')
    palette = ctx.texture((256, 128), 1, palette_bytes, dtype='u4')
    indices.use(1)
    palette.use(2)
    masks.use(3)
    color = ctx.texture((2544, 1353), 4, dtype='f1')
    target = ctx.framebuffer([color])
    target.use()
    target.clear(0, 0, 0, 1)
    ctx.viewport = (67, 0, 2410, 1353)
    vao = ctx.vertex_array(program, [])
    vao.render(moderngl.TRIANGLES, vertices=3)
    result = np.flipud(np.frombuffer(color.read(alignment=1), np.uint8)
                       .reshape(1353, 2544, 4))[:, :, :3].copy()
    for resource in (vao, target, color, palette, indices, masks, program):
        resource.release()
    ctx.release()
    return result


def screen(preview_dir=None):
    source = analyze(MATCHED, [(60, 940), (60, 960), (60, 990)],
                     (60, 956, 60, 964), ORIGINAL)
    resource_report = json.loads((RESOURCE / 'report.json').read_text(encoding='utf-8'))
    if resource_report.get('passed') is not True or resource_report['case'] != json.loads(
            (MATCHED / 'report.json').read_text(encoding='utf-8'))['case']:
        raise ValueError('resource case is not the passing matched replay')
    a = json.loads((RESOURCE / 'run/invocation.json').read_text(encoding='utf-8'))
    b = json.loads((MATCHED / 'run/invocation.json').read_text(encoding='utf-8'))
    if a['executable_sha256'] != b['executable_sha256']:
        raise ValueError('resource and source executable differ')
    run = RESOURCE / 'run'
    ram = run / 'offroad-resource-3116-ram.bin'
    rom = run / 'offroad-resource-rom.bin'
    texture = run / 'offroad-resource-3116-textures.bin'
    memory = Memory(rom.read_bytes(), ram.read_bytes())
    _, future = scene(memory, 3, True)
    flat = [quad for item in future for quad in item['quads']]
    packets = list(PACKET.iter_unpack((MATCHED / 'run/vunit-fade-producer.bin').read_bytes()[4:]))
    if len(flat) != len(packets) or any(quad != list(packet[3:19])
                                            for quad, packet in zip(flat, packets)):
        raise ValueError('ordinary future scene differs from all producer packets')
    _, loaded = scene(memory, 1, True, loaded_sections=True, retain_depths=True)
    original = load_original(ORIGINAL / 'run').current
    near = list(map(int, original[66]))
    near_matches = [(item, quad) for item in loaded for quad in item['quads'] if quad == near]
    if len(near_matches) != 1 or near_matches[0][0]['id'] != (0x80000000 | NEAR_SOURCE):
        raise ValueError('original adjacent ground has no unique loaded source match')
    target = next(item for item in loaded if item['id'] == (0x80000000 | LOADED_SOURCE))
    if len(target['quads']) != 1:
        raise ValueError('unexpected loaded source geometry')
    candidate = target['quads'][0]
    edge = [tuple(candidate[6:8]), tuple(candidate[8:10])]
    expected = [tuple(near[4:6]), tuple(near[2:4])]
    if (edge != expected or any(np.array_equal(candidate, q) for q in original)
            or candidate in flat):
        raise ValueError('ground adjacency or absence changed')
    descriptor = next(item for item in sections(memory, loaded=True)['sources']
                      if item['source'] == LOADED_SOURCE)
    allocation = allocated_pool(memory)
    if not allocated_match(descriptor, allocation):
        raise ValueError('loaded descriptor does not match the unique allocated object')
    texture_bytes = texture.read_bytes()
    added, tag = render_quads([candidate], texture_bytes)
    original_keys = {tuple(map(int, quad)) for quad in original}
    host_keys = {tuple(quad) for quad in flat}
    loaded_quads = [quad for item in loaded if item['id'] & 0x80000000
                    for quad in item['quads']]
    unsubmitted = [quad for quad in loaded_quads if tuple(quad) not in original_keys
                   and tuple(quad) not in host_keys]
    margin_items = [(item, quad) for item in loaded if item['id'] & 0x80000000
                    for quad in item['quads'] if tuple(quad) not in original_keys
                    and tuple(quad) not in host_keys and projected_box(quad)[0] < 0
                    and projected_box(quad)[2] >= -86]
    margin = [quad for _, quad in margin_items]
    if candidate not in margin:
        raise ValueError('target ground quad is absent from the missing left-margin set')
    all_added, all_tag = render_quads(margin, texture_bytes)
    descriptors = {item['source']: item for item in sections(memory, loaded=True)['sources']}
    eligible = [quad for item, quad in margin_items
                if allocated_match(descriptors[item['id'] & 0x7fffffff], allocation)]
    _, eligible_tag = render_quads(eligible, texture_bytes)
    old = np.fromfile(ORIGINAL / 'run/vunit-mirror-3120-page1-plane0.bin',
                      dtype='<u2').reshape(1600, 2736)
    old_tag = np.fromfile(ORIGINAL / 'run/vunit-mirror-3120-page1-plane1.bin',
                          dtype='u1').reshape(1600, 2736)
    sky = (old >= 6912) & (old < 7168) & (old_tag == 1)
    gap = candidates(sky, old_tag, 344, 2736-344, 64)
    covered = tag != 0
    all_covered = all_tag != 0
    yy, xx = np.where(covered)
    preview = None
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=False)
        palette_path = run / 'offroad-resource-3116-palettes.bin'
        baseline = resolve(old, old_tag, palette_path.read_bytes())
        variants = {}
        for name, index, mask in (('single', added, tag), ('all-left', all_added, all_tag)):
            replacement = (mask != 0) & sky
            proposed_index, proposed_tag = old.copy(), old_tag.copy()
            proposed_index[replacement] = index[replacement]
            proposed_tag[replacement] = mask[replacement]
            variants[name] = (resolve(proposed_index, proposed_tag, palette_path.read_bytes()),
                              int(replacement.sum()))
        reference = np.asarray(Image.open(ORIGINAL / 'run/gl-snap/mvgl_000.bmp').convert('RGB'))
        delta = np.max(np.abs(baseline.astype('i2') - reference.astype('i2')), axis=2)
        if int((delta > 1).sum()) > baseline.shape[0] * baseline.shape[1] // 10000:
            raise ValueError('saved palette resolve exceeds previous baseline tolerance')
        Image.fromarray(baseline).save(preview_dir / 'baseline.png')
        for name, (rgb, _) in variants.items():
            Image.fromarray(rgb).save(preview_dir / (name + '-sky-only.png'))
        crop = (40, 450, 520, 1200)
        contact = Image.new('RGB', (1440, 780), 'black')
        draw = ImageDraw.Draw(contact)
        for i, (name, rgb) in enumerate((('baseline', baseline),
                                         ('single', variants['single'][0]),
                                         ('all-left', variants['all-left'][0]))):
            contact.paste(Image.fromarray(rgb).crop(crop), (i * 480, 30))
            draw.text((i * 480 + 8, 7), name, fill='white')
        contact.save(preview_dir / 'comparison-crop.png')
        preview = dict(replaced_indexed_sky_pixels={name: count for name, (_, count) in variants.items()},
                       changed_completed_pixels={name: int(np.count_nonzero(np.any(rgb != baseline, axis=2)))
                                                 for name, (rgb, _) in variants.items()},
                       baseline_completed_differences_over_one=int((delta > 1).sum()),
                       max_baseline_channel_difference=int(delta.max()),
                       palette_sha256=sha(palette_path),
                       scope='Sky-only offline compositing, not native draw order or exact completed acceptance')
    return dict(source_frame=source['source_frame'], completed_frame=source['completed_frame'],
                original_ground_command=66, original_ground_source=hex(NEAR_SOURCE),
                candidate_source=hex(LOADED_SOURCE), candidate_section=descriptor['number'],
                candidate_ordinal=descriptor['ordinal'], candidate_model=hex(target['model']),
                candidate_depth=target['depth'], candidate_quad=candidate,
                candidate_loaded_object_verified=True,
                original_ground_exact_match=True, candidate_absent_from_original_and_host=True,
                candidate_pixels=int(covered.sum()),
                candidate_box=[int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())],
                sky_overlap=int((covered & sky).sum()), gap_overlap=int((covered & gap).sum()),
                loaded_scene_quads=len(loaded_quads),
                exact_original_loaded_quads=sum(tuple(quad) in original_keys for quad in loaded_quads),
                exact_host_loaded_quads=sum(tuple(quad) in host_keys for quad in loaded_quads),
                unsubmitted_loaded_quads=len(unsubmitted),
                unsubmitted_left_margin_quads=len(margin),
                allocated_left_margin_quads=len(eligible),
                allocated_left_margin_gap_overlap=int(((eligible_tag != 0) & gap).sum()),
                all_left_margin_pixels=int(all_covered.sum()),
                all_left_margin_sky_overlap=int((all_covered & sky).sum()),
                all_left_margin_gap_overlap=int((all_covered & gap).sum()),
                gap_pixels=int(gap.sum()),
                sample=dict(x=60, y=960, tag=int(tag[960, 60]), pen=int(added[960, 60])),
                preview=preview,
                source_sha256={p.name: sha(p) for p in (ram, rom, texture,
                    ORIGINAL / 'run/vunit-mirror-3120-page1-plane0.bin',
                    ORIGINAL / 'run/vunit-mirror-3120-page1-plane1.bin')},
                scope='Single loaded-source isolated GPU screen; not ordered insertion or completed-image acceptance')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite saved screen')
    result = screen(args.preview_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('candidate_pixels', 'candidate_box',
                                              'sky_overlap', 'gap_overlap', 'sample')}))


if __name__ == '__main__':
    main()
