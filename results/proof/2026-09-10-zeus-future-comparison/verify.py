from pathlib import Path
import hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
for name,quads in [('wide-future-full2',12133607),('wide-future-full3',19945019),('wide-future-full3-repeat',19945019)]:
    r=read(name+'-replay.json');f=r['scene']['result']['private_future']
    assert r['passed'] and f['passed'] and f['scenes']==6953 and f['quads']==quads
    s=read(name+'-frames.json');assert s['count']==8849 and s['first']==2 and s['last']==8850 and s['exact_sequence'] and len(s['snapshots'])==14
    for kind in ('motion','gl','resources','oracle'):assert read(name+'-'+kind+'.json')['passed']
    assert all(a==b for a,b in read(name+'-resources.json')['files'].values())
    o=read(name+'-oracle.json');assert len(o['samples'])==5
    for s in o['samples']:
        assert s['passed'] and s['color_differences']==s['depth_differences']==0
        assert s['integrity']['other_page_unchanged'] and s['actual_sha256']==s['integrity']['sha256'][2:]
repeat=read('repeat.json');assert repeat['passed'] and len(repeat['completed'])==14 and len(repeat['immediate'])==5
assert all(r['rows']==6953 for r in repeat['streams'].values())
v=read('visual-comparison.json');assert v['passed'] and len(v['frames'])==14
changed=[]
for f in v['frames']:
    assert f['hashes'][2]==f['hashes'][3]
    p=next(p for p in f['pairs'] if p['left']==2 and p['right']==3)
    assert p['rgb_pixels']==p['alpha_pixels']==0
    p=next(p for p in f['pairs'] if p['left']==1 and p['right']==2)
    if p['rgb_pixels']:changed.append(f['frame'])
assert changed==[3500,3901,5073,8401]
e=read('native-export.json');assert e['passed'] and e['patch_count']==181 and e['candidate_sha256'].startswith('24b18ba8')
print('PASS receipt consistency: three full routes/resources,15 immediate oracles,3x repeat,14 sampled2x/3x equal colors. Raw execution remains receipt; no useful3x/presentation/handover/default acceptance.')
