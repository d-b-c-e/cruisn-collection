"""Recompute public route and selected-pixel proof; retain raw-resource limits."""
from pathlib import Path
from decimal import Decimal
import csv,hashlib,io,json,zipfile,zlib
import numpy as np
from PIL import Image,ImageChops

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
    trace=rows(name);assert [int(r['frame']) for r in trace]==list(range(1,len(trace)+1))
    return [(int(r['frame']),Decimal(r['emulated_seconds']),tuple((k,v) for k,v in r.items() if k.startswith(':'))) for r in trace]


def picture(name):
    r=read(name)
    if r['encoding']=='png':im=Image.open(io.BytesIO(data[r['archive_file']])).convert('RGB')
    else:
        assert r['encoding']=='rgb-xor-zlib'
        base=Image.open(io.BytesIO(data[r['base_file']])).convert('RGB')
        delta=zlib.decompress(data[r['archive_file']]);assert len(delta)==3840*2160*3
        rgb=np.bitwise_xor(np.frombuffer(base.tobytes(),np.uint8),np.frombuffer(delta,np.uint8)).tobytes()
        im=Image.frombytes('RGB',(3840,2160),rgb)
    assert im.size==(3840,2160) and sha(im.tobytes())==r['rgb_sha256']
    return im


def equal(a,b):return ImageChops.difference(a,b).getbbox() is None


dense=('margin-72s-legacy','margin-72s-page','margin-72s-repeat','sky-72s-off','sky-72s-repeat','sky-72s-repeat-again')
specs=[(n,'amazon',7290,7198,7228,1) for n in dense]
specs += [(n,'amazon',8860,1800,8760,60) for n in ('sky-full-amazon','sky-full-amazon-repeat-v2')]
specs.append(('sky-hongkong-enabled','hongkong',6000,5400,5420,1))
images={}
for name,game,end,first,last,every in specs:
    prefix='runs/'+name+'/';original='original/'+game+'/'
    report=read(prefix+'report.json');invocation=read(prefix+'invocation.json')
    assert inputs(prefix+'frames.csv')==inputs(original+'frames.csv')[:end]
    for file in ('exotica-camera.csv','exotica-adc.csv'):
        reference=[r for r in rows(original+file) if int(r['frame'])<end]
        actual=rows(prefix+file)
        first_motion,last_motion=int(reference[0]['frame']),int(reference[-1]['frame'])
        assert int(actual[0]['frame'])==first_motion and int(actual[-1]['frame'])>=last_motion
        assert [r for r in actual if int(r['frame'])<=last_motion]==reference
    complete=rows(prefix+'captures.csv')
    assert [int(c['completed_frame']) for c in complete]==list(range(first,last+1,every))
    assert all(c['completed_frame']==c['last_received_frame'] and c['dropped_messages']=='0' and (int(c['width']),int(c['height']))==(3840,2160) for c in complete)
    build='margin' if name.startswith('margin-') else 'sky'
    assert invocation['executable_sha256']==read('receipts/'+build+'-native-export.json')['candidate_sha256']
    assert invocation['environment']['MIDV_FFB']=='0' and invocation['returncode']==0 and not invocation['error']
    if name in dense:
        assert not report['passed'] and not report.get('error')
        assert report['comparison']['input_or_time_mismatches']==0 and report['comparison']['pixel_mismatches']>0
        assert invocation['environment']['MIDZ_GL_NATIVE']=='1'
        oracle=read('receipts/'+name+'-cpu.json')
        assert oracle['passed'] and all(oracle[k]['differing_pixels']==0 and oracle[k]['pixels']==1048576 for k in ('color','depth'))
        for frame in (7200,7214,7215):images[(name,frame)]=picture(prefix+f'frame-{frame}.json')
    else:assert report['passed']
    resource=read('receipts/'+name+'-resources.json')
    assert resource['passed'] and len(resource['files'])==10
    assert all(v['reference']==v['candidate'] for v in resource['files'].values())
    palette=report['zeus_palette']['result'];assert palette['guard']==1 and palette['conflicts']==palette['flushes']
    margin=report['zeus_margin_clear']['result'];assert margin['expanded']<=margin['clears']
    if name.startswith('sky-'):
        sky=report['zeus_sky']['result'];enabled=int(name!='sky-72s-off')
        assert sky['enabled']==enabled and sky['accepted']<=sky['groups'] and sky['copied']<=sky['accepted']*8
        if enabled and game=='amazon':assert sky['copied']>0

for frame in (7200,7214,7215):
    legacy,page,page_repeat,off,sky,repeat=(images[(name,frame)] for name in dense)
    assert equal(page,page_repeat) and equal(page,off) and equal(sky,repeat)
    for a,b in ((legacy,page),(off,sky)):
        assert equal(a.crop((768,0,3072,2160)),b.crop((768,0,3072,2160)))
    assert not equal(page,sky)
assert not equal(images[('margin-72s-legacy',7215)],images[('sky-72s-repeat',7215)])
for name,count in [('margin-72s-legacy',31),('margin-72s-repeat',31),('sky-72s-off',31),('sky-72s-repeat-again',31),('sky-full-amazon-repeat-v2',117)]:
    r=read('receipts/'+name+'-gl.json');assert r['passed'] and r['frames']==count
for name in ('sky-full-amazon','sky-full-amazon-repeat-v2','sky-hongkong-enabled'):
    assert all(r['interior_changes']==0 for r in read('receipts/'+name+'-gl-shared.json')['details'])
for file,count in [('exotica-camera.csv',7060),('exotica-adc.csv',21180)]:
    actual=rows('runs/sky-full-amazon/'+file)
    assert len(actual)==count and actual==rows('runs/sky-full-amazon-repeat-v2/'+file)
    assert int(actual[0]['frame'])==1800 and int(actual[-1]['frame'])==8859
for name in ('sky-full-amazon','sky-hongkong-enabled'):
    failure=read('receipts/'+name+'-motion-interval-failure.json')
    assert not failure['passed']
failure=read('failures/first-full-repeat/report.json')
assert not failure['passed'] and failure['error']=='renderer fell back after losing its stream'
failed_captures=rows('failures/first-full-repeat/captures.csv')
assert len(failed_captures)==112 and failed_captures[-1]['completed_frame']=='8460'
assert sum(r['dropped_messages']=='0' for r in failed_captures)==111
assert failed_captures[-1]['dropped_messages']=='1'
assert b'consumer timeout' in data['failures/first-full-repeat/stderr.log']
for frame in (3500,4700,5410):assert not read(f'receipts/sky-hongkong-{frame}.json')['passed']
assert not read('receipts/margin-gpu-initial.json')['passed']
for name in ('margin-gpu-v2.json','sky-gpu-initial.json','sky-native-final-oracle.json','sky-recorded-margin-oracle.json'):
    assert read('receipts/'+name)['passed']
material=read('receipts/material-snapshot-audit.json')['cases']
assert sum(r['models'] for r in material)==1686
assert sum(len(r['model_snapshot_mismatches']) for r in material)==6
assert sum(r['palette_checks']['checked'] for r in material)==1600
assert all(not r['palette_snapshot_mismatches'] for r in material)
depth=read('receipts/future-depth-audit.json')['cases'][0]
assert depth['frame']==3500 and depth['multipliers'][2]['centers_above_depth24']==1425
lifetime=read('receipts/future-model-lifetime.json')
assert lifetime['counts']['parsed_model_bindings']==970 and not lifetime['errors']
assert all(r['counts']['checked_bindings']==r['counts']['unchanged']==970 for r in lifetime['later_snapshots'])
assert sum(r['counts']['later_actual_equal_earlier_wave'] for r in lifetime['later_snapshots'])==401
checks=read('checks/report.json');identity=read('checks/source-identity.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==428
for name,content in data.items():
    if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==91 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=281,errors=0,failures=0,skipped=0)
regressions=read('regressions/report.json')
assert regressions['passed'] and len(regressions['cases'])==7 and regressions['source_identity']==manifest['source_identity']
assert regressions['candidate_sha256']==read('receipts/sky-native-export.json')['candidate_sha256']
for case in regressions['cases']:assert case['passed'] and read('regressions/'+case['id']+'.json')['passed']
print('PASS: nine original input/motion traces and selected4K margin/panorama pixels. Complete image sequences, geometry/resources/CPU/GPU/build/seven-default gates are receipts; retained failures and wider coverage limits remain explicit.')
