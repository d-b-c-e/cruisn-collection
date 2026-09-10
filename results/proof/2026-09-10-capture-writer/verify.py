"""Check the archived receipt identities and conclusions; raw executions remain local."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
assert manifest['schema']==1
for relative,digest in manifest['files'].items():
 file=(root/relative).resolve();assert file.is_relative_to(root)
 assert hashlib.sha256(file.read_bytes()).hexdigest()==digest,relative
load=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
export=load('paced-native-export.json');assert export['passed'] and export['patch_count']==159
assert export['candidate_sha256']==manifest['native_sha256']
checks=load('checks/report.json');assert checks['passed'] and len(checks['steps'])==96
assert checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
assert load('checks/unit-tests.json')==dict(errors=0,failures=0,passed=True,skipped=0,tests=290)
seven=load('seven-defaults.json');assert seven['passed'] and len(seven['cases'])==7 and all(c['passed'] for c in seven['cases'])
assert seven['candidate_sha256']==manifest['native_sha256'] and seven['source_identity']==manifest['source_identity']
for name,count in [('paced-usa',49),('paced-short',21),('paced-short-repeat',21),('paced-full-amazon',117)]:
 pixels=load(name+'-gl.json');assert pixels['passed'] and pixels['frames']==count and not pixels['different_frames']
 files=load(name+'-bmp-bytes.json');assert files['passed'] and len(files['files'])==count
 for pair in files['files'].values():
  a,b=pair.values() if isinstance(pair,dict) else pair;assert a==b
for name in ('paced-short','paced-short-repeat','paced-full-amazon','paced-long'):
 motion=load(name+'-motion.json');assert motion['passed'] and motion['camera_equal'] and motion['adc_times_equal']
resources=load('paced-full-amazon-resources.json');assert resources['passed'] and len(resources['files'])==10
assert all(v['reference']==v['candidate'] for v in resources['files'].values())
for name in ('async-usa-after','bulk-short-repeat','paced-long'):
 assert not load('runs/'+name+'.json')['passed'],name
fault=load('paced-long-timings.json');assert fault['passed'] and fault['expected_timeout']
assert fault['timings']['stall']['max_ms']>=4900 and any(w['phase']=='stall' for w in fault['waits'])
for name in ('paced-menu-usa','paced-menu-exotica'):
 menu=load('menus/'+name+'.json');assert menu['passed'] and menu['replay_passed'] and len(menu['menu'])==9 and len(menu['actions'])==1
upstream=load('upstream-refresh.json');assert upstream['open_prs']==291 and len(upstream['matched'])==4
print('PASS',len(manifest['files']),'hash-bound receipts; native/pixel/resource executions are not recomputed')
