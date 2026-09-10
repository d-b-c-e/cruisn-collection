"""Recompute scalar evidence; GPU execution remains a hash-bound receipt."""
from pathlib import Path
import csv,hashlib,json,re
root=Path(__file__).parent
def read(n):return json.loads((root/n).read_text(encoding='utf-8'))
def rows(n):
    with (root/n).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
for name,digest in read('manifest.json')['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
identity=read('checks/source-identity.json');checks=read('checks/report.json');change=read('source-changes.json')
assert hashlib.sha256(''.join(f'{k}\0{v}\n' for k,v in sorted(identity['files'].items())).encode()).hexdigest()==identity['sha256']==checks['source_identity']==checks['source_identity_after']==change['current_identity']
assert set(change['files'])=={'gpu/zeus_depth.py','harness/verify_zeus_depth_domain.py','harness/verify_zeus_depth_mirror.py','harness/local_checks.py'}
assert change['previous_identity']=='a3d78d50fb5a045fa77c0b19657c3f209970eaac2ab08aa197c0c1e94bc541f2'
assert checks['passed'] and len(checks['steps'])==129 and all(x['returncode']==0 for x in checks['steps'])
assert read('checks/unit-tests.json')==dict(passed=True,tests=332,skipped=0,errors=0,failures=0)
domain=read('checks/zeus-depth-domain.json');mirror=read('checks/zeus-depth-mirror.json')
assert domain['passed'] and domain['original_depth_values']==1<<24 and len(domain['cases'])==3
assert all(c['original_color_equal'] for c in domain['cases'])
assert [c['red_pixels'] for c in domain['cases']]==[domain['adjacent_ties']+1,1<<24,1<<24]
assert mirror['passed'] and len(mirror['cases'])==72 and sum(c['steps'] for c in mirror['cases'])==360
assert all(c['passed'] and len(c['color_sha256'])==5 for c in mirror['cases'])
assert {(c['scale'],c['page']) for c in mirror['cases']}=={(1,0),(1,400),(4,0),(4,400)}
for n in ('naive-failure.json','naive-diagnostic.json','fixture-blank-failure.json','fixture-restoration-failure.json'):assert not read(n)['passed']
assert read('naive-diagnostic.json')['different_pixels']['count']==2
for mode,expected in [('stock',99.99),('observe',94.90),('draw',93.06)]:
    result=read(mode+'/performance.json');assert result['passed'] and result['whole_run_speed_percent']==expected
    assert result['motion']['passed'] and result['motion']['camera_equal'] and result['motion']['adc_times_equal']
    text='\n'.join(read(mode+'/speed.json')['lines']);assert float(re.search(r'Average speed: ([0-9.]+)%',text)[1])==expected
    clock=rows(mode+'/clock.csv');assert len(clock)==8860 and all(int(r['frame'])==i for i,r in enumerate(clock,1))
    assert all(float(a['host_seconds'])<float(b['host_seconds']) for a,b in zip(clock,clock[1:]))
    for interval in result['intervals']:
        a,b=clock[interval['first_frame']-1],clock[interval['last_frame']-1]
        host=float(b['host_seconds'])-float(a['host_seconds']);emu=float(b['emulated_seconds'])-float(a['emulated_seconds'])
        assert abs(host-interval['host_seconds'])<1e-9 and abs(emu/host-interval['emulation_ratio'])<1e-9
    if mode!='stock':
        scenes=rows(mode+'/scenes.csv');assert len(scenes)==5290 and sum(int(r['quads']) for r in scenes)==15907490
        assert all(r['guest_cycles']=='0' for r in scenes)
observer=rows('observe/scenes.csv');draw=rows('draw/scenes.csv')
assert all(all(a[k]==b[k] for k in ('scene','frame','quads','hash')) for a,b in zip(observer,draw))
active=rows('draw/active.csv');assert len(active)==5290 and sum(int(r['quads']) for r in active)==970889
cost=read('observer-cost.json')
for key,value in cost['timings'].items():assert abs(sum(float(r[key]) for r in observer[1:])/5289-value['mean'])<1e-8
print('PASS 16,777,216-depth and 72-material GPU receipts, 129 local checks, three full replay clocks and unchanged ordered scene fingerprints. Performance remains open; no live D32F renderer or farther-distance acceptance.')
