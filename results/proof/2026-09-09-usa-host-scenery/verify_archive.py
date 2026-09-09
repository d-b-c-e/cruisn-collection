"""Recompute declared USA host evidence; raw models/resources remain local."""
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
original=rows('original/frames.csv');fields=[k for k in original[0] if k not in ('host_seconds','speed_percent')]
assert len(original)==5012
images={};fingerprints=None
for name in ['control','draw1','draw2','draw3','repeat3','observe3-v3','resource-control','resource-draw3']:
    prefix='runs/'+name+'/'
    resource=name.startswith('resource');end=4502 if resource else 5012
    r=read(prefix+'report.json');assert r['passed'] and r['comparison']['passed']
    frames=rows(prefix+'frames.csv');assert [int(v['frame']) for v in frames]==list(range(1,end+1))
    assert [[v[k] for k in fields] for v in frames]==[[v[k] for k in fields] for v in original[:end]]
    reference='resource-control' if resource else 'control'
    for file in ['usa-camera.csv','usa-adc.csv']:assert data[prefix+file]==data['runs/'+reference+'/'+file]
    if name in ('draw2','draw3','repeat3','observe3-v3'):
        scenes=rows(prefix+'usa-host-scenes.csv');assert len(scenes)==755
        keys=['frame','time','page','pending','unsupported','near','far','projection','decoded','quads','quads_hash']
        values=[[r[k] for k in keys] for r in scenes]
        assert len({tuple(r[:3]) for r in values})==len(values)
        if fingerprints is None:fingerprints=values
        assert values==fingerprints and sum(int(r['quads']) for r in scenes)==168874
    captures=read(prefix+'captures.json');wanted=[4500] if resource else [3700,3800,4900]
    assert [int(c['completed_frame']) for c in captures]==wanted
    for c in captures:
        assert int(c['dropped_messages'])==0
        image=Image.open(io.BytesIO(data['images/'+c['sha256']+'.png'])).convert('RGB')
        assert image.size==(3824,2073)
        images[name,int(c['completed_frame'])]=image
for prefix,camera,adc in [('control',3211,9633),('resource-control',2701,8103)]:
    assert len(rows('runs/'+prefix+'/usa-camera.csv'))==camera and len(rows('runs/'+prefix+'/usa-adc.csv'))==adc
for a,b,changed in [('control','draw1',10),('draw1','draw2',12),('draw2','draw3',0),
                    ('draw3','repeat3',0),('control','observe3-v3',0),('observe3-v3','draw3',None)]:
    receipt=read('receipts/'+a+'-'+b+'.json');assert receipt['passed'] and receipt['gl']['frames']==16
    if changed is not None:assert len(receipt['gl']['different_frames'])==changed
    for frame in (3700,3800,4900):
        x,y=images[a,frame],images[b,frame]
        c=ImageChops.difference(x,y).split();mask=ImageChops.lighter(ImageChops.lighter(c[0],c[1]),c[2])
        pixels=x.width*x.height-mask.histogram()[0]
        row=next((v for v in receipt['gl']['pixel_changes'] if v['frame']==frame),None)
        assert pixels==(row['changed_pixels'] if row else 0)
        if row:assert list(mask.getbbox())==row['bounds_xyxy_exclusive']
for name in ['observe3-duplicate-fail','observe3-v2-oracle','allocator']:assert not read('failures/'+name+'.json')['passed']
resources=read('receipts/original-resources.json');assert resources['passed']
assert sum(r['size'] for r in resources['files'].values())==153833626
oracle=read('receipts/final-scene-oracle.json');assert oracle['passed'] and len(oracle['snapshots'])==3
assert all(len(r['trials'])==3 and all(t['passed'] for t in r['trials']) and r['trials'][2]['runtime_passed'] for r in oracle['snapshots'])
assert read('receipts/native-export.json')['passed'] and read('receipts/native-export.json')['patch_count']==142
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==reg['source_identity']==manifest['source_identity']
identity=read('checks/source-identity.json')
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==329
for name,content in data.items():
    if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==50 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=217,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='248aef7c5c56402ed117d52ef228cc3864d9f14dadbfaf654a025d4cb834f20b'
with tempfile.TemporaryDirectory(prefix='cruisn-usa-host-proof-') as temporary:
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
print('PASS: eight original input/motion traces, repeated host fingerprints, selected4K pixels and seven telemetry/four software force verdicts; geometry/resources/builds remain receipts.')
