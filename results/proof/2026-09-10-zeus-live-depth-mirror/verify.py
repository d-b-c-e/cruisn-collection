"""Recompute public scalar evidence; raw game pixels/depth remain local receipts."""
from pathlib import Path
import csv,hashlib,json,re
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
def rows(n):
    with (root/n).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
identity=read('checks/source-identity.json');checks=read('checks/report.json');defaults=read('defaults.json');native=read('native-export.json')
assert hashlib.sha256(''.join(f'{k}\0{v}\n' for k,v in sorted(identity['files'].items())).encode()).hexdigest()==identity['sha256']==checks['source_identity']==checks['source_identity_after']==defaults['source_identity']
assert checks['passed'] and len(checks['steps'])==129 and all(s['returncode']==0 for s in checks['steps'])
assert read('checks/unit-tests.json')==dict(passed=True,tests=336,skipped=0,errors=0,failures=0)
shader=read('checks/zeus-depth-mirror.json');assert shader['passed'] and len(shader['cases'])==76 and sum(c['steps'] for c in shader['cases'])==380
assert read('checks/zeus-depth-domain.json')['passed']
assert native['passed'] and native['patch_count']==177 and native['native_commit']=='25228b19d59bf434817b998134a042637b16075b'
assert native['candidate_sha256']==defaults['candidate_sha256']=='2267c6502d17e6c8efe73d7a2daecda4e752267f26bcbf25af088bb3488f321f'
assert not defaults['passed'] and defaults['subset'] is None and len(defaults['cases'])==7 and not defaults['physical_force']
assert [c['id'] for c in defaults['cases'] if not c['passed']]==['usa-widescreen']
assert all(c['telemetry']['passed'] and c['telemetry']['coverage_passed'] for c in defaults['cases'])
retry=read('defaults-usa-retry.json');assert retry['passed'] and retry['subset']==['usa-widescreen'] and len(retry['cases'])==1
assert retry['source_identity']==defaults['source_identity'] and retry['candidate_sha256']==defaults['candidate_sha256'] and not retry['physical_force']
assert retry['cases'][0]['passed'] and retry['cases'][0]['telemetry']['passed'] and all(t['passed'] for t in retry['cases'][0]['timings'])
clock=rows('default-stall-clock.csv');assert [int(r['frame']) for r in clock]==list(range(1,5013))
worst=max((float(b['host_seconds'])-float(a['host_seconds']),int(b['frame'])) for a,b in zip(clock,clock[1:]))
assert worst[1]==1858 and 6.13<worst[0]<6.14
bad=next(c for c in defaults['cases'] if c['id']=='usa-widescreen')['timings'][0]
a,b=clock[bad['first_frame']-1],clock[bad['last_frame']-1]
ratio=(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
assert not bad['passed'] and abs(ratio-bad['emulation_ratio'])<1e-12
force=[c['force_gate'] for c in defaults['cases'] if 'force_gate' in c];assert len(force)==4 and all(c['passed'] for c in force)
all_rows={};captures=0;pairs=0
for name,case in read('cases.json').items():
    r=read(name+'/run.json')['receipt'];assert r['passed'] and r['comparison']['passed']
    gl=read(name+'/gl.json');assert gl['passed'] and gl['frames']==case['gl'] and not gl['different_frames'] and not gl['size_mismatches'];captures+=case['gl']
    assert all(row['size']==[3840,2160] for row in r['evidence']['gl_captures']['files'].values())
    motion=read(name+'/motion.json');assert motion['passed'] and motion['camera_equal'] and motion['adc_times_equal']
    resources=read(name+'/resources.json');assert resources['passed'] and len(resources['files'])==10 and all(a==b for a,b in resources['files'].values())
    ack=(root/name/'acknowledgments.log').read_text(encoding='utf-8')
    if name=='disabled':assert not r['zeus_depth_mirror']['enabled'] and 'MIDZ_DEPTH_MIRROR=' not in ack;continue
    data=rows(name+'/mirror.csv');all_rows[name]=data;assert [int(x['frame']) for x in data]==list(range(case['first'],case['last']+1))
    assert all(x['color_differences']=='0' and x['depth_differences']=='0' and x['height']=='4096' for x in data)
    assert all(int(a[k])<=int(b[k]) for a,b in zip(data,data[1:]) for k in ('batches','vertices','clears'))
    assert [int(x['frame']) for x in data if x['snapshot']=='1']==case['snapshots']
    result=r['zeus_depth_mirror']['result'];assert result['passed'] and result['frames']==len(data)
    assert [s['frame'] for s in result['snapshots']]==case['snapshots']
    assert all(s['passed'] and s['color_differences']==s['depth_differences']==0 and s['sha256'][0]==s['sha256'][1] for s in result['snapshots'])
    assert re.findall(r'^MIDZ_DEPTH_MIRROR_RESULT complete=(\d+) frames=(\d+) batches=(\d+) vertices=(\d+) clears=(\d+) snapshots=(\d+) remaining=(\d+)$',ack,re.M)==[('1',str(len(data)),str(result['batches']),str(result['vertices']),str(result['clears']),str(len(case['snapshots'])),'0')]
    n=4*len(case['snapshots']);assert re.findall(r'^MIDZ_DEPTH_MIRROR_WRITER submitted=(\d+) written=(\d+) failed=(\d+) rejected=(\d+)',ack,re.M)==[(str(n),str(n),'0','0')]
    pairs+=len(case['snapshots'])
repeat=read('repeat-identity.json');assert repeat['passed'] and len(repeat['files'])==36 and all(a==b for a,b in repeat['files'].values())
assert len(all_rows['full'])==len(all_rows['repeat'])==8849
assert all(all(a[k]==b[k] for k in repeat['compared_fields']) for a,b in zip(all_rows['full'],all_rows['repeat']))
assert all(not f['passed'] for f in read('failures.json').values())
assert captures==305 and pairs==29
print('PASS 305 completed4K/29 raw comparison receipts, 8849 repeated frame counters/36 raw hashes, 336 Python/129 local-command receipts. Default suite retains one timingFAIL; USA targeted retry separate. Original-only mirror; no farther scenery acceptance.')
