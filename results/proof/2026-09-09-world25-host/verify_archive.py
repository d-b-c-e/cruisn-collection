"""Recompute the explicitly archived World2.5 evidence; raw resources stay local."""
from pathlib import Path
import csv,io,json,hashlib,zipfile,tempfile,sys,importlib.util
from PIL import Image,ImageChops
root=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['files'])
    data={n:z.read(n) for n in z.namelist()}
for name,digest in manifest['files'].items():assert sha(data[name])==digest,name
read=lambda n:json.loads(data[n]);rows=lambda n:list(csv.DictReader(io.StringIO(data[n].decode())))
reference=None;fingerprints=None
for name in ['control','future1','future2','future3','repeat3']:
    prefix='runs/'+name+'/'
    r=read(prefix+'report.json');assert r['passed'] and r['comparison']['passed']
    frames=rows(prefix+'frames.csv');assert [int(v['frame']) for v in frames]==list(range(1,6001))
    keys=[k for k in frames[0] if k not in ('host_seconds','speed_percent')]
    values=(keys,[[v[k] for k in keys] for v in frames])
    if reference is None:reference=values
    assert values==reference
    for file in ['world-camera.csv','world-adc.csv']:assert data[prefix+file]==data['runs/control/'+file]
    if name in ('future3','repeat3'):
        scenes=rows(prefix+'world-host-scenes.csv');assert len(scenes)==1666
        values=[[r[k] for k in ['frame','page','quads','quads_hash']] for r in scenes]
        if fingerprints is None:fingerprints=values
        assert values==fingerprints and sum(int(r['quads']) for r in scenes)==3773825
for file in ['world-camera.csv','world-adc.csv']:
    original=rows('original/'+file);candidate=rows('runs/control/'+file)
    assert [r for r in original if 1800<=int(r['frame'])<=5990]==candidate
    assert max(int(r['frame']) for r in original)==5998
assert len(rows('runs/control/world-camera.csv'))==4191 and len(rows('runs/control/world-adc.csv'))==12573
for file in ['usa-camera.csv','usa-adc.csv']:
    assert data['runs/usa-control/'+file]==data['runs/usa-codec-v4/'+file]
assert len(rows('runs/usa-control/usa-camera.csv'))==1751 and len(rows('runs/usa-control/usa-adc.csv'))==5253
usa_frames=[]
for name in ['usa-control','usa-codec-v4']:
    assert read('runs/'+name+'/report.json')['passed']
    frames=rows('runs/'+name+'/frames.csv');assert [int(r['frame']) for r in frames]==list(range(1,3553))
    keys=[k for k in frames[0] if k not in ('host_seconds','speed_percent')]
    usa_frames.append([[r[k] for k in keys] for r in frames])
assert usa_frames[0]==usa_frames[1]
usa=read('receipts/usa-model-oracle.json')
assert usa['passed'] and usa['projected']==5178 and usa['unclipped']==5068 and usa['quads']==44652
assert read('receipts/usa-v4-gl.json')['passed'] and read('receipts/usa-v4-motion.json')['passed']
reset=[r for r in rows('reset/scene-state.csv') if r['lead']!='11'];assert len(reset)==350
assert all(r['section']==r['lead']=='0' and r['far']=='80000' and r['table']==str(0xb665) for r in reset)
assert (reset[0]['frame'],reset[-1]['frame'])==('2602','3300')
for name in ['future1','guard-control','resources-off']:assert not read(f'failures/{name}.json')['passed']
for name in ['usa-codec','usa-codec-v2']:assert not read(f'failures/{name}-oracle.json')['passed']
assert not read('receipts/control-motion.json')['passed']
assert read('receipts/reference-common.json')['passed']
assert not read('receipts/oracle-broad-v2.json')['passed']
for name in ['resources','resources-motion','oracle-frontiers','oracle-world24','oracle-old','native-export']:
    assert read('receipts/'+name+'.json')['passed']
for receipt,frames,a,b,count in [('one-to-two',[4700],'future1','future2',18),
                                ('two-to-three',[4700,5900],'future2','future3',10)]:
    r=read('receipts/'+receipt+'.json');assert r['passed'] and len(r['gl']['different_frames'])==count
    for frame in frames:
        x,y=[Image.open(io.BytesIO(data[f'images/{name}-{frame}.png'])).convert('RGB') for name in (a,b)]
        assert x.size==y.size==(3824,2073)
        c=ImageChops.difference(x,y).split();mask=ImageChops.lighter(ImageChops.lighter(c[0],c[1]),c[2])
        row=next(v for v in r['gl']['pixel_changes'] if v['frame']==frame)
        assert x.width*x.height-mask.histogram()[0]==row['changed_pixels']
        assert list(mask.getbbox())==row['bounds_xyxy_exclusive']
repeat=read('receipts/repeat.json');assert repeat['passed'] and repeat['gl']['frames']==30 and repeat['host_scene_fingerprints_equal']
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==reg['source_identity']==manifest['source_identity']
assert len(checks['steps'])==44 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=206,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='a5d0fb417c2277346ae1c0742e82cf7a9ee5832fadde5ce5676f01a598a0ab43'
with tempfile.TemporaryDirectory(prefix='cruisn-world25-proof-') as temporary:
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
print('PASS: five6000 input/motion traces, reset scalars, repeated3x fingerprints, selected4K pixels and seven telemetry/four force verdicts; remaining checks are receipts.')
