from pathlib import Path
import hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
r=read('summary.json');heads={p['number']:p for p in read('heads.json')};old={p['number']:p for p in read('previous-heads.json')}
assert r['passed'] and len(heads)==r['open_prs']==292 and not r['main_relevant']
assert r['master']=='999a6334107a4d6a88c728781c00163c67af6054'
assert len(r['main_commits'])==1 and r['main_commits'][0]['sha']==r['master']
paths=('zeus','src/devices/cpu/tms320c3x/','src/devices/video/poly.h')
match=lambda files:[f for f in files if any(p in f.lower() for p in paths)]
assert not match(r['main_files'])
changed={n for n,p in heads.items() if n not in old or p['head']!=old[n]['head']}
assert changed=={p['number'] for p in r['changed_prs']}=={16098,16096,16090,16083}
for p in r['changed_prs']:assert p['head']==heads[p['number']]['head'] and not match(p['files']) and not p['relevant']
assert set(r['closed'])==set(old)-set(heads)=={16097,13444}
for n in (6515,13138,16021,16094):assert heads[n]['head']==old[n]['head']
print('PASS archived292-head inventory/delta/path selection; main and four changed/new heads contain no Zeus/C3x/poly files. Network execution and earlier unchanged-head full-path audit remain receipts.')
