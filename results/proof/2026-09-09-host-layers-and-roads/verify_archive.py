"""Recompute publishable host-layer and road scalar proof; no ROMs required.

Requires Pillow. Raw geometry, projection, materials, builds and GPU fixtures
remain hash-bound receipts; this archive does not rerender whole game scenes.
"""
from pathlib import Path
import csv,hashlib,io,json,re,zipfile
from PIL import Image,ImageChops
root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['files'])
    data={n:z.read(n) for n in z.namelist()}
for name,digest in manifest['files'].items():assert sha(data[name])==digest,name
read=lambda n:json.loads(data[n])
rows=lambda n:list(csv.DictReader(io.StringIO(data[n].decode())))
reference=None;fingerprints=None
for name in ['legacy-v2','coverage-v2','both-v2','split-drain-small']:
    prefix='runs/'+name+'/'
    r=read(prefix+'report.json');assert r['passed'] and r['comparison']['passed']
    frames=rows(prefix+'frames.csv');assert [int(v['frame']) for v in frames]==list(range(1,4503))
    keys=[k for k in frames[0] if k not in ('host_seconds','speed_percent')]
    values=(keys,[[v[k] for k in keys] for v in frames])
    if reference is None:reference=values
    assert values==reference
    for file in ['world-camera.csv','world-adc.csv']:
        assert data[prefix+file]==data['runs/legacy-v2/'+file]
    scenes=rows(prefix+'world-host-scenes.csv')
    keys=['frame','page','quads','quads_hash']
    values=[[v[k] for k in keys] for v in scenes]
    if fingerprints is None:fingerprints=values
    assert values==fingerprints
    assert r['capture']['sha256']==read('receipts/pending-control.json')['capture']['sha256']
for name in ['legacy','split-v2','split-v3','split-drain']:
    assert read('failures/'+name+'.json')['passed'] is False
assert read('failures/split-v2.json')['capture_diagnostics']['captured_count']==41
assert read('failures/split-v3.json')['capture_diagnostics']['missing_frames']==[4500]
assert 'No display matches' in read('failures/split-drain.json')['error']
assert not read('receipts/gpu-before.json')['passed']
assert not read('receipts/gpu-after-v2.json')['passed'] # retained wrong synthetic dither flag; final check corrects it
assert read('receipts/coverage-vs-both.json')['passed'] and read('receipts/coverage-vs-both.json')['frames']==51
images=[Image.open(io.BytesIO(data['images/'+name+'-4408.png'])).convert('RGB') for name in ['pending','legacy','coverage']]
assert all(im.size==(3824,2073) for im in images)
def mask(a,b):return ImageChops.difference(a,b).convert('RGB').point(lambda p:255 if p else 0)
def binary(a,b):
    r,g,b=mask(a,b).split();return ImageChops.lighter(ImageChops.lighter(r,g),b)
before=binary(images[0],images[1]);after=binary(images[0],images[2])
assert before.histogram()[255]==3079 and after.histogram()[255]==139
assert ImageChops.subtract(after,before).getbbox() is None
total=far=unclipped=0
for name in ['road-tunnel','road-road-gap']:
    prefix='roads/'+name+'/'
    r=read(prefix+'replay.json');assert r['passed'] and r['comparison']['passed']
    selection=read(prefix+'selection.json');summary=read(prefix+'summary.json')
    assert summary['completed'] and summary['starts']==summary['projected']==len(selection)
    assert [r['call'] for r in selection]==list(range(1,len(selection)+1))
    for r in selection:
        extended=r['depth']>=r['threshold']
        assert 1<=r['metadata_selector']<=15 and r['slot']==r['metadata_selector']-1
        assert r['selected']==r['template' if extended else 'original']
        far+=extended;unclipped+=r['end_pc']==0x242;total+=1
    assert read('receipts/'+name+'-check.json')['passed']
assert (total,far,unclipped)==(23589,17821,21123)
alloc=read('roads/final-fields.json');assert len(alloc)==1332
for r in alloc:
    m=r['metadata'];assert (m>>8)&15==11
    flags=0x2000|((m>>16)&15)|int(bool(m&0xf000))|(1<<28)
    assert r['flags']==flags and r['meta']==(m&0xf000)|0x300
    assert r['tag']==r['initial_tag']|(1<<24)|((1<<25) if r['section_flags']&16 else 0)
assert not read('receipts/road-descriptors.json')['passed']
assert read('receipts/road-descriptors-v2.json')['passed']
boundary=read('receipts/drain-boundary.json');assert boundary['passed']
m=re.search(rb'MIDV capture drain: target=(\d+) presented=(\d+) wait_ms=(\d+) complete=(\d+)',data['receipts/drain-boundary-stdout.log'])
assert m and int(m[1])==298 and int(m[2])>=298 and 0<int(m[3])<=10000 and int(m[4])==1
checks=read('checks/report.json');assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(errors=0,failures=0,passed=True,skipped=0,tests=203)
gpu=read('checks/gpu-quality.json');assert gpu['passed'] and len(gpu['checks'])==32 and all(r['passed'] for r in gpu['checks'])
export=read('receipts/native-export.json');assert export['passed'] and export['patch_count']==138
assert export['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
print('PASS: selected 4K pixels, four input/ADC/fingerprint traces, road selection/final fields and capture-drain receipt. Full geometry/build/GPU checks remain receipts; no cross-game acceptance.')
