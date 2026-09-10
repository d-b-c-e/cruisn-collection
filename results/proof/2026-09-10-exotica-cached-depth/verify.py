from pathlib import Path
import csv,hashlib,json,re,statistics
root=Path(__file__).parent;read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for name,digest in read('manifest.json')['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
identity=read('source-identity.json');checks=read('checks.json');native=read('native-export.json');defaults=read('defaults.json')
payload=''.join(f'{k}\0{v}\n' for k,v in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']==checks['source_identity']==checks['source_identity_after']==defaults['source_identity']
assert checks['passed'] and len(checks['steps'])==115 and all(s['returncode']==0 for s in checks['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=321,skipped=0,errors=0,failures=0)
assert native['passed'] and native['patch_count']==166 and native['native_commit']=='7b432126ffed9c15fbdf7356a9ad8b6625d74231'
assert native['candidate_sha256']==defaults['candidate_sha256']=='d16e8b7a7c4f4ed377402017c4a7814d2c87d953f9def0872ff95b37d0fd964e'
assert native['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
assert defaults['passed'] and defaults['subset'] is None and len(defaults['cases'])==7 and not defaults['physical_force']
assert all(c['passed'] and c['telemetry']['passed'] for c in defaults['cases'])
assert len([c for c in defaults['cases'] if 'force_gate' in c])==4 and all(c['force_gate']['passed'] for c in defaults['cases'] if 'force_gate' in c)
cases=read('evidence.json')['cases'];assert len(cases)==15
images=source_verified=depth_verified=0
for name,case in cases.items():
 for path,data in case['reports'].items():
  r=data['receipt'];assert r.get('passed',True),path
  if path.endswith('-gl.json'):assert not r['different_frames'];images+=r['frames']
  if path.endswith('-motion.json'):assert r['adc_times_equal'] and r['camera_equal']
 for line in case['acknowledgments']:
  m=re.fullmatch(r'MIDZ_HOST_SOURCE_CACHE_RESULT mode=2 verified=(\d+) hits=(\d+) misses=(\d+)',line)
  if m:
   n,hits,misses=map(int,m.groups());assert n==hits+misses;source_verified+=n
  m=re.fullmatch(r'MIDZ_HOST_EARLY_DEPTH_RESULT mode=2 tested=(\d+) verified=(\d+) skipped=(\d+)',line)
  if m:
   n,v,skipped=map(int,m.groups());assert n==v and not skipped;depth_verified+=v
assert images==542 and source_verified==10204 and depth_verified==29794639
for name in ['cached-full-verify','cached-full-both','cached-full-repeat']:
 r=cases[name]['reports'][name+'-7187-oracle.json']['receipt'];assert r['passed'] and r['original_context']['exact_context']
cache=read('cache-snapshots.json');assert cache['passed'] and len(cache['snapshots'])==7
assert 'snapshots=7 descriptors=35724 frontiers=686 negative=693 binding_changes=7' in cache['stdout']
depth=read('depth-snapshots.json');assert depth['passed'] and len(depth['cases'])==14
assert sum(c['native']['quads'] for c in depth['cases'])==45340
assert all(c['passed'] and all(a==b for a,b in c['files'].values()) for c in depth['cases'])
with (root/'scene-cost.csv').open(encoding='utf-8',newline='') as stream:costs=list(csv.DictReader(stream))
means={}
for name in ['cached5072-off','cached5072-both','cached5072-repeat','cached-nogl','written-nogl3']:
 rows=[r for r in costs if r['run']==name];assert len(rows)==2457
 values=[sum(float(r[k]) for k in ('source_us','assembly_us','hash_us','materials_us'))/1000 for r in rows if int(r['frame'])>3501 and float(r['snapshot_us'])<1000]
 means[name]=statistics.mean(values);print(name,'mean CPU scene',round(means[name],3),'ms')
assert means['cached5072-both']<means['cached5072-off'] and means['cached5072-repeat']<means['cached5072-off']
with (root/'frame-clock.csv').open(encoding='utf-8',newline='') as stream:clocks=list(csv.DictReader(stream))
speeds={}
for name in means:
 rows={int(r['frame']):r for r in clocks if r['run']==name};assert set(rows)=={3501,5000,5100,5990}
 a,b=rows[3501],rows[5990]
 speeds[name]=100*(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
 print(name,'measured emulation speed',round(speeds[name],2),'%')
assert speeds['cached5072-both']>speeds['cached5072-off'] and speeds['cached-nogl']>speeds['written-nogl3']
print('PASS15 trial receipts,10,204 full source comparisons,29,794,639 exact depth decisions,542 paired4K images,all7defaults and selected CPU/clock measurements. Raw GPU/resource/route bytes remain external receipts.')
