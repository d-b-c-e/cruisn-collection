"""Recompute public Off Road route/pixel evidence; raw model operands stay local."""
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
    short = name in ('control', 'model', 'model-v2')
    report = read(prefix+'report.json')
    assert report['passed'] and report['comparison']['passed']
    frames = rows(prefix+'frames.csv')
    count = 3001 if short else 6000
    assert [int(r['frame']) for r in frames] == list(range(1, count+1))
    assert [[r[k] for k in keys] for r in frames] == reference[:count]
    control = 'runs/'+('control' if short else 'control6000')+'/'
    for file, expected in [('offroad-camera.csv', 1201 if short else 4191),
                           ('offroad-adc.csv', 4804 if short else 16764)]:
        assert data[prefix+file] == data[control+file]
        assert len(rows(prefix+file)) == expected
    if short:
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
for name, projections, quads in [('model-v2', 463, 3309), ('middle', 182, 4633),
                                  ('late', 754, 1660), ('canonical', 463, 3309)]:
    receipt = read('receipts/'+name+'.json')
    assert receipt['passed'] and receipt['native_checked'] and not receipt['failures']
    assert receipt['projected'] == projections and receipt['quads'] == quads
    assert receipt['projection_paths'] == [0x1e03] and receipt['page_controls'] == [0x201, 0x204]
assert not read('failures/two-word-stride.json')['passed']
assert not read('failures/raw-page-register.json')['passed']
assert not read('failures/adc-count.json')['passed']
checks = read('checks/report.json')
assert checks['passed'] and checks['source_identity'] == checks['source_identity_after'] == manifest['source_identity']
identity = read('checks/source-identity.json')
payload = ''.join(f'{name}\0{digest}\n' for name, digest in sorted(identity['files'].items())).encode()
assert sha(payload) == identity['sha256'] == manifest['source_identity']
assert len(identity['files']) == 348
for name, content in data.items():
    if name.startswith('source/'):
        assert sha(content.replace(b'\r\n', b'\n')) == identity['files'][name[7:]], name
assert len(checks['steps']) == 56 and all(r['returncode'] == 0 for r in checks['steps'])
for name, digest in checks['artifacts'].items():
    assert sha(data['checks/'+name]) == digest
assert read('checks/unit-tests.json') == dict(passed=True, tests=232, errors=0, failures=0, skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks']) == 32
print('PASS: seven original input/motion traces and twelve completed4K images; '
      'private geometry, native execution and GPU verdicts remain receipts.')
