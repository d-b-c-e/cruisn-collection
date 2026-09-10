"""Recompute sanitized trace comparisons; raw game resources remain local."""
from pathlib import Path
import csv
import hashlib
import json
import statistics

root = Path(__file__).parent
read = lambda n: json.loads((root/n).read_text(encoding='utf-8'))
manifest = read('manifest.json')
for name, digest in manifest['files'].items():
    path = (root/name).resolve()
    assert path.is_relative_to(root.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
identity = read('checks/source-identity.json');checks = read('checks/report.json')
payload = ''.join(f'{n}\0{h}\n' for n, h in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest() == identity['sha256'] == manifest['source_identity']
assert checks['passed'] and checks['source_identity'] == checks['source_identity_after'] == identity['sha256']
assert len(identity['files']) == 454 and len(checks['steps']) == 103
assert all(s['returncode'] == 0 for s in checks['steps'])
assert read('checks/unit-tests.json') == dict(passed=True, tests=307, skipped=0, errors=0, failures=0)
native = read('native-export.json');defaults = read('defaults.json')
assert native['passed'] and native['patch_count'] == 162
assert native['native_commit'] == '86deac56192a7692110d44d264b5d30b02c5f208'
assert native['candidate_sha256'] == 'f25ecd8ea7cd9d2a0c13becb94c96d59aebffc8f1aabe92cd6431c2cfe18e471'
assert native['personal_sha256'] == '87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
assert defaults['passed'] and len(defaults['cases']) == 7 and defaults['subset'] is None
assert defaults['candidate_sha256'] == native['candidate_sha256'] and not defaults['physical_force']
assert defaults['source_identity'] == identity['sha256']
assert all(c['passed'] and c['telemetry']['passed'] for c in defaults['cases'])
forces = [c['force_gate'] for c in defaults['cases'] if 'force_gate' in c]
assert len(forces) == 4 and all(f['passed'] for f in forces)

labels = ['5072-off3', '5072-on1', '5072-on2', '5072-on3', '5072-repeat3',
          '5000-off3', '5000-on3', '5990-on3', '5978-off3', '5978-on3']
traces = {}
for label in labels:
    assert read(label+'/run.json')['passed'] and read(label+'/oracle.json')['passed']
    motion = read(label+'/motion.json')
    assert motion['passed'] and motion['camera_samples'] == [4191, 4191]
    assert motion['actual_adc_reads'] == [12573, 12573] and motion['adc_times_equal']
    for name in ('gl', 'resources', 'visible'):
        if (root/label/(name+'.json')).exists():
            receipt = read(label+'/'+name+'.json');assert receipt['passed']
            if name == 'gl':assert receipt['different_frames'] == []
            if name == 'resources':assert len(receipt['files']) == 10 and all(a == b for a, b in receipt['files'].values())
    with (root/label/'scenes.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2457 and all(int(r['guest_cycles']) == 0 for r in rows)
    assert all(int(a['scene']) < int(b['scene']) for a, b in zip(rows, rows[1:]))
    traces[label] = rows

clock = ['frame', 'cpu_frame', 'cpu_time', 'device_time', 'scene', 'scene_frame', 'scene_time']
def equal(a, b, fields):
    assert all(all(x[k] == y[k] for k in fields) for x, y in zip(traces[a], traces[b]))
for label in labels[:5]:equal('5072-off3', label, clock)
for label in ('5072-on3', '5072-repeat3'):equal('5072-off3', label, ['viewport'])
equal('5000-off3', '5000-on3', clock+['viewport'])
equal('5978-off3', '5978-on3', clock+['viewport'])
repeat = clock+['multiplier', 'instances', 'quads', 'viewport', 'hash', 'bounds', 'culled_bounds']
equal('5072-on3', '5072-repeat3', repeat)
equal('5000-on3', '5990-on3', repeat)
assert sum(int(r['quads']) for r in traces['5072-on3']) == 4848660
assert sum(int(r['quads']) for r in traces['5000-on3']) == 2776927
third = 0
for a, b, c in zip(traces['5072-on1'], traces['5072-on2'], traces['5072-on3']):
    assert int(a['viewport']) <= int(b['viewport']) <= int(c['viewport'])
    third += int(c['viewport']) > int(b['viewport'])
assert third == 578
for frame in (5000, 5072, 5990):
    for mode in ('off', 'on'):
        receipt = read(f'offline/{frame}-{mode}.json')
        assert receipt['passed'] and receipt['immutable_inputs'] and len(receipt['cases']) == 8
extra = read('offline/5978-on.json');assert extra['passed'] and len(extra['cases']) == 8
gpu = read('scene5978-local-composition.json')
assert gpu['passed'] and gpu['size'] == [1368, 800] and gpu['original_depth_unchanged']
assert gpu['original_wave_gpu_exact'] and gpu['private_wave_gpu_exact']
assert gpu['additional_color_changes_3_over_2'] == 1110
for label in ('5072-off3', '5072-on3', '5000-off3', '5000-on3'):
    costs = sorted(sum(float(r[k]) for k in ('source_us', 'assembly_us', 'hash_us'))/1000 for r in traces[label])
    rank = (len(costs)-1)*.99;lo = int(rank)
    p99 = costs[lo]+(costs[lo+1]-costs[lo])*(rank-lo)
    print(f'{label}: mean {statistics.mean(costs):.3f}ms, p99 {p99:.3f}ms; raw snapshot I/O excluded')
print(f'PASS {len(manifest["files"])} evidence hashes, sanitized traces and receipts; raw geometry/resources/pixels not recomputed.')
