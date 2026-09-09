"""Bounded sampled USA future-scenery material continuity, not a lifetime proof."""
import argparse
import json
from pathlib import Path

from usa_sections import future, material_operands, final_flags, rom_span, palette_ownership
from verify_usa_future import Memory
from verification import sha256_file, write_json


def references(read):
    result = future(read)
    palettes, textures, models, owners = set(), set(), set(), {}
    custom = unsupported = unbound = 0
    for row in result['definitions']:
        meta, model = row['definition'][5], row['definition'][0]
        if meta & 0x2000:
            custom += 1; continue
        operands = material_operands(read, model)
        flags = final_flags(operands['model_prefix'], meta)
        if flags & 0x8e3:
            unsupported += 1; continue
        if not operands['palette_binding']:
            unbound += 1; continue
        if model in models:
            continue
        models.add(model)
        header = read(model+1)
        vertices, polygons = (header & 255)+1, (header >> 16)+1
        if polygons > 1024 or not rom_span(model, 2+2*vertices+5*polygons):
            raise ValueError('unsupported future model material span')
        for index in range(polygons):
            p = model+2+2*vertices+5*index
            poly, uv0, uv1, texture = read(p), read(p+2), read(p+3), read(p+4)
            if flags & 0x400:
                binding = operands['palette_binding']
                index = operands['model_prefix'] & 0xfff
            else:
                index = poly >> 16
                if read(0x62) != read(0x9ea9):
                    raise ValueError('lookup and allocation palette tables disagree')
                address = read(0x62)+index
                if not 0 <= address < 0x20000:
                    raise ValueError('lookup palette outside RAM')
                binding = read(address)
                if not binding:
                    unbound += 1; continue
            slot = palette_ownership(read, index)
            if slot is None:
                raise ValueError('bound material lost its palette ownership')
            owners[index] = slot
            bank = ((binding >> 16) << 8) & 65535
            if bank+256 > 32768:
                raise ValueError('palette bank outside captured hardware memory')
            palettes.add(bank)
            if poly & 0x300 == 0x100:
                coords = [uv0 & 65535, uv0 >> 16, uv1 & 65535, uv1 >> 16]
                u = [v & 255 for v in coords]; v = [v >> 8 for v in coords]
                base = (texture & 65535)*256
                if base+max(v)*256+max(u) >= 0x800000:
                    raise ValueError('texture footprint outside captured atlas')
                textures.add((base, min(u), max(u), min(v), max(v)))
    return dict(definitions=len(result['definitions']), models=len(models), custom=custom,
                unsupported=unsupported, unbound=unbound, palette_banks=sorted(palettes),
                texture_rectangles=sorted(textures), owners=owners)


def compare_samples(before, after, require_static=False):
    banks = before['refs']['palette_banks']
    changed = [bank for bank in banks if before['palette'][bank*4:(bank+256)*4] != after['palette'][bank*4:(bank+256)*4]]
    changed_owners = [index for index, slot in before['refs']['owners'].items()
                      if index in after['refs']['owners'] and after['refs']['owners'][index] != slot]
    atlas_equal = before['texture'] == after['texture']
    return dict(first=before['frame'], last=after['frame'], atlas_equal=atlas_equal,
                palette_banks=len(banks), changed_palette_banks=changed,
                compared_owners=len(set(before['refs']['owners']) & set(after['refs']['owners'])),
                changed_owners=changed_owners,
                passed=atlas_equal and not changed_owners and (not require_static or not changed))


def check(run, require_static=False):
    receipt = json.loads((run/'usa-future-capture.json').read_text())
    if receipt.get('complete') is not True:
        raise ValueError('incomplete USA resource capture')
    scenes = sorted(run.glob('usa-future-scene-*.json'))
    if len(scenes) != receipt['snapshots'] or len(scenes) < 2:
        raise ValueError('at least two complete resource snapshots required')
    rom = (run/'usa-future-rom.bin').read_bytes()
    snapshots = []
    for scene in scenes:
        frame = json.loads(scene.read_text())['frame']
        texture_path, palette_path = run/f'usa-future-textures-{frame}.bin', run/f'usa-future-palettes-{frame}.bin'
        texture, palette = texture_path.read_bytes(), palette_path.read_bytes()
        if len(texture) != 0x800000 or len(palette) != 0x20000:
            raise ValueError('incomplete hardware material snapshot')
        memory = Memory(rom, (run/f'usa-future-ram-{frame}.bin').read_bytes(), (run/f'usa-future-fast-{frame}.bin').read_bytes())
        ref = references(memory)
        snapshots.append(dict(frame=frame, refs=ref, texture=texture, palette=palette,
                              sources={p.name: sha256_file(p) for p in (texture_path, palette_path)}))
    evidence = []
    for i, before in enumerate(snapshots[:-1]):
        for after in snapshots[i+1:]:
            evidence.append(compare_samples(before, after, require_static))
    return dict(schema=2, passed=all(r['passed'] for r in evidence), require_static=require_static,
                snapshots=[dict(frame=s['frame'], sources=s['sources'], **{k: len(v) if isinstance(v, (list, dict)) else v for k, v in s['refs'].items()}) for s in snapshots],
                pairs=evidence, scope='Entire texture atlas and bound future-model palette ownership at five sampled scenes. '
                'Palette content changes remain reported and require live palette reads; no frozen-color cache. '
                'Changes between samples, pending uploads, unbound descriptors, full material lifetime and GPU acceptance remain unproven.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path); ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--require-static', action='store_true', help='also require unchanging palette colors; stricter diagnostic only')
    args = ap.parse_args()
    try:
        result = check(args.run, args.require_static)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = dict(schema=1, passed=False, error=str(error))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
