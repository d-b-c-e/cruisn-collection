"""Recompute public scalar evidence; raw resources and pixels remain local."""
from pathlib import Path
import csv,hashlib,json,re,statistics
root=Path(__file__).parent
def read(n):return json.loads((root/n).read_text(encoding='utf-8'))
def rows(n):
    with (root/n).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
manifest=read('manifest.json')
for name,digest in manifest['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
identity=read('checks/source-identity.json');checks=read('checks/report.json');defaults=read('defaults.json');native=read('native-export.json')
payload=''.join(f'{k}\0{v}\n' for k,v in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']==checks['source_identity']==checks['source_identity_after']==defaults['source_identity']
assert checks['passed'] and len(checks['steps'])==127 and all(s['returncode']==0 for s in checks['steps'])
assert read('checks/unit-tests.json')==dict(passed=True,tests=332,skipped=0,errors=0,failures=0)
assert native['passed'] and native['patch_count']==176 and native['native_commit']=='50a6eaa3d1f233f51d1c0174b6858a09487e9120'
assert native['candidate_sha256']==defaults['candidate_sha256']=='a4e4cd4dc060e068ae4e4f3c29f9c8abc853bdc28420958ee797f924742581de'
assert native['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
assert defaults['passed'] and defaults['subset'] is None and len(defaults['cases'])==7 and not defaults['physical_force']
assert all(c['passed'] and c['telemetry']['passed'] and c['telemetry']['coverage_passed'] for c in defaults['cases'])
force=[c['force_gate'] for c in defaults['cases'] if 'force_gate' in c]
assert len(force)==4 and all(c['passed'] for c in force)
all_rows={};capture_total=0
for name,case in read('cases.json').items():
    cpu=rows(name+'/exotica-active-scenes.csv');gpu=rows(name+'/exotica-active-gpu.csv');fences=rows(name+'/exotica-host-fences.csv')
    all_rows[name]=cpu
    assert len(cpu)==len(gpu)==len(fences)==case['scenes']
    assert sum(int(x['quads']) for x in cpu)==case['quads']
    assert len({x['scene'] for x in cpu})==len(cpu)
    assert cpu[0]['seal_pages']=='4096'
    mode=1 if name=='observe' else 2
    for c,g,f in zip(cpu,gpu,fences):
        assert c['scene']==g['scene']==f['scene'] and c['frame']==g['frame']
        assert c['quads']==g['quads'] and c['ready_frame']==f['ready_frame'] and c['sealed_frame']==f['end_frame']
        assert int(c['ready_frame'])-int(c['frame']) in (0,1) and c['guest_cycles']=='0'
        assert int(g['mode'])==mode and g['height']=='4096'
        assert 0<=int(c['already_submitted'])<=int(c['candidates'])<=int(c['objects'])<=4096
        assert 0<=int(c['instances'])+int(c['excluded_raster'])<=int(c['candidates'])-int(c['already_submitted'])
        assert 0<=int(c['seal_pages'])<=4096 and int(c['seal_verified'])==int(name=='verify' or int(c['frame']) in case['snapshot_frames'])
        assert int(g['snapshot'])==int(int(c['frame']) in case['snapshot_frames'])
    ack=(root/name/'acknowledgments.log').read_text(encoding='utf-8')
    assert re.findall(r'^MIDZ_HOST_ACTIVE=(\d+)$',ack,re.M)==[str(mode)]
    for tag in ('SEALED','RESOURCE_LEASE','RAM_MODELS','SEAL_PAGES'):
        assert re.findall(r'^MIDZ_HOST_ACTIVE_'+tag+r'=(\d+)$',ack,re.M)==['1']
    assert re.findall(r'^MIDZ_HOST_ACTIVE_RESULT complete=(\d+) scenes=(\d+) quads=(\d+) remaining=(\d+)$',ack,re.M)==[('1',str(len(cpu)),str(case['quads']),'0')]
    assert re.findall(r'^MIDZ_HOST_ACTIVE_GPU_RESULT complete=(\d+) scenes=(\d+) quads=(\d+)$',ack,re.M)==[('1',str(len(cpu)),str(case['quads']))]
    writer=re.findall(r'^MIDZ_HOST_ACTIVE_WRITER submitted=(\d+) written=(\d+) failed=(\d+) rejected=(\d+)',ack,re.M)
    assert writer==[(str(4*len(case['snapshot_frames'])),str(4*len(case['snapshot_frames'])),'0','0')]
    r=read(name+'/run.json')['receipt'];assert r['passed'] and r['comparison']['passed']
    active=r['exotica_host_scene']['result']['active_margins']
    assert active['passed'] and active['scenes']==len(cpu) and active['quads']==case['quads']
    assert all(s['original_depth_unchanged'] and s['outside_color_unchanged'] and s['resource_lease']['passed'] for s in active['snapshots'])
    motion=read(name+'/motion.json');assert motion['passed'] and motion['camera_equal'] and motion['adc_times_equal']
    resources=read(name+'/resources.json');assert resources['passed'] and len(resources['files'])==10
    assert all(pair[0]==pair[1] for pair in resources['files'].values())
    gl=read(name+'/gl.json')
    if name=='verify':
        # This pair is intentionally against the no-draw control; optimized-vs-old
        # equality is a separate byte-identity receipt, not this changed picture.
        assert gl['frames']==25 and len(gl['different_frames'])==25 and not gl['size_mismatches']
    else:assert gl['passed'] and not gl['different_frames']
    capture_total+=gl['frames']
    assert all(x['size']==[3840,2160] for x in r['evidence']['gl_captures']['files'].values())
keys=set(all_rows['full'][0])-{'assembly_us','materials_us','seal_us','lease_us'}
assert all(all(a[k]==b[k] for k in keys) for a,b in zip(all_rows['full'],all_rows['repeat']))
for name in ('full','repeat','observe'):
    cpu=all_rows[name]
    assert len(cpu)==5290 and sum(int(r['quads']) for r in cpu)==970889
    assert sum(int(r['excluded_raster']) for r in cpu)==55 and sum(int(r['ram_models']) for r in cpu)==0
    assert sum(int(r['camera_advanced']) for r in cpu)==57 and sum(int(r['bindings_advanced']) for r in cpu)==45
assert max(int(r['seal_pages']) for r in all_rows['verify'][1:])==4
assert sum(int(r['seal_pages']) for r in all_rows['verify'])==11499
assert capture_total==397
raw=read('raw-identity.json');assert raw['passed'] and len(raw['cases'])==4
assert [len(c['files']) for c in raw['cases']]==[51,51,17,51]
assert read('verification-identity.json')['passed']
assert all(not c['passed'] for c in read('failures.json').values())
print('PASS 397 completed 4K capture receipts, 2457 full texture-image verification receipts, repeated 5290 scenes/970889 ordered quads, seven default receipts and final local identity.')
print('Original route/resources/pixels, full geometry, build and force outcomes remain receipts; current-distance margins only. Raw resources are not in this archive.')
