"""Public scalar, selected-pixel and telemetry proof; raw resources stay local."""
from pathlib import Path
import csv
from decimal import Decimal
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import zipfile
from PIL import Image, ImageChops

root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as archive:
    assert len(archive.namelist())==len(set(archive.namelist()))
    assert set(archive.namelist())==set(manifest['files'])
    data={name:archive.read(name) for name in archive.namelist()}
for name,digest in manifest['files'].items():assert sha(data[name])==digest,name
read=lambda name:json.loads(data[name])
rows=lambda name:list(csv.DictReader(io.StringIO(data[name].decode())))

def inputs(name):
    trace=rows(name)
    assert [int(r['frame']) for r in trace]==list(range(1,len(trace)+1))
    return [(int(r['frame']),Decimal(r['emulated_seconds']),tuple((k,v) for k,v in r.items() if k.startswith(':'))) for r in trace]
original=inputs('original/frames.csv')[:6000]
control=rows('runs/control/exotica-camera.csv');adc=rows('runs/control/exotica-adc.csv')
assert len(control)==4191 and [int(r['frame']) for r in control]==list(range(1800,5991))
assert len(adc)==12573 and all(0x9c0000<=int(r['address'],16)<=0x9c000f for r in adc)
assert all(Decimal(b['time'])>=Decimal(a['time']) for a,b in zip(adc,adc[1:]))
images={}
for name in manifest['runs']:
    prefix='runs/'+name+'/'
    assert inputs(prefix+'frames.csv')==original
    assert rows(prefix+'exotica-camera.csv')==control
    assert rows(prefix+'exotica-adc.csv')==adc
    report=read(prefix+'report.json');assert report['passed']
    complete=rows(prefix+'captures.csv')
    assert [int(c['completed_frame']) for c in complete]==list(range(5400,5421))
    assert all(int(c['completed_frame'])==int(c['last_received_frame']) and int(c['dropped_messages'])==0 and (int(c['width']),int(c['height']))==(3840,2160) for c in complete)
    captures=read(prefix+'captures.json');assert [int(r['completed_frame']) for r in captures]==[5400,5410,5420]
    for row in captures:
        frame=int(row['completed_frame'])
        assert {k:v for k,v in row.items() if k!='sha256'}==next(v for v in complete if int(v['completed_frame'])==frame)
        im=Image.open(io.BytesIO(data['images/'+row['sha256']+'.png'])).convert('RGB');assert im.size==(3840,2160)
        if name=='control':images[frame]=im
        else:assert ImageChops.difference(images[frame],im).getbbox() is None

for name in ('section-canonical','section-repeat'):
    progress=rows('runs/'+name+'/exotica-section-progress.csv')
    assert len(progress)==4191 and [int(r['frame']) for r in progress]==list(range(1800,5991))
    for r in progress:
        assert int(r['starts'])-int(r['ends'])==bool(int(r['loading']))
        assert int(r['allocating'])<=bool(int(r['loading']))
        assert int(r['bank'])==0
    assert all(not int(r['loading']) and not int(r['allocating']) for r in progress)
    assert int(progress[-1]['ends'])==8
    receipt=read('runs/'+name+'/exotica-section-capture.json')
    assert receipt==dict(schema=1,complete=True,first=1800,last=5990,allocations=1135,sections=8,snapshots=6)
    oracle=read('receipts/'+name+'-future-final.json')
    assert oracle['passed'] and oracle['ordinary']==1079 and oracle['custom_excluded']==56
    assert oracle['initial_bindings']==2158 and oracle['overrides']==9 and oracle['live_partial_samples']==0
    assert len(oracle['snapshots'])==6 and all(r['native_verified'] and r['sections']==54 and r['ordinary']==6323 for r in oracle['snapshots'])
    assert sum(r['descriptors'] for r in oracle['snapshots'])==42882
    assert sum(r['actual_allocations'] for r in oracle['snapshots'])==6474
    assert sum(r['later_allocations'] for r in oracle['snapshots'])==2507
assert data['runs/section-canonical/exotica-section-progress.csv']==data['runs/section-repeat/exotica-section-progress.csv']
a=read('receipts/section-canonical-future-final.json');b=read('receipts/section-repeat-future-final.json')
assert a['sources']==b['sources'] and a['snapshots']==b['snapshots']
assert read('receipts/future-acceptance.json')['passed']
failure=read('failures/initial-type-summary.json');assert not failure['passed'] and failure['failures']==18
checks=read('checks/report.json');identity=read('checks/source-identity.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==392
for name,content in data.items():
    if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==72 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=263,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
print('PASS: five input/motion traces, three selected4K images per run and loader scalar boundaries. Descriptors/materials/rawresources/builds remain receipts; no new seven-default renewal or host drawing.')
