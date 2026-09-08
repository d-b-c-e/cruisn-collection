"""Describe matched-geometry depth-state changes; never certify scene equivalence."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct


def read_quads(path):
    data = Path(path).read_bytes()
    quads, offset = [], 0
    sizes = {1: 260, 2: 1024, 3: 16, 4: 24}
    while offset < len(data):
        if len(data) - offset < 8:
            raise ValueError('truncated record header')
        kind, size = struct.unpack_from('<II', data, offset)
        offset += 8
        if sizes.get(kind) != size or len(data) - offset < size:
            raise ValueError('invalid record type or size')
        payload = data[offset:offset + size]
        offset += size
        if kind == 1:
            if not 3 <= struct.unpack_from('<I', payload, 4)[0] <= 8:
                raise ValueError('invalid vertex count')
            quads.append(payload)
    if not quads:
        raise ValueError('empty quad stream')
    return hashlib.sha256(data).hexdigest(), quads


def analyze(reference, candidate):
    captures = [read_quads(path) for path in (reference, candidate)]
    groups = [defaultdict(list), defaultdict(list)]
    for lookup, (_, quads) in zip(groups, captures):
        for index, payload in enumerate(quads):
            # Match the earlier state-delta report, including unused vertex slots.
            lookup[payload[4:8] + payload[68:]].append((index, payload))
    matched = ambiguous = 0
    pairs = []
    for geometry, originals in groups[0].items():
        candidates = groups[1].get(geometry, [])
        unique = len(originals) == len(candidates) == 1
        for (i, a), (j, b) in zip(originals, candidates):
            matched += 1
            ambiguous += not unique
            old_flags, old_bias = struct.unpack_from('<Ii', a, 36)
            new_flags, new_bias = struct.unpack_from('<Ii', b, 36)
            if old_bias == new_bias:
                continue
            # Depth-clear overrides the bias branch in both CPU and GL paths.
            used = lambda flags: bool(flags & 4 and not flags & 32)
            pairs.append(dict(reference_quad=i, candidate_quad=j,
                old_bias=old_bias, new_bias=new_bias, old_flags=old_flags,
                new_flags=new_flags, used_in_reference=used(old_flags),
                used_in_candidate=used(new_flags), unique_geometry=unique))
    transitions = Counter((p['old_bias'], p['new_bias']) for p in pairs)
    return dict(scope=__doc__, record_sha256=[item[0] for item in captures],
        quads=[len(item[1]) for item in captures], matched_geometry=matched,
        ambiguous_geometry_pairs=ambiguous, changed_bias_pairs=len(pairs),
        changed_bias_unique_geometry=sum(p['unique_geometry'] for p in pairs),
        bias_used_in_both=sum(p['used_in_reference'] and p['used_in_candidate'] for p in pairs),
        transitions=[dict(old_bias=a, new_bias=b, count=n)
                     for (a, b), n in sorted(transitions.items())],
        pairs=pairs,
        limitations=[
            'Geometry association does not prove object identity or original draw order.',
            'Duplicate geometry is paired in occurrence order and marked ambiguous.',
            'A used depth-bias branch does not prove a visible-pixel change.',
            'This report neither changes nor waives strict frame/scene FAIL results.',
        ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path)
    mode.add_argument('--check', type=Path)
    args = parser.parse_args()
    report = analyze(args.reference, args.candidate)
    if args.check:
        if json.loads(args.check.read_text(encoding='utf-8')) != report:
            raise ValueError('derived state-bias receipt does not recompute')
    else:
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('pairs', 'limitations')}, indent=2))


if __name__ == '__main__':
    main()
