"""Verify queue/clock evidence; raw graphics, game operands and build outputs stay local."""
from pathlib import Path
import csv,hashlib,json,re,statistics
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
def rows(n):
    with (root/n).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
manifest=read('manifest.json')
for name,digest in manifest['files'].items():
    path=(root/name).resolve();assert path.is_relative_to(root.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
identity=read('checks/source-identity.json');checks=read('checks/report.json')
payload=''.join(f'{n}\0{h}\n' for n,h in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']==manifest['source_identity']
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==identity['sha256']
assert len(checks['steps'])==109 and all(s['returncode']==0 for s in checks['steps'])
assert read('checks/unit-tests.json')==dict(passed=True,tests=315,skipped=0,errors=0,failures=0)
native=read('native-export.json');defaults=read('defaults.json')
assert native['passed'] and native['patch_count']==163
assert native['native_commit']=='99442f1a7b6ed6079a40d315feb067c03c89ddfa'
assert native['candidate_sha256']=='70a190d7bc732a42848644cfaf5becb777a749b3468699712d7f4219bf6a8c40'
assert native['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
assert defaults['passed'] and defaults['subset'] is None and len(defaults['cases'])==7 and not defaults['physical_force']
assert defaults['source_identity']==identity['sha256'] and defaults['candidate_sha256']==native['candidate_sha256']
assert all(c['passed'] and c['telemetry']['passed'] for c in defaults['cases'])
assert len([c for c in defaults['cases'] if 'force_gate' in c])==4
assert all(c['force_gate']['passed'] for c in defaults['cases'] if 'force_gate' in c)
labels=['5072-on3','5072-repeat3','5000-on3','5990-on3','5978-on3','5978-on1','5978-on2']
queues={};images=0
fields=['scene','frame','generation','pages','palettes','bytes','hash']
for label in labels:
    assert read(label+'/run.json')['passed'] and read(label+'/oracle.json')['passed'] and read(label+'/materials.json')['passed']
    motion=read(label+'/motion.json');assert motion['passed'] and motion['camera_samples']==[4191,4191]
    assert motion['actual_adc_reads']==[12573,12573] and motion['adc_times_equal']
    gl=read(label+'/gl.json');assert gl['passed'] and not gl['different_frames']
    images+=21 if label=='5000-on3' else 17
    resources=read(label+'/resources.json');assert resources['passed'] and len(resources['files'])==10
    assert all(a==b for a,b in resources['files'].values())
    producer=rows(label+'/materials.csv');consumer=rows(label+'/materials-gpu.csv');scenes=rows(label+'/scenes.csv')
    assert len(producer)==len(consumer)==len(scenes)==2457
    for i,(p,c,s) in enumerate(zip(producer,consumer,scenes),1):
        assert all(p[k]==c[k] for k in fields) and int(p['generation'])==i
        assert p['scene']==s['scene'] and p['frame']==s['frame'] and int(s['guest_cycles'])==0
        assert int(p['bytes'])==96+int(p['pages'])*4100+int(p['palettes'])*1032
        assert 0<=int(p['pages'])<=4096 and 0<=int(p['palettes'])<=4096
    assert int(producer[0]['pages'])==4096
    text=(root/label/'acknowledgments.log').read_text(encoding='utf-8')
    assert re.findall(r'MIDZ_HOST_MATERIALS_RESULT queued=(\d+) hash=(\w+)',text)==[('2457',producer[-1]['hash'])]
    assert re.findall(r'MIDZ_HOST_MATERIALS_GPU_RESULT complete=(\d+) received=(\d+) snapshots=(\d+) hash=(\w+)',text)==[('1','2457','1',producer[-1]['hash'])]
    queues[label]=producer
    clock={int(r['frame']):r for r in rows(label+'/clock.csv')}
    a,b=clock[3501],clock[5990]
    speed=100*(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
    print(f'{label}: 2457 queued scenes; observed interval {speed:.2f}% with diagnostics')
assert images==123
assert all(all(a[k]==b[k] for k in fields) for a,b in zip(queues['5072-on3'],queues['5072-repeat3']))
for name in ('private-nogl-bounds3','private-nogl-material3','private-material-full3'):
    assert read(name+'/run.json')['passed']
    motion=read(name+'/motion.json');assert motion['passed'] and motion['adc_times_equal']
    full=name=='private-material-full3'
    assert motion['camera_samples']==[7060,7060] if full else motion['camera_samples']==[4191,4191]
    assert motion['actual_adc_reads']==[21180,21180] if full else motion['actual_adc_reads']==[12573,12573]
    if name!='private-nogl-bounds3':
        a,b=rows(name+'/materials.csv'),rows(name+'/materials-gpu.csv')
        assert len(a)==len(b)==(5290 if full else 2457)
        assert all(all(x[k]==y[k] for k in fields) for x,y in zip(a,b))
        assert read(name+'/materials.json')['passed']
    if not full:
        clock={int(r['frame']):r for r in rows(name+'/clock.csv')};a,b=clock[3501],clock[5990]
        speed=100*(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
        print(f'{name}: {speed:.2f}% with regular raw snapshots but no GL snapshots')
for name in ('6330-oracle','7187-source-oracle','8760-oracle'):
    assert read('private-material-full3/'+name+'.json')['passed']
failure=read('private-material-full3/7187-context-coverage-failure.json')
assert not read('private-material-full3/7187-oracle.json')['passed'] and not failure['passed']
assert failure['requested_frame']==7187 and sorted(failure['original_model_frames'])==['7199','7200']
assert read('private-material-full3/gl.json')['passed'] and read('private-material-full3/gl.json')['frames']==117
assert read('private-material-full3/resources.json')['passed']
print(f'PASS {len(manifest["files"])} evidence hashes, 17199 queue updates and receipts for 123 matching4K captures. No raw-pixel or geometry recomputation.')
print('Extended coverage:5290 full-drive material updates,117 more matching4K images; original-context7187 coverage failure retained.')
