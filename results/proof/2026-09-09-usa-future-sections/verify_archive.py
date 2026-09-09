"""Recompute public USA future proof; raw geometry/materials remain receipts."""
from pathlib import Path
import csv, io, json, hashlib, zipfile
from PIL import Image

root = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
manifest = json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes()) == manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as z:
    assert len(z.namelist()) == len(set(z.namelist())) and set(z.namelist()) == set(manifest['files'])
    data = {n: z.read(n) for n in z.namelist()}
for name, digest in manifest['files'].items(): assert sha(data[name]) == digest, name
read = lambda n: json.loads(data[n])
rows = lambda n: list(csv.DictReader(io.StringIO(data[n].decode())))
original = rows('original/frames.csv')
fields = [k for k in original[0] if k not in ('host_seconds', 'speed_percent')]
assert len(original) == 5012
images = None
for name in ['control', 'sections-final', 'future', 'future-resources']:
    prefix = 'runs/'+name+'/'
    assert read(prefix+'report.json')['passed'] and read(prefix+'report.json')['comparison']['passed']
    frames = rows(prefix+'frames.csv')
    assert [int(r['frame']) for r in frames] == list(range(1, 5013))
    assert [[r[k] for k in fields] for r in frames] == [[r[k] for k in fields] for r in original]
    for file, count in [('usa-camera.csv', 3211), ('usa-adc.csv', 9633)]:
        assert len(rows(prefix+file)) == count and data[prefix+file] == data['runs/control/'+file]
    captures = read(prefix+'captures.json')
    assert [int(c['completed_frame']) for c in captures] == [4900, 4950, 5000]
    pixels = []
    for c in captures:
        assert int(c['dropped_messages']) == 0
        image = Image.open(io.BytesIO(data['images/'+c['sha256']+'.png'])).convert('RGB')
        assert image.size == (3824, 2073)
        pixels.append(sha(image.tobytes()))
    if images is None: images = pixels
    assert pixels == images
    if name.startswith('future'):
        progress = rows(prefix+'usa-future-progress.csv')
        receipt = read(prefix+'usa-future-capture.json')
        assert receipt['complete'] and receipt['scenes'] == len(progress) == 1770 and receipt['snapshots'] == 5
        assert all(1800 <= int(r['frame']) <= 5010 and r['loading'] == r['next_section'] for r in progress)
        assert all(float(a['time']) < float(b['time']) for a, b in zip(progress, progress[1:]))
        assert len({(r['native_frame'], r['time'], r['page']) for r in progress}) == len(progress)
for name in ['sections-final-oracle-v1', 'future-sections-oracle', 'future-resources-sections']:
    r = read('receipts/'+name+'.json')
    assert r['passed'] and (r['objects'], r['eligible'], r['palettes'], r['custom']) == (1724, 1700, 1504, 24)
for name in ['future-native-oracle-final', 'future-resources-native-oracle']:
    r = read('receipts/'+name+'.json')
    assert r['passed'] and r['frontiers'] == 1770 and r['allocation_sources'] == 1724 and r['partial'] == 0
    assert sum(s['compared'] for s in r['snapshots']) == 3525
    assert sum(s['bound_palettes'] for s in r['snapshots']) == 3104
    assert sum(s['native']['compared'] for s in r['snapshots']) == 26807
    assert sum(s['native']['custom'] for s in r['snapshots']) == 185
material = read('receipts/future-materials-ownership.json')
assert material['passed'] and all(p['atlas_equal'] and not p['changed_owners'] for p in material['pairs'])
assert not read('receipts/future-materials-v1.json')['passed']
observations = read('palette-observations.json')
assert [r['frame'] for r in observations] == [3001, 3501, 4001, 4501, 4901]
assert all(r['owners'] == [[46, 4390913]] and r['owner_word'] == (0x8000 | 46) for r in observations)
assert set(i for r in observations for i in r['changed_indices']) == {251, 252, 253, 254, 255}
checks = read('checks/report.json')
assert checks['passed'] and checks['source_identity'] == checks['source_identity_after'] == manifest['source_identity']
identity = read('checks/source-identity.json')
content = ''.join(f'{name}\0{digest}\n' for name, digest in sorted(identity['files'].items())).encode()
assert sha(content) == identity['sha256'] == manifest['source_identity'] and len(identity['files']) == 339
for name, content in data.items():
    if name.startswith('source/'): assert sha(content.replace(b'\r\n', b'\n')) == identity['files'][name[7:]], name
for name, digest in checks['artifacts'].items(): assert sha(data['checks/'+name]) == digest
assert len(checks['steps']) == 53 and all(s['returncode'] == 0 for s in checks['steps'])
assert read('checks/unit-tests.json') == dict(passed=True, tests=223, errors=0, failures=0, skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks']) == 32
print('PASS: four original routes/motion traces, three late4K images, frontier sequence and palette ownership scalars; full descriptors/resources/native/GPU checks remain receipts.')
