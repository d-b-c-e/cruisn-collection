from pathlib import Path
import hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
i=read('source-identity.json');c=read('report.json')
assert hashlib.sha256(''.join(f'{k}\0{v}\n' for k,v in sorted(i['files'].items())).encode()).hexdigest()==i['sha256']==c['source_identity']==c['source_identity_after']
assert len(i['files'])==503 and c['passed'] and len(c['steps'])==132 and all(s['returncode']==0 for s in c['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=349,skipped=0,errors=0,failures=0)
for name,q,p in [('future-present-control3',19945019,False),('future-present-extended2',12133607,True),('future-present-extended3',19945019,True),('future-present-extended3-repeat',19945019,True)]:
    r=read(name+'-replay.json');f=r['scene']['result']['private_future']
    assert r['passed'] and f['passed'] and f['presented']==p and f['scenes']==6953 and f['quads']==q
    assert len(f['snapshots'])==5 and len(r['depth']['result']['snapshots'])==14
    for kind in ('motion','gl','resources','oracle'):assert read(name+'-'+kind+'.json')['passed']
    gl=read(name+'-gl.json');assert gl['frames']==233 and gl['common_original_frames']==117
    if not p:assert gl['original_identity'] and not gl['different_common_frames']
    assert all(a==b for a,b in read(name+'-resources.json')['files'].values())
    o=read(name+'-oracle.json');assert len(o['samples'])==5
    for s in o['samples']:assert s['passed'] and s['color_differences']==s['depth_differences']==0 and s['integrity']['other_page_unchanged']
rep=read('repeat.json');assert rep['passed'] and len(rep['completed'])==14 and len(rep['immediate'])==5 and all(v['rows']==6953 for v in rep['streams'].values())
v=read('comparison.json');assert v['passed'] and [p['frames'] for p in v['pairs']]==[233]*3 and [p['different'] for p in v['pairs']]==[84,33,0]
p=read('internal-preservation.json');assert p['passed'] and len(p['pairs'])==3 and all(x['passed'] and x['completed']==14 and x['immediate']==5 for x in p['pairs'])
e=read('native-export.json');assert e['passed'] and e['patch_count']==182 and e['candidate_sha256'].startswith('ca7e814b') and e['personal_sha256'].startswith('87d04de4')
print('PASS source/receipt consistency:349Python,47native,132commands; four original routes/resources,20 sampled insertion oracles,2334K repeat and33measured3x differences. Actual execution remains receipt; no useful3x/handover/default/deployment acceptance.')
