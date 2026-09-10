from pathlib import Path
import hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
m=read('manifest.json')
for n,h in m['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h
baseline=root.parent/'2026-09-10-upstream-refresh/all-prs.json'
assert hashlib.sha256(baseline.read_bytes()).hexdigest()==m['baseline_sha256']
old={p['number']:p for p in json.loads(baseline.read_text(encoding='utf-8'))}
current=read('heads.json');s=read('summary.json')
assert len(current)==len({p['number'] for p in current})==s['open_prs']==293
changed={p['number'] for p in current if p['number'] not in old or p['head']!=old[p['number']]['headRefOid']}
assert changed=={p['number'] for p in s['changed_prs']}=={16090,16096,16097}
def relevant(p):return 'zeus' in p.lower() or p.startswith('src/devices/cpu/tms320c3x/') or p=='src/devices/video/poly.h'
assert s['master']=='607f9dc340bff276bb61f1357d3915e8d53ac556'
assert len(s['main_commits'])==3 and not any(map(relevant,s['main_files']))
assert not any(relevant(f) for p in s['changed_prs'] for f in p['files'])
expected={6515,13138,16021,16094}
assert {p['number'] for p in old.values() if any(map(relevant,p['files']))}==expected
assert all(next(p for p in current if p['number']==n)['head']==old[n]['headRefOid'] for n in expected)
print('PASS293 inventoried heads, three changed/new PR file lists, three main commits, unchanged four Zeus heads. Prior complete file inventories remain the baseline.')
