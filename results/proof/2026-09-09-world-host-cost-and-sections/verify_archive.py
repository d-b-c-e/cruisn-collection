"""Recompute the ROM-free World host-cost milestone; keep limitations explicit."""
import csv,hashlib,importlib.util,io,json,math,sys,tempfile,zipfile
from collections import Counter,defaultdict
from pathlib import Path

root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as z:
    assert set(z.namelist())==set(manifest['files'])
    data={n:z.read(n) for n in z.namelist()}
for n,digest in manifest['files'].items():assert sha(data[n])==digest,n
read=lambda n:json.loads(data[n])
rows=lambda n:list(csv.DictReader(io.StringIO(data[n].decode())))
cost=read('receipts/cost-comparison-v2.json')
assert cost['passed'] and cost['summary_performance_passed']
assert not cost['performance']['detailed3']['passed']
def percentile(values):
    v=sorted(map(float,values));assert all(math.isfinite(x) and x>=0 for x in v)
    return dict(maximum=v[-1],**{f'p{p}':v[min(len(v)-1,int(len(v)*p/100))] for p in (50,95,99)})
phases=('guard_us','prepare_us','pack_us','quad_log_us','submit_us')
counts=('pending','unsupported','distance','decoded','quads')
signatures={};inputs=[]
for name,metrics in cost['metrics'].items():
    base='cost/'+name+'/'
    s=rows(base+'world-host-scenes.csv');f=rows(base+'frames.csv')
    assert read(base+'report.json')['passed']
    keys=[(int(r['frame']),int(r['page'])) for r in s]
    assert keys==sorted(set(keys)) and len(s)==3731
    for r in s:
        assert abs(sum(float(r[p]) for p in phases)-float(r['microseconds']))<.01
        assert len(r['quads_hash'])==16 and all(c in '0123456789abcdef' for c in r['quads_hash'])
    sig=[[int(r['frame']),int(r['page']),*(int(r[t]) for t in counts),r['quads_hash']] for r in s]
    signatures[name]=sha(json.dumps(sig).encode())
    assert signatures[name]==metrics['scene_signature_sha256']
    assert sum(int(r['quads']) for r in s)==metrics['quads']
    assert percentile(r['microseconds'] for r in s)==metrics['costs']
    assert {p:percentile(r[p] for r in s) for p in (*phases,'previous_scene_log_us')}==metrics['phases']
    assert [int(r['frame']) for r in f]==list(range(1,9270))
    fields=[k for k in f[0] if k not in ('host_seconds','speed_percent')]
    inputs.append((fields,[tuple(r[k] for k in fields) for r in f]))
    for n in ('world-camera.csv','world-adc.csv'):assert data[base+n]==data['cost/summary3/'+n]
    interval=f[1799:9260]
    host=[float(r['host_seconds']) for r in interval]
    assert all(math.isfinite(v) for v in host) and all(a<b for a,b in zip(host,host[1:]))
    ratio=(float(interval[-1]['emulated_seconds'])-float(interval[0]['emulated_seconds']))/(host[-1]-host[0])
    assert ratio==metrics['emulation_ratio'] and (ratio>=.99)==cost['performance'][name]['passed']
assert all(i==inputs[0] for i in inputs)
assert len({s for n,s in signatures.items() if n!='summary2'})==1
assert signatures['summary2']!=signatures['summary3']
for n in ('old3-equal','trace-toggle','summary-repeat','sparse2-vs3'):
    assert read('receipts/'+n+'.json')['passed'] # Completed GL/full geometry remain receipts.
comparison=read('receipts/binding-comparisons.json')
assert not comparison['bindings-full']['allocator_coverage_complete']
assert not comparison['bindings-v2']['allocator_coverage_complete']
assert comparison['bindings-v3']['allocator_coverage_complete']
binding=read('bindings/values.json');by_serial=defaultdict(list);producers=Counter()
for r in binding['writes']:by_serial[r['serial']].append(r);producers[(r['field'],r['pc'])]+=1
assert [r['serial'] for r in binding['objects']]==list(range(1,8223))
initial=0
for r in binding['objects']:
    for field in (16,17):
        writes=[w for w in by_serial[r['serial']] if w['field']==field]
        early=[w for w in writes if w['phase']==0]
        assert len(early)==1 and early[0]['value']==r['lookup'][field-16]
        assert early[0]['pc']==(0x6266 if field==16 else 0x6269)
        assert writes[-1]['value']==r['ready'][field-16]
        initial+=1
assert initial==16444 and len(binding['writes'])==16854
assert [dict(field=f,pc=p,writes=n) for (f,p),n in sorted(producers.items())]==read('receipts/bindings-v3-check.json')['producers']
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
assert len(checks['steps'])==39 and all(s['returncode']==0 for s in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=199,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==24
a=read('receipts/regression-source-identity.json');b=read('receipts/current-source-identity.json')
delta=read('receipts/regression-source-delta-final.json')
assert a['sha256']==reg['source_identity']==delta['regression_source_identity']
assert b['sha256']==manifest['source_identity']==delta['current_identity']
assert sorted(k for k in a['files'].keys()|b['files'].keys() if a['files'].get(k)!=b['files'].get(k))==delta['changed_files']
assert delta['changed_files']==['harness/analyze_world_bindings.py','lua/world_section_capture.lua','tests/test_world_bindings.py']
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='41b0fdf35edf3c61ec2448721a5d283061f1e310c794028a0ec1e83fd5c01690'
with tempfile.TemporaryDirectory(prefix='cruisn-world-proof-') as temporary:
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
    drivetrain=module('analyze_drivetrain');force=module('analyze_force_gate')
    from scenery_c31 import F
    yaw=module('verify_world_sections').yaw_matrix
    vectors=read('math/world-yaw-vectors.json')['vectors'];assert len(vectors)==137
    for v in vectors:assert yaw(F(v['mantissa'],v['exponent']),v['constants'])==v['matrix']
    force_count=0
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
print('PASS: five scene/timing/input controls, 137 yaw vectors, 16444 initial material values plus 410 later writes, seven telemetry/four force verdicts. Detailed timing FAIL and incomplete early binding coverage retained. GL, raw geometry/resources/placement/ownership/build results remain receipts; no new distance or physical FFB acceptance.')
