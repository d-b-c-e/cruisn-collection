from pathlib import Path
import hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
i=read('source-identity.json');c=read('report.json')
assert hashlib.sha256(''.join(f'{k}\0{v}\n' for k,v in sorted(i['files'].items())).encode()).hexdigest()==i['sha256']==c['source_identity']==c['source_identity_after']
assert len(i['files'])==503 and c['passed'] and len(c['steps'])==132 and all(s['returncode']==0 for s in c['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=348,skipped=0,errors=0,failures=0)
for name,scenes,quads,frames,captures in [('wide-future-observe1-guard',4120,835720,5989,7),('wide-future-full1',6953,2312876,8849,14),('wide-future-full-control3',6953,19945019,8849,14)]:
    r=read(name+'-replay.json');assert r['passed'] and r['scene']['result']['passed'] and r['depth']['result']['passed']
    future=r['scene']['result']['private_future'];assert future['passed'] and future['scenes']==scenes and future['quads']==quads
    rows=read(name+'-frames.json');assert rows['count']==frames and rows['exact_sequence'] and rows['first']==2 and rows['last']==frames+1 and len(rows['snapshots'])==captures
    if 'full1' not in name:assert all(int(s['color_differences'])==0 for s in rows['snapshots'])
    for kind in ('motion','gl','resources'):assert read(name+'-'+kind+'.json')['passed']
    assert all(a==b for a,b in read(name+'-resources.json')['files'].values())
for name,count in [('observe1',1),('draw1',5),('observe3',5)]:
    r=read(name+'-oracle.json');assert r['passed'] and len(r['samples'])==count
    for s in r['samples']:
        assert s['passed'] and s['color_differences']==s['depth_differences']==0
        assert s['integrity']['other_page_unchanged'] and s['actual_sha256']==s['integrity']['sha256'][2:]
        assert s['integrity']['width']==2736 and s['integrity']['height']==4096
assert not read('initial-failure.json')['passed']
e=read('native-export.json');assert e['passed'] and e['patch_count']==181 and e['candidate_sha256'].startswith('24b18ba8') and e['personal_sha256'].startswith('87d04de4')
assert read('zeus-wide-depth.json')['passed'] and read('zeus-depth-mirror.json')['passed']
print('PASS source/selected receipt consistency,348Python/47native/132commands, original resource hashes and eleven immediate insertion oracle receipts. Actual GPU/route/4K execution remains hash-bound; no visual/handover/default/deployment acceptance.')
