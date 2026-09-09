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
original=rows('original/frames.csv');assert len(original)==6000
fields=[k for k in original[0] if k not in ('host_seconds','speed_percent')]
counters=('pending','future','future_definitions','unsupported','near','far','projection','material','decoded','pretrack','partial','deferred','quads')
phases=('guard_us','prepare_us','pack_us','log_us','submit_us')
images={};scenes_by_run={}
def signature(scenes):
    return [[int(r['frame']),r['time'],int(r['page']),int(r['multiplier']),int(r['future_enabled']),*(int(r[n]) for n in counters),r['quads_hash']] for r in scenes]
for name in manifest['runs']:
    prefix='runs/'+name+'/'
    report=read(prefix+'report.json');assert report['passed'] and report['comparison']['passed']
    resource=name.startswith('resource');end=5502 if resource else 6000
    trace=rows(prefix+'frames.csv');assert [int(r['frame']) for r in trace]==list(range(1,end+1))
    assert [[r[k] for k in fields] for r in trace]==[[r[k] for k in fields] for r in original[:end]]
    reference='resource-control-v2' if resource else 'control'
    for file,count in [('offroad-camera.csv',3701 if resource else 4191),('offroad-adc.csv',14804 if resource else 16764)]:
        assert data[prefix+file]==data['runs/'+reference+'/'+file]
        assert len(rows(prefix+file))==count
    if prefix+'offroad-host-scenes.csv' in data:
        scenes=rows(prefix+'offroad-host-scenes.csv');scenes_by_run[name]=scenes
        keys=[(int(r['frame']),Decimal(r['time']),int(r['page'])) for r in scenes]
        assert all(a[0]<b[0] and a[1]<b[1] for a,b in zip(keys,keys[1:]))
        for r in scenes:
            assert int(r['pending'])+int(r['future_definitions'])==sum(int(r[n]) for n in ('unsupported','near','far','projection','material','decoded'))
            assert 0<=int(r['future'])<=int(r['future_definitions'])<=32768
            assert int(r['pending'])<=1200
            assert int(r['multiplier']) in (1,2,3) and int(r['mode']) in (1,2)
            assert abs(sum(float(r[n]) for n in phases)-float(r['microseconds']))<.01
        if not resource:assert len(scenes)==1978
    if name not in manifest['visible_runs']:continue
    captures=rows(prefix+'captures.csv');expected=[5500] if resource else list(range(4000,5951,50))
    assert [int(c['completed_frame']) for c in captures]==expected
    assert all(int(c['completed_frame'])==int(c['last_received_frame']) and int(c['dropped_messages'])==0 and (int(c['width']),int(c['height']))==(3824,2073) for c in captures)
    chosen=read(prefix+'captures.json');wanted=[5500] if resource else [4000,4250,4600,5500]
    assert [int(c['completed_frame']) for c in chosen]==wanted
    for c in chosen:
        frame=int(c['completed_frame']);assert {k:v for k,v in c.items() if k!='sha256'}==next(v for v in captures if int(v['completed_frame'])==frame)
        image=Image.open(io.BytesIO(data['images/'+c['sha256']+'.png'])).convert('RGB');assert image.size==(3824,2073)
        images[name,frame]=image
for name in ('observe','draw3','repeat3','quiet3'):
    assert signature(scenes_by_run[name])==signature(scenes_by_run['draw3'])
    assert sum(int(r['quads']) for r in scenes_by_run[name])==2573619
    assert sum(int(r['partial']) for r in scenes_by_run[name])==7
    assert sum(int(r['pretrack']) for r in scenes_by_run[name])==52
comparisons=[('control','draw1','control-draw1',29),('draw1','draw2','draw1-draw2',40),('draw2','draw3','draw2-draw3',6),('draw3','repeat3','draw3-repeat3',0),('draw3','quiet3','draw3-quiet3',0)]
for a,b,name,changed in comparisons:
    receipt=read('receipts/'+name+'.json');assert receipt['passed'] and receipt['gl']['frames']==40
    assert len(receipt['gl']['different_frames'])==changed
    for frame in (4000,4250,4600,5500):
        x,y=images[a,frame],images[b,frame];channels=ImageChops.difference(x,y).split()
        mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]);pixels=x.width*x.height-mask.histogram()[0]
        record=next((r for r in receipt['gl']['pixel_changes'] if r['frame']==frame),None)
        assert pixels==(record['changed_pixels'] if record else 0)
        if record:assert list(mask.getbbox())==record['bounds_xyxy_exclusive']
timings=read('receipts/timings.json')
for name,r in timings.items():
    trace=rows('runs/'+name+'/frames.csv');a,b=trace[1799],trace[5989]
    speed=100*(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
    assert abs(speed-r['speed_percent'])<1e-10
    assert speed<80 if name=='repeat3' else speed>99
    if 'host' in r:
        values=sorted(float(v['microseconds']) for v in scenes_by_run[name]);expected=r['host']['phases']['microseconds']
        assert expected['maximum']==max(values) and expected['p99']==values[int(len(values)*.99)]
resource=read('receipts/original-resources.json');assert resource['passed'] and resource['total_bytes']==53802202
assert all(r['equal'] and r['sha256'][0]==r['sha256'][1] for r in resource['files'].values())
assert not read('failures/invalid-capture-interval.json')['passed']
oracle=read('receipts/observe-oracle.json');assert oracle['passed'] and len(oracle['snapshots'])==5 and sum(r['quads'] for r in oracle['snapshots'])==7402
export=read('receipts/native-export.json');assert export['passed'] and export['patch_count']==146
assert export['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
foundation=read('foundation/host-oracle-cached.json');assert foundation['passed'] and len(foundation['results'])==72 and sum(r['quads'] for r in foundation['results'])==50736
for name in ('future-final','prepared-early-final','prepared-middle-final','prepared-late-final','material-analysis'):assert read('foundation/'+name+'.json')['passed']
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==reg['source_identity']==manifest['source_identity']
identity=read('checks/source-identity.json')
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==367
for name,content in data.items():
    if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==63 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=247,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='c88ae4f260d663734bf9f582a90ca4488cfac154c90be9290bbb08e20b368d8d'
with tempfile.TemporaryDirectory(prefix='cruisn-offroad-host-proof-') as temporary:
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
print('PASS: nine input/motion traces, host fingerprints, selected4K pixels, timing including stalled repeat, seven telemetry/four software-force verdicts; raw resources/geometry/builds remain receipts.')
