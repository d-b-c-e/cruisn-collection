"""Recompute declared evidence; raw game resources and full geometry stay local."""
from pathlib import Path
import csv,io,json,hashlib,zipfile,tempfile,sys,importlib.util
from decimal import Decimal
from PIL import Image,ImageChops
root=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['files'])
    data={n:z.read(n) for n in z.namelist()}
for name,digest in manifest['files'].items():assert sha(data[name])==digest,name
read=lambda n:json.loads(data[n]);rows=lambda n:list(csv.DictReader(io.StringIO(data[n].decode())))
original=rows('original/frames.csv');fields=[k for k in original[0] if k not in ('host_seconds','speed_percent')]
assert len(original)==5012
images={};scenes_by_run={}
counters=['pending','unsupported','near','far','projection','decoded','quads']
def signature(scenes):
    return [[r['frame'],r['time'],r['page'],*[r[k] for k in counters],r['quads_hash'],
             *sorted((k,int(v)) for k,v in r.items() if k.startswith('future_') and k!='future_new_sections' and int(v))]
            for r in scenes]
for name in manifest['runs']:
    prefix='runs/'+name+'/';resource='resource' in name;end=4502 if resource else 5012
    report=read(prefix+'report.json');assert report['passed'] and report['comparison']['passed']
    frames=rows(prefix+'frames.csv');assert [int(v['frame']) for v in frames]==list(range(1,end+1))
    assert [[v[k] for k in fields] for v in frames]==[[v[k] for k in fields] for v in original[:end]]
    reference='resource-control' if resource else 'control'
    for file in ['usa-camera.csv','usa-adc.csv']:assert data[prefix+file]==data['runs/'+reference+'/'+file],name
    if prefix+'usa-host-scenes.csv' in data:
        scenes=rows(prefix+'usa-host-scenes.csv');scenes_by_run[name]=scenes
        keys=[(int(r['frame']),Decimal(r['time']),int(r['page'])) for r in scenes]
        assert len(set(keys))==len(keys) and all(a[0]<b[0] and a[1]<b[1] for a,b in zip(keys,keys[1:]))
        for r in scenes:
            assert int(r['pending'])+int(r.get('future_ready',0))==sum(int(r[k]) for k in counters[1:6])
            assert int(r['future_definitions'])==sum(int(r[k]) for k in ('future_special','future_unbound','future_deferred','future_ready'))
            assert int(r['future_ready'])<=16384 and int(r['future_definitions'])<=65536
    captures=read(prefix+'captures.json');wanted=[4500] if resource else [3600,3700,4700,4800]
    assert [int(c['completed_frame']) for c in captures]==wanted
    for c in captures:
        assert int(c['dropped_messages'])==0
        image=Image.open(io.BytesIO(data['images/'+c['sha256']+'.png'])).convert('RGB')
        assert image.size==(3824,2073)
        images[name,int(c['completed_frame'])]=image
for prefix,camera,adc in [('control',3211,9633),('resource-control',2701,8103)]:
    assert len(rows('runs/'+prefix+'/usa-camera.csv'))==camera and len(rows('runs/'+prefix+'/usa-adc.csv'))==adc
for name in ['repeat3','detailed3','cache3','cache-repeat3','tail3','tail-repeat3']:
    assert signature(scenes_by_run[name])==signature(scenes_by_run['future3'])
    assert len(scenes_by_run[name])==750 and sum(int(r['quads']) for r in scenes_by_run[name])==6445085
for name in ['cache2','tail2']:assert signature(scenes_by_run[name])==signature(scenes_by_run['future2'])
old=rows('original/pending-scenes.csv');assert len(old)==755
assert signature([r for r in old if 3501<=int(r['frame'])<=4999])==signature(scenes_by_run['pending3'])
assert not read('failures/pending-old-new.json')['passed']
comparisons=[('control','future1','control-future1',10),('future1','future2','future1-2',13),
 ('future2','future3','future2-3',3),('future3','repeat3','future3-repeat',0),
 ('future3','detailed3','future3-detailed',0),('future3','cache3','future3-cache3',0),
 ('cache3','cache-repeat3','cache3-repeat',0),('future2','cache2','future2-cache2',0),
 ('future3','tail3','future3-tail3',0),('tail3','tail-repeat3','tail3-repeat',0),('future2','tail2','future2-tail2',0)]
for a,b,name,changed in comparisons:
    receipt=read('receipts/'+name+'.json');assert receipt['passed'] and receipt['gl']['frames']==16
    assert len(receipt['gl']['different_frames'])==changed
    for frame in (3600,3700,4700,4800):
        x,y=images[a,frame],images[b,frame]
        c=ImageChops.difference(x,y).split();mask=ImageChops.lighter(ImageChops.lighter(c[0],c[1]),c[2])
        pixels=x.width*x.height-mask.histogram()[0]
        row=next((v for v in receipt['gl']['pixel_changes'] if v['frame']==frame),None)
        assert pixels==(row['changed_pixels'] if row else 0)
        if row:assert list(mask.getbbox())==row['bounds_xyxy_exclusive']
for file in ['original-resources','tail-original-resources']:
    resources=read('receipts/'+file+'.json');assert resources['passed'] and resources['total_bytes']==153833626
    assert all(r['equal'] and r['sha256'][0]==r['sha256'][1] for r in resources['files'].values())
for file,count in [('offline-future-oracle',5),('runtime-future-oracle',4),('cached-runtime-oracle',4),('tail-runtime-oracle',4)]:
    oracle=read('receipts/'+file+'.json');assert oracle['passed'] and len(oracle['snapshots'])==count
    assert all(len(r['trials'])==3 and all(t['passed'] for t in r['trials']) for r in oracle['snapshots'])
    if count==4:assert all(r['trials'][2]['runtime_passed'] for r in oracle['snapshots'])
for file,count in [('native-export',143),('native-cache-export',144),('native-tail-export',145)]:
    receipt=read('receipts/'+file+'.json');assert receipt['passed'] and receipt['patch_count']==count
    assert receipt['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
for file,names in [('timing',['future3','repeat3']),('cache-timing',['cache3','cache-repeat3']),('tail-timing',['tail3','tail-repeat3','tail2'])]:
    receipts=read('receipts/'+file+'.json')
    for name in names:
        timing=receipts[name].get('timing',receipts[name]);trace=rows('runs/'+name+'/frames.csv')
        a,b=trace[3499],trace[4999]
        ratio=(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
        assert abs(ratio-timing['emulation_ratio'])<1e-12 and ratio<.99 # The performance failure remains explicit.
        if 'host' in receipts[name]:
            values=sorted(float(r['microseconds']) for r in scenes_by_run[name])
            p99=values[min(len(values)-1,int(len(values)*99/100))]
            expected=receipts[name]['host']['phases']['microseconds']
            assert abs(p99-expected['p99'])<1e-6 and max(values)==expected['maximum']
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==reg['source_identity']==manifest['source_identity']
identity=read('checks/source-identity.json')
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==341
for name,content in data.items():
    if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==53 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=227,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='37c0a4cef63b2bc56ef8d8daaccd4b75e457621633e3c93f228570cda6d0dc93'
with tempfile.TemporaryDirectory(prefix='cruisn-usa-future-proof-') as temporary:
    extracted=Path(temporary)
    assert extracted.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
    for name,content in data.items():
        if name.startswith(('tools/','regressions/')):
            path=extracted/name;assert path.resolve().is_relative_to(extracted.resolve())
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    sys.path.insert(0,str(extracted/'tools'))
    def module(name):
        spec=importlib.util.spec_from_file_location('archived_'+name,extracted/'tools'/(name+'.py'))
        result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
    drivetrain=module('analyze_drivetrain');force=module('analyze_force_gate');force_count=0
    for case,expected in zip(plan['cases'],reg['cases']):
        assert case['id']==expected['id'] and expected['passed']
        path=extracted/'regressions'/case['id'];config=case['telemetry'];memory=path/config['memory']
        actual=drivetrain.analyze(path,memory)
        actual['coverage_passed']=actual['game_state_samples']>=config.get('minimum_active_frames',500) and actual['wire']['maximum_speed_mph']>=config.get('minimum_speed_mph',10)
        assert json.loads(json.dumps(actual))==expected['telemetry'],case['id']
        if config.get('force_gate_game'):
            actual=force.analyze(path,memory,config['force_gate_game'],config.get('force_gate_policy','driving'),config.get('force_polarity',False))
            assert json.loads(json.dumps(actual))==expected['force_gate'],case['id'];force_count+=1
    assert force_count==4
print('PASS: 17 input/motion traces, repeated host fingerprints, selected4K pixels, timing limits and seven telemetry/four software force checks; raw geometry/resources/builds remain receipts.')
