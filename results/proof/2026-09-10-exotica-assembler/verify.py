"""Verify receipt hashes and consistency; raw game execution is not repeated."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).parent
read = lambda name: json.loads((root/name).read_text(encoding='utf-8'))
manifest = read('manifest.json')
for name, digest in manifest['files'].items():
    path = (root/name).resolve()
    assert path.is_relative_to(root.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
checks = read('checks/report.json');identity = read('checks/source-identity.json')
payload = ''.join(f'{name}\0{digest}\n' for name, digest in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest() == identity['sha256'] == manifest['source_identity']
assert len(identity['files']) == 442
assert checks['passed'] and checks['source_identity'] == checks['source_identity_after'] == identity['sha256']
assert len(checks['steps']) == 99 and all(s['returncode'] == 0 for s in checks['steps'])
assert read('checks/unit-tests.json') == dict(errors=0, failures=0, passed=True, skipped=0, tests=295)
for frame, original, pairs, expected in (
        (5000, 2202, 219, [(913, 5291, 1813), (1515, 9596, 4740), (1515, 9596, 4740)]),
        (5072, 3255, 132, [(632, 5656, 330), (1296, 13345, 382), (1622, 16408, 382)]),
        (5990, 2012, 183, [(730, 4800, 457), (818, 5478, 457), (818, 5478, 457)])):
    scene = read(f'assembler{frame}-final.json')
    assert scene['passed'] and scene['immutable_inputs']
    assert scene['native_sha256'] == manifest['native_analyzer_sha256']
    assert scene['original_ordered_quads'] == original and scene['original_context_pairs'] == pairs
    assert len(scene['cases']) == 8
    for offset, fade in ((0, 'original'), (4, 'completed')):
        for i, multiplier in enumerate((1, 2, 3, 3)):
            case = scene['cases'][offset+i];n = case['native']
            assert case['passed'] and n['passed'] and case['fade'] == fade
            assert case['multiplier'] == multiplier and case['repeat'] == (i == 3)
            assert tuple(n[k] for k in ('instances', 'quads', 'viewport_quads')) == expected[multiplier-1]
        a, b = scene['cases'][offset+2:offset+4]
        assert a['quad_sha256'] == b['quad_sha256'] and a['instance_sha256'] == b['instance_sha256']
    assert scene['cases'][2]['quad_sha256'] != scene['cases'][6]['quad_sha256']
print(f"PASS {len(manifest['files'])} hash-bound receipts; raw geometry/executions are not recomputed.")
