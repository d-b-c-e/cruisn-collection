"""Check whether qualified static Off-Road billboards can cover the saved gap.

This is a source/material/projected-bounds screen for the El Paso 3116/3120
fixture, not a runtime billboard adapter or a raster visibility test.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from analyze_vunit_margin_gap import PACKET, analyze, gap_distance, projected_box
from offroad_billboard_source import descriptor
from offroad_billboard import prepare, quad
from offroad_scene import scene, position_and_order, host_project
from offroad_sections import sections, span
from scenery_c31 import F
from verification import sha256_file
from verify_offroad_future import Memory


ROOT = Path(__file__).resolve().parents[1] / 'results/diagnostics/offroad-full-20260910'
MATCHED = ROOT / 'left-gap-matched-run'
RESOURCE = ROOT / 'left-gap-resource-run'
ORIGINAL = ROOT / 'left-gap-original-run'


def screen():
    # Recheck the source/display join, actual indexed sample, and same-run
    # original commands rather than trusting a previous JSON summary.
    source = analyze(MATCHED, [(60, 940), (60, 960), (60, 990)],
                     (60, 956, 60, 964), ORIGINAL)
    report = json.loads((RESOURCE / 'report.json').read_text(encoding='utf-8'))
    if report.get('passed') is not True or report['case'] != json.loads(
            (MATCHED / 'report.json').read_text(encoding='utf-8'))['case']:
        raise ValueError('resource replay does not match passing recording')
    matched_invocation = json.loads((MATCHED / 'run/invocation.json').read_text(encoding='utf-8'))
    resource_invocation = json.loads((RESOURCE / 'run/invocation.json').read_text(encoding='utf-8'))
    if matched_invocation['executable_sha256'] != resource_invocation['executable_sha256']:
        raise ValueError('resource replay executable differs')
    ram_path = RESOURCE / 'run/offroad-resource-3116-ram.bin'
    rom_path = RESOURCE / 'run/offroad-resource-rom.bin'
    memory = Memory(rom_path.read_bytes(), ram_path.read_bytes())
    ordinary_counts, ordinary = scene(memory, 3, True, retain_depths=True)
    actual = list(PACKET.iter_unpack((MATCHED / 'run/vunit-fade-producer.bin').read_bytes()[4:]))
    decoded = [q for obj in ordinary for q in obj['quads']]
    if (len(decoded) != len(actual) or
            any(q != list(packet[3:19]) for q, packet in zip(decoded, actual))):
        raise ValueError('resource scene differs from all captured host packets')

    view = [memory(memory(0x1120b) + i) for i in range(12)]
    basis = [memory(memory(0x1120e) + i) for i in range(12)]
    binding = [memory(a) for a in (0x1b4cd, 0x1b4cf, 0x1b4ce)]
    if memory(0x11145) or memory(0x19e20):
        raise ValueError('saved billboard material or damage state changed')
    pending = []
    owner = memory(0x1b73e)
    seen = set()
    while owner:
        if owner in seen or len(seen) >= 2048:
            raise ValueError('invalid pending billboard list')
        seen.add(owner)
        obj = [memory(owner + i) for i in range(22)]
        pending.append((owner, obj))
        owner = obj[0]

    counts = Counter()
    candidates = []
    future_sources = sections(memory)['sources']
    unsupported_future_flags = Counter(source['flags'] for source in future_sources
                                       if not source['supported'])
    for section in future_sources:
        definition = section['definition']
        hit_index = definition[3] >> 16
        flags = definition[0]
        if flags not in (0x804, 0x800804):
            continue
        bits = memory(memory(0x1b4da) + (hit_index >> 5)) if flags & 0x800000 else 0
        obj = descriptor(definition, section['number'], section['ordinal'],
                         memory(memory(section['entry'] + 3) + 16),
                         binding, hit_index, bits)
        if obj is None:
            counts['damaged_future'] += 1
            continue
        candidates.append((section['source'] | 0x80000000, obj, 'future'))
    for owner, obj in pending:
        flags = obj[5] & 0x7fffffff
        if flags not in (0x804, 0x800804):
            continue
        hit_index = obj[7] >> 16
        if flags & 0x800000 and memory(memory(0x1b4da) + (hit_index >> 5)) & (1 << (hit_index & 31)):
            counts['damaged_pending'] += 1
            continue
        candidates.append((owner, obj, 'pending'))

    projected = []
    box = tuple(source['native_box'])
    for owner, obj, kind in candidates:
        counts[kind + '_candidates'] += 1
        position, _ = position_and_order(obj, view, F.load(memory(0x11238)))
        near = position[2] - F.load(memory(obj[20]))
        if near.value() < 1000:
            counts['near'] += 1
            continue
        if near.value() >= 141888:
            counts['far'] += 1
            continue
        model = obj[20] + 7
        words = [memory(model + i) for i in range(5)]
        if words[0] != 3 or words[3] != 0:
            counts['unsupported_model'] += 1
            continue
        if not span(words[1], 12) or not span(words[4], 6):
            raise ValueError('invalid static billboard model span')
        matrix = prepare(obj, view, basis)
        vertices = [memory(words[1] + i) for i in range(12)]
        depths = []
        xy = host_project(vertices, matrix, memory(0x11230), memory, 3, camera_depths=depths)
        if xy is None:
            counts['projection'] += 1
            continue
        xyz = [value for i in range(4) for value in
               (xy[2 * i], xy[2 * i + 1], F.load(depths[i]).fix())]
        polygon = [memory(words[4] + i) for i in range(6)]
        command = quad(obj, polygon, xyz,
                       memory(obj[17] + (polygon[0] >> 16)),
                       0x2000 if obj[5] & memory(0x11249) else 0)
        palette_end, texture_end = memory(0x19e21) * 256, memory(0x19e23) * 256
        if command[0] & 0x300 != 0x100:
            valid = command[1] + (command[0] & 255) < palette_end
        else:
            u = max(word & 255 for word in command[10:14])
            v = max(word >> 8 for word in command[10:14])
            valid = (command[1] + 255 < palette_end and
                     command[14] * 256 + min(v + 1, 255) * 256 + min(u + 1, 255) < texture_end)
        if not valid:
            counts['material'] += 1
            continue
        projected.append(dict(owner=owner, kind=kind, bounds=list(projected_box(command)),
                              flags=command[0], palette=command[1], texture=command[14]))

    for item in projected:
        item['distance'] = gap_distance(item['bounds'], box)
    nearest = sorted(projected, key=lambda item: (item['distance'], item['owner']))
    return dict(passed=True, source_frame=source['source_frame'],
                completed_frame=source['completed_frame'], native_gap_box=list(box),
                ordinary_host_objects=len(ordinary), ordinary_host_quads=len(decoded),
                ordinary_host_packet_bytes_exact=True,
                source_hash=source['source_hash'],
                ordinary_selection_counts=dict(ordinary_counts), counts=dict(counts),
                unsupported_future_flags={hex(flag): count for flag, count in
                                          sorted(unsupported_future_flags.items())},
                material_valid_extra_billboards=len(projected),
                bounds_intersecting_gap=sum(item['distance'] == 0 for item in projected),
                nearest=nearest[:20],
                sha256={p.name: sha256_file(p) for p in
                        (MATCHED / 'report.json', RESOURCE / 'report.json',
                         ram_path, rom_path, MATCHED / 'run/vunit-fade-producer.bin')},
                scope='One saved El Paso scene. Static undamaged billboard classes only; '
                      'projected bounds, not raster visibility. Other classes and courses '
                      'remain unsupported. No game run or runtime adapter.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite saved billboard screen')
    result = screen()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print({k: result[k] for k in ('passed', 'ordinary_host_quads',
                                  'material_valid_extra_billboards',
                                  'bounds_intersecting_gap')})


if __name__ == '__main__':
    main()
