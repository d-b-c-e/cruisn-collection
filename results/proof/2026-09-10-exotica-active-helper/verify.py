from pathlib import Path
import json,hashlib
r=Path(__file__).parent;read=lambda n:json.loads((r/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
i=read('source-identity.json');c=read('checks.json')
payload=''.join(f'{k}\0{v}\n' for k,v in sorted(i['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==i['sha256']==c['source_identity']==c['source_identity_after']
assert c['passed'] and len(c['steps'])==118 and all(s['returncode']==0 for s in c['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=321,skipped=0,errors=0,failures=0)
s=read('snapshots.json');assert s['passed'] and len(s['cases'])==14
assert all(row['passed'] and all(a==b for a,b in row['files'].values()) for row in s['cases'])
a=[x for x in s['cases'] if x['mode']=='active'];f=[x for x in s['cases'] if x['mode']=='future']
assert len(a)==len(f)==7 and sum(x['decisions'] for x in a)==2275
assert sum(x['native']['instances'] for x in a)==189 and sum(x['native']['quads'] for x in a)==1238
assert sum(x['native']['quads'] for x in f)==22670
l=read('live.json');assert l['passed'] and l['native']==dict(passed=True,lists=52,objects=4591,margin_candidates=814)
print('PASS canonical helper receipts:321Python/42native/118commands,4591live decisions,2275snapshot decisions,189active instances/1238quads,22670unchanged future quads. Raw native operands/geometry remain local; no new live MAME build.')
