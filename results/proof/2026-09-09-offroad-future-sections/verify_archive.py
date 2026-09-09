"""Public input/pixel/scalar proof. Raw model/resource checks remain receipts."""
from pathlib import Path
import csv
import hashlib
import io
import json
import zipfile
from PIL import Image, ImageChops

root = Path(__file__).resolve().parent
sha = lambda data: hashlib.sha256(data).hexdigest()
manifest = json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes()) == manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as archive:
    assert len(archive.namelist()) == len(set(archive.namelist()))
    assert set(archive.namelist()) == set(manifest['files'])
    data = {name: archive.read(name) for name in archive.namelist()}
for name, digest in manifest['files'].items():
    assert sha(data[name]) == digest, name
read = lambda name: json.loads(data[name])
rows = lambda name: list(csv.DictReader(io.StringIO(data[name].decode())))
original = rows('original/frames.csv')
keys = [k for k in original[0] if k not in ('host_seconds', 'speed_percent')]
reference = [[r[k] for k in keys] for r in original]
assert len(reference) == 6000
images = None
for name in manifest['runs']:
    prefix = 'runs/'+name+'/'
    report = read(prefix+'report.json')
    assert report['passed'] and report['comparison']['passed']
    frames = rows(prefix+'frames.csv')
    assert [int(r['frame']) for r in frames] == list(range(1, 6001))
    assert [[r[k] for k in keys] for r in frames] == reference
    for file, count in [('offroad-camera.csv', 4191), ('offroad-adc.csv', 16764)]:
        assert data[prefix+file] == data['runs/control6000/'+file]
        assert len(rows(prefix+file)) == count
    if name not in manifest['visible_runs']:
        continue
    captures = read(prefix+'captures.json')
    assert [int(r['completed_frame']) for r in captures] == [5500, 5550, 5600]
    current = []
    for row in captures:
        assert int(row['completed_frame']) == int(row['last_received_frame'])
        assert int(row['dropped_messages']) == 0
        image = Image.open(io.BytesIO(data['images/'+row['sha256']+'.png'])).convert('RGB')
        assert image.size == (3824, 2073) == (int(row['width']), int(row['height']))
        current.append(image)
    if images is None:
        images = current
    for a, b in zip(images, current):
        assert ImageChops.difference(a, b).getbbox() is None

# Recompute arithmetic frontier guards from captured scalar fields. Actual ROM
# section markers/membership and complete descriptors require local raw resources.
for run in ('sections', 'sections-frontiers'):
    prefix = 'runs/'+run+'/'
    receipt = read(prefix+'offroad-section-capture.json')
    trace = rows(prefix+'offroad-section-progress.csv')
    assert receipt['complete'] and receipt['started'] == receipt['completed'] == 1409
    assert receipt['scenes'] == len(trace) == 1978
    partial, initialized, previous = [], 0, -1
    for serial, row in enumerate(trace, 1):
        r = {k: int(v) for k, v in row.items() if k != 'time'}
        now = float(row['time'])
        assert r['scene'] == serial and now > previous and r['pc'] == 0x1bf9
        assert receipt['first'] <= r['frame'] <= receipt['last'] and r['live_allocations'] == 0
        previous = now
        if not r['track']:
            assert not any(r[k] for k in ('current_entry', 'front_entry', 'back_entry', 'count'))
            continue
        initialized += 1
        assert r['mode'] == 1 and 1 <= r['count'] <= 128
        for field, number in [('current_entry', 'current'), ('front_entry', 'front'), ('back_entry', 'back')]:
            assert r[field] == r['track']+4*r[number] and 0 <= r[number] < r['count']
        assert r['back'] <= r['current'] <= r['front']
        assert r['trail'] == r['current']-r['back']
        delta = r['lead']-(r['front']-r['current'])
        assert delta in (0, 1)
        if delta:
            assert r['front']+1 < r['count']
            partial.append(r['frame'])
    assert initialized == 1926 and partial == [2099, 2255, 2369, 2537, 4228, 4538, 5814]

for name, projections, quads in [('early', 463, 3309), ('middle', 182, 4633), ('late', 754, 1660)]:
    receipt = read('receipts/prepared-'+name+'.json')
    assert receipt['passed'] and receipt['native_checked'] and receipt['prepared_native_checked']
    assert receipt['prepared_transforms'] == receipt['lod_selections'] == projections
    assert receipt['quads'] == quads and not receipt['failures']
final = read('receipts/verified-frontiers-v1.json')
assert final['passed'] and not final['failures']
assert final['initial'] == 1380 and final['initial_dynamic_excluded'] == 29
assert len(final['snapshots']) == 12
assert sum(s['loaded_matched'] for s in final['snapshots']) == 2424
assert sum(s['later_matched'] for s in final['snapshots']) == 703
assert sum(s['later_bindings'] for s in final['snapshots']) == 703
for name in ('yaw-rounding', 'model-replacement', 'incomplete-frontier', 'missing-dll-path'):
    assert read('failures/'+name+'.json')['passed'] is False
for label, count, commands, tests in [('checks', 358, 61, 239), ('prepared-checks', 351, 58, 235)]:
    checks = read(label+'/report.json'); identity = read(label+'/source-identity.json')
    assert checks['passed'] and checks['source_identity'] == checks['source_identity_after'] == identity['sha256']
    payload = ''.join(f'{name}\0{digest}\n' for name, digest in sorted(identity['files'].items())).encode()
    assert sha(payload) == identity['sha256'] and len(identity['files']) == count
    assert len(checks['steps']) == commands and all(r['returncode'] == 0 for r in checks['steps'])
    for name, digest in checks['artifacts'].items():
        assert sha(data[label+'/'+name]) == digest
    assert read(label+'/unit-tests.json') == dict(passed=True, tests=tests, errors=0, failures=0, skipped=0)
    assert read(label+'/gpu-quality.json')['passed'] and len(read(label+'/gpu-quality.json')['checks']) == 32
identity = read('checks/source-identity.json')
assert identity['sha256'] == manifest['source_identity']
for name, content in data.items():
    if name.startswith('source/'):
        assert sha(content.replace(b'\r\n', b'\n')) == identity['files'][name[7:]], name
print('PASS: eight original input/motion traces, fifteen completed4K images and '
      '1978 scalar frontiers per canonical probe; raw geometry/materials and native/GPU execution remain receipts.')
