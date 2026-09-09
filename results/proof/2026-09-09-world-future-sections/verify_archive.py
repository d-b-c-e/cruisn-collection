"""Recompute published scalar, route, timing, telemetry and selected pixel proof.

Raw ROM/model/texture/placement and hardware capture checks remain receipts.
Pillow is required for the four archived full-resolution gameplay images.
"""
import csv,hashlib,importlib.util,io,json,math,sys,tempfile,zipfile
from collections import Counter
from pathlib import Path
from PIL import Image,ImageChops

root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['files'])
    data={n:z.read(n) for n in z.namelist()}
for n,digest in manifest['files'].items():assert sha(data[n])==digest,n
read=lambda n:json.loads(data[n])
rows=lambda n:list(csv.DictReader(io.StringIO(data[n].decode())))
def percentile(values):
    v=sorted(map(float,values));assert all(math.isfinite(x) and x>=0 for x in v)
    return dict(maximum=v[-1],**{f'p{p}':v[min(len(v)-1,int(len(v)*p/100))] for p in (50,95,99)})
phases=('guard_us','prepare_us','pack_us','quad_log_us','submit_us')
counts=('pending','unsupported','distance','decoded','quads')
metrics=read('receipts/performance-final.json');signatures={};inputs=[]
for name,metric in metrics.items():
    prefix='matrix/'+name+'/'
    s=rows(prefix+'world-host-scenes.csv');f=rows(prefix+'frames.csv')
    assert read(prefix+'report.json')['passed']
    keys=[(int(r['frame']),int(r['page'])) for r in s]
    assert keys==sorted(set(keys)) and len(s)==3731
    for r in s:
        assert abs(sum(float(r[p]) for p in phases)-float(r['microseconds']))<.01
        assert len(r['quads_hash'])==16 and all(c in '0123456789abcdef' for c in r['quads_hash'])
        assert r['quad_trace']=='0'
    sig=[[int(r['frame']),int(r['page']),*(int(r[t]) for t in counts),r['quads_hash']] for r in s]
    signatures[name]=sha(json.dumps(sig).encode())
    m=metric['scene'];assert signatures[name]==m['scene_signature_sha256']
    assert {k:sum(int(r[k]) for r in s) for k in counts}==m['totals']
    assert percentile(r['microseconds'] for r in s)==m['host_microseconds']
    assert {p:percentile(r[p] for r in s) for p in (*phases,'previous_scene_log_us')}==m['phases']
    assert percentile(r['future_us'] for r in s)==metric['future_us']
    assert sum(int(r['future_unbound']) for r in s)==metric['unbound']
    unbound=[r for r in s if int(r['future_unbound'])]
    if name=='native-pending3':assert not unbound
    else:
        # Late resource invalidation is retained, not mistaken for zero missing
        # materials because the four earlier snapshot oracles had none.
        assert len(unbound)==118 and metric['unbound']==49088
        assert all(int(r['future_unbound'])==416 and 9025<=int(r['frame'])<=9259 for r in unbound)
    assert [int(r['frame']) for r in f]==list(range(1,9270))
    fields=[k for k in f[0] if k not in ('host_seconds','speed_percent')]
    inputs.append((fields,[tuple(r[k] for k in fields) for r in f]))
    for file in ('world-camera.csv','world-adc.csv'):
        assert data[prefix+file]==data['matrix/native-pending3/'+file]
    interval=f[1799:9260];host=[float(r['host_seconds']) for r in interval]
    assert all(math.isfinite(v) for v in host) and all(a<b for a,b in zip(host,host[1:]))
    ratio=(float(interval[-1]['emulated_seconds'])-float(interval[0]['emulated_seconds']))/(host[-1]-host[0])
    assert ratio==metric['timing']['emulation_ratio'] and ratio>=.99
assert all(i==inputs[0] for i in inputs)
assert signatures['native-future3']==signatures['native-future3-repeat']==signatures['native-observe3']
assert len({signatures[n] for n in ('native-pending3','native-future2','native-future3')})==3
for name in ['future3-repeat','future2-vs3','pending-native-control','pending-oracle','native-math','descriptor-check','frontier-check-v1','snapshot-check','integrity-check']:
    assert read('receipts/'+name+'.json')['passed'],name
assert len(read('receipts/future2-vs3.json')['gl']['different_frames'])==16
assert read('receipts/future3-repeat.json')['gl']['frames']==31
assert read('receipts/visual-review.json')['passed'] is False
assert read('receipts/world25-descriptor-check.json')['passed'] is False
assert read('receipts/road-codec-check.json')['passed'] is True
membership=read('scalars/world25-membership.json');states=Counter()
assert len(membership)==2686 and read('receipts/world25-membership-check.json')['passed']
for r in membership:
    state=0x2000 if r['control']&4 and r['tag_low']>r['limit'] else 0x1000
    assert state==r['actual_state'];states[state]+=1
assert states=={0x2000:2296,0x1000:390}
for a,b,frame,receipt in [('hillside-pending3','hillside-future2',2880,'pending3-vs-future2-gl'),('mountain-future2','mountain-future3',6720,'future2-vs3'),('tunnel-pending3','tunnel-future3',4408,'integrity-check')]:
    left=Image.open(io.BytesIO(data['images/'+a+'.png'])).convert('RGB')
    right=Image.open(io.BytesIO(data['images/'+b+'.png'])).convert('RGB')
    assert left.size==right.size==(3824,2073)
    channels=ImageChops.difference(left,right).split()
    mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
    changed=left.width*left.height-mask.histogram()[0]
    report=read('receipts/'+receipt+'.json')
    gl=report.get('gl',report)
    expected=next(r for r in gl['pixel_changes'] if r['frame']==frame)
    assert changed==expected['changed_pixels'] and changed>0
    assert list(mask.getbbox())==expected['bounds_xyxy_exclusive']
alloc=read('scalars/allocations.json');excluded=Counter();eligible=compared=0
assert [r['serial'] for r in alloc]==list(range(1,8223))
for r in alloc:
    metadata=r['metadata'];kind=(metadata>>8)&15
    if kind in (10,11):excluded[kind]+=1;continue
    expected=0x2000|((metadata>>16)&15)|int(bool(metadata&0xf000))|{3:1<<21,9:1<<21,6:1<<31,7:1<<22}.get(kind,0)
    assert expected==r['flags'] and metadata&65535==r['meta']
    signed=metadata if metadata<0x80000000 else metadata-0x100000000
    assert signed>>20==r['override_index']
    material=list(r['lookup'])
    if r['override_index']>=0 and 0<=r['override_lookup']<0x80000000:material[0]=r['override_lookup']
    assert material==r['materials']
    compared+=1;eligible+=not bool(expected&0x861)
assert compared==6823 and eligible==5405 and excluded=={10:67,11:1332}
frontiers=read('scalars/frontiers.json');assert len(frontiers)==166
assert Counter(r['stage'] for r in frontiers)=={1:52,2:114}
for r in frontiers:
    expected={d['id'] for d in r['listing'] if d['slot']>r['stage']+4 or d['slot']==r['stage']+4 and d['ordinal']>=r['cursor_ordinal']}
    assert expected==set(r['later_allocations'])
    receipt=next(c for c in read('receipts/frontier-check-v1.json')['results'] if c['frame']==r['frame'])
    assert receipt['passed'] and receipt['expected']==receipt['observed']==len(expected)
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==reg['source_identity']==manifest['source_identity']
assert len(checks['steps'])==42 and all(s['returncode']==0 for s in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=202,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==24
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='0f947fd500385cbab10bd68a857703f2659d7dcdfc1b8334bcae52d5cdc4b0d1'
with tempfile.TemporaryDirectory(prefix='cruisn-future-proof-') as temporary:
    extracted=Path(temporary)
    for n,p in data.items():
        if n.startswith(('tools/','regressions/')):
            destination=extracted/n
            assert destination.resolve().is_relative_to(extracted.resolve())
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(p)
    sys.path.insert(0,str(extracted/'tools'))
    def module(name):
        spec=importlib.util.spec_from_file_location('archived_'+name,extracted/'tools'/(name+'.py'))
        result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
    drivetrain=module('analyze_drivetrain');force=module('analyze_force_gate');force_count=0
    for case,expected in zip(plan['cases'],reg['cases']):
        assert case['id']==expected['id'] and expected['passed']
        path=extracted/'regressions'/case['id'];config=case['telemetry'];memory=path/config['memory']
        observed=drivetrain.analyze(path,memory)
        observed['coverage_passed']=observed['game_state_samples']>=config.get('minimum_active_frames',500) and observed['wire']['maximum_speed_mph']>=config.get('minimum_speed_mph',10)
        assert json.loads(json.dumps(observed))==expected['telemetry'],case['id']
        if config.get('force_gate_game'):
            actual=force.analyze(path,memory,config['force_gate_game'],config.get('force_gate_policy','driving'),config.get('force_polarity',False))
            assert json.loads(json.dumps(actual))==expected['force_gate'],case['id'];force_count+=1
    assert force_count==4
print('PASS: five full Germany route/timing/scenery-fingerprint controls, three selected 4K pixel comparisons, 6823 scalar descriptors, 166 partial frontiers, 2686 World2.5 membership decisions and seven telemetry/four force checks. Tunnel visual FAIL and initial World2.5 allocation-state FAIL retained. Full placement, geometry/resources, remaining GL, native/math/build results are receipts. Roads, comprehensive occlusion/handover and cross-game 3x remain incomplete.')
