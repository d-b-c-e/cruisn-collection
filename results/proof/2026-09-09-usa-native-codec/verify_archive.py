"""Recompute archived USA input/motion/pixel evidence; model data stays local."""
from pathlib import Path
import csv,hashlib,io,json,zipfile
from PIL import Image,ImageChops

root=Path(__file__).resolve().parent
sha=lambda data:hashlib.sha256(data).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as archive:
    assert len(archive.namelist())==len(set(archive.namelist()))
    assert set(archive.namelist())==set(manifest['files'])
    data={name:archive.read(name) for name in archive.namelist()}
for name,digest in manifest['files'].items():assert sha(data[name])==digest,name
read=lambda name:json.loads(data[name])
rows=lambda name:list(csv.DictReader(io.StringIO(data[name].decode())))
original=rows('original/frames.csv')
keys=[k for k in original[0] if k not in ('host_seconds','speed_percent')]
reference=[[r[k] for k in keys] for r in original]
assert len(reference)==5012
images=None
for name in ['control','early','late','prepared-early','prepared-late']:
    prefix='runs/'+name+'/'
    report=read(prefix+'report.json')
    assert report['passed'] and report['comparison']['passed']
    frames=rows(prefix+'frames.csv')
    assert [int(r['frame']) for r in frames]==list(range(1,5013))
    assert [[r[k] for k in keys] for r in frames]==reference
    for file in ['usa-camera.csv','usa-adc.csv']:
        assert data[prefix+file]==data['runs/control/'+file]
    captures=read(prefix+'captures.json')
    assert [int(r['completed_frame']) for r in captures]==[4900,4950,5000]
    current=[]
    for row in captures:
        assert int(row['dropped_messages'])==0
        image=Image.open(io.BytesIO(data['images/'+row['sha256']+'.bmp'])).convert('RGB')
        assert image.size==(3824,2073)
        current.append(image)
    if images is None:images=current
    for a,b in zip(images,current):assert ImageChops.difference(a,b).getbbox() is None
assert len(rows('runs/control/usa-camera.csv'))==3211
assert len(rows('runs/control/usa-adc.csv'))==9633
for label,count,fast,quads,excluded in [('early',5178,5068,44652,110),('late',13725,13473,66846,252)]:
    receipt=read('receipts/final-'+label+'-model.json')
    assert receipt['passed'] and receipt['native_checked'] and receipt['prepared_native_checked']
    assert receipt['projected']==receipt['prepared_transforms']==count
    assert receipt['unclipped']==fast and receipt['quads']==quads
    assert receipt['excluded_clipped_or_special']==excluded and receipt['legacy_origin_assumptions']==0
failure=read('failures/unsigned-depth-verifier.json')
assert not failure['passed'] and len(failure['failures'])==32
checks=read('checks/report.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
identity=read('checks/source-identity.json')
payload=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(payload)==identity['sha256']==manifest['source_identity']
for name,content in data.items():
    if name.startswith('source/'):
        assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==47 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=212,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
print('PASS: five original5012 input/motion traces and all fifteen completed4K images; model/native/GPU verdicts remain receipts.')
