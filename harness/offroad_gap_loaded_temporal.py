"""Check saved later Off-Road source against loaded ground missing from both draw lists.

Read-only resource and isolated GPU screen; this does not insert native geometry.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from analyze_vunit_margin_gap import PACKET, analyze, projected_box
from offroad_gap_loaded_screen import render_quads, resolve, LOADED_SOURCE, sha
from offroad_scene import scene
from offroad_sections import sections
from screen_vunit_sky_gaps import candidates
from verify_offroad_future import Memory, allocated_pool
from vunit_display_scene import load as load_original

HERE = Path(__file__).resolve().parents[1] / 'results/diagnostics/offroad-full-20260910'
SOURCE = HERE / 'left-gap-3136-source-run'
RESOURCE = HERE / 'left-gap-resource-3132-run'


def screen(preview_dir=None):
    source = analyze(SOURCE, [(60, 970), (60, 1030)], (60, 965, 60, 975), SOURCE)
    resource_report = json.loads((RESOURCE / 'report.json').read_text(encoding='utf-8'))
    source_report = json.loads((SOURCE / 'report.json').read_text(encoding='utf-8'))
    if not resource_report['passed'] or not source_report['passed'] or resource_report['case'] != source_report['case']:
        raise ValueError('resource and source case mismatch')
    ra = json.loads((RESOURCE / 'run/invocation.json').read_text(encoding='utf-8'))
    sa = json.loads((SOURCE / 'run/invocation.json').read_text(encoding='utf-8'))
    if ra['executable_sha256'] != sa['executable_sha256'] or ra['environment']['MIDV_FFB'] != '0':
        raise ValueError('native executable or force mismatch')
    run = RESOURCE / 'run'
    ram = run / 'offroad-resource-3132-ram.bin'
    rom = run / 'offroad-resource-rom.bin'
    texture = run / 'offroad-resource-3132-textures.bin'
    memory = Memory(rom.read_bytes(), ram.read_bytes())
    _, future = scene(memory, 3, True)
    host = [quad for item in future for quad in item['quads']]
    packets = list(PACKET.iter_unpack((SOURCE / 'run/vunit-fade-producer.bin').read_bytes()[4:]))
    if len(host) != len(packets) or any(quad != list(packet[3:19]) for quad, packet in zip(host, packets)):
        raise ValueError('resource projection does not match saved host packets')
    _, loaded = scene(memory, 1, True, loaded_sections=True)
    original = load_original(SOURCE / 'run').current
    original_keys = {tuple(map(int, quad)) for quad in original}
    host_keys = {tuple(quad) for quad in host}
    loaded_quads = [quad for item in loaded for quad in item['quads']]
    absent = [quad for quad in loaded_quads if tuple(quad) not in original_keys and tuple(quad) not in host_keys]
    margin_items = [(item, quad) for item in loaded for quad in item['quads']
                    if tuple(quad) not in original_keys and tuple(quad) not in host_keys
                    and projected_box(quad)[0] < 0 and projected_box(quad)[2] >= -86]
    margin = [quad for _, quad in margin_items]
    if len(set(map(tuple, margin))) != len(margin):
        raise ValueError('duplicate left-margin loaded geometry')
    index, tags = render_quads(margin, texture.read_bytes())
    page = source['page']
    old_path = SOURCE / f'run/vunit-mirror-3136-page{page}-plane0.bin'
    tag_path = SOURCE / f'run/vunit-mirror-3136-page{page}-plane1.bin'
    old = np.fromfile(old_path, dtype='<u2').reshape(1600, 2736)
    old_tags = np.fromfile(tag_path, dtype='u1').reshape(1600, 2736)
    sky = (old >= 6912) & (old < 7168) & (old_tags == 1)
    gap = candidates(sky, old_tags, 344, 2736-344, 128)
    covered = tags != 0
    preview = None
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=False)
        palette_path = run / 'offroad-resource-3132-palettes.bin'
        palette = palette_path.read_bytes()
        baseline = resolve(old, old_tags, palette)
        proposed_index, proposed_tags = old.copy(), old_tags.copy()
        replacement = covered & sky
        proposed_index[replacement] = index[replacement]
        proposed_tags[replacement] = tags[replacement]
        proposal = resolve(proposed_index, proposed_tags, palette)
        reference = np.asarray(Image.open(SOURCE / 'run/gl-snap/mvgl_000.bmp').convert('RGB'))
        delta = np.max(np.abs(baseline.astype('i2') - reference.astype('i2')), axis=2)
        if int((delta > 1).sum()) > baseline.shape[0] * baseline.shape[1] // 10000:
            raise ValueError('offline palette resolve exceeds baseline tolerance')
        Image.fromarray(baseline).save(preview_dir / 'baseline.png')
        Image.fromarray(proposal).save(preview_dir / 'all-left-sky-only.png')
        crop = (40, 450, 520, 1200)
        contact = Image.new('RGB', (960, 780), 'black')
        draw = ImageDraw.Draw(contact)
        for i, (name, rgb) in enumerate((('baseline', baseline), ('all-left', proposal))):
            contact.paste(Image.fromarray(rgb).crop(crop), (i * 480, 30))
            draw.text((i * 480 + 8, 7), name, fill='white')
        contact.save(preview_dir / 'comparison-crop.png')
        preview = dict(replaced_indexed_sky_pixels=int(replacement.sum()),
                       changed_completed_pixels=int(np.count_nonzero(np.any(proposal != baseline, axis=2))),
                       baseline_completed_differences_over_one=int((delta > 1).sum()),
                       max_baseline_channel_difference=int(delta.max()), palette_sha256=sha(palette_path),
                       scope='Sky-only offline composite; native draw order and exact completed acceptance unproven')
    relevant = []
    descriptors = {item['source']: item for item in sections(memory, loaded=True)['sources']}
    allocation = allocated_pool(memory)
    for item, quad in margin_items:
        box = projected_box(quad)
        if not (box[0] <= -71 <= box[2] and box[1] <= 172 and box[3] >= 145):
            continue
        _, own_tags = render_quads([quad], texture.read_bytes())
        source_id = item['id'] & 0x7fffffff
        descriptor = descriptors[source_id]
        owners = allocation.get(descriptor['words'][6], [])
        allocated_match = len(owners) == 1 and owners[0][5] & 0x7fffffff == descriptor['words'][5] and all(
            owners[0][i] == descriptor['words'][i] for i in (*range(6, 9), *range(11, 21)))
        relevant.append(dict(source=hex(item['id'] & 0x7fffffff), model=hex(item['model']),
                             depth=item['depth'], box=box, material=[quad[0], quad[1], quad[14]],
                             section=descriptor['number'], ordinal=descriptor['ordinal'],
                             allocated_object_match=allocated_match,
                             gap_overlap=int(((own_tags != 0) & gap).sum()),
                             sky_overlap=int(((own_tags != 0) & sky).sum())))
    relevant.sort(key=lambda row: -row['gap_overlap'])
    target = next((item for item in loaded if item['id'] == (0x80000000 | LOADED_SOURCE)), None)
    target_quads = [] if target is None else target['quads']
    if target_quads:
        tindex, ttags = render_quads(target_quads, texture.read_bytes())
        target_result = dict(projected=True, quads=len(target_quads), absent=sum(tuple(q) not in original_keys
                             and tuple(q) not in host_keys for q in target_quads),
                             gap_overlap=int(((ttags != 0) & gap).sum()),
                             sky_overlap=int(((ttags != 0) & sky).sum()),
                             sample_tag=int(ttags[970, 60]), sample_pen=int(tindex[970, 60]))
    else:
        target_result = dict(projected=False)
    return dict(source_frame=source['source_frame'], completed_frame=source['completed_frame'],
                original_quads=len(original), host_quads=len(host), host_exact_match=True,
                loaded_quads=len(loaded_quads), original_loaded_matches=sum(tuple(q) in original_keys for q in loaded_quads),
                host_loaded_matches=sum(tuple(q) in host_keys for q in loaded_quads),
                absent_loaded_quads=len(absent), absent_left_margin_quads=len(margin),
                gap_pixels=int(gap.sum()), gap_covered=int((covered & gap).sum()),
                sky_covered=int((covered & sky).sum()),
                relevant_loaded_sources=relevant,
                preview=preview,
                candidate_source=hex(LOADED_SOURCE), candidate=target_result,
                source_sha256={path.name: sha(path) for path in (ram, rom, texture, old_path, tag_path)},
                scope='Saved-source match plus isolated GPU screen only; no native ordered insertion or product acceptance')


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
    print(json.dumps({k: result[k] for k in ('host_quads', 'gap_pixels', 'gap_covered', 'candidate')}))


if __name__ == '__main__':
    main()
