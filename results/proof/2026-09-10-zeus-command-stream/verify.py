from pathlib import Path
import csv,hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
i=read('source-identity.json');c=read('report.json')
assert hashlib.sha256(''.join(f'{k}\0{v}\n' for k,v in sorted(i['files'].items())).encode()).hexdigest()==i['sha256']==c['source_identity']==c['source_identity_after']
assert len(i['files'])==500 and c['passed'] and len(c['steps'])==132 and all(s['returncode']==0 for s in c['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=345,skipped=0,errors=0,failures=0)
assert len(read('source-changes.json')['files'])==5
failure=read('initial-parser-failure.json');assert not failure['passed'] and failure['error']=='command journal record size'
a,b=read('first-journal.json'),read('checked-journal.json');assert a['passed'] and b['passed'] and a['sha256']==b['sha256']
assert a['commands']==3989 and a['upload_bytes']==9192 and a['record_counts']=={'1':3799,'2':186,'3':1,'5':1,'6':2}
for name in ('first','checked'):
    r=read(name+'-oracle.json');assert r['passed'] and len(r['cases'])==2
    for case in r['cases']:
        assert case['passed'] and case['color_differences']==case['depth_differences']==0 and case['actual_sha256']==case['expected_sha256']
        assert case['header']['width']==2736 and case['header']['height']==4096 and case['counters']==dict(quads=3799,sky_copies=0,clears=1,uploads=1)
for a,b in zip(read('first-oracle.json')['cases'],read('checked-oracle.json')['cases']):assert a['actual_sha256']==b['actual_sha256']
r=read('replay.json');assert r['passed'] and r['mirror']['result']['passed'] and r['mirror']['stream_frame']==5080
rows=list(csv.DictReader((root/'frames.csv').open(encoding='utf-8')));assert [int(r['frame']) for r in rows]==list(range(2,5991))
assert sum(int(r['snapshot']) for r in rows)==8 and all(int(r['color_differences'])==0 for r in rows)
assert all(read(n)['passed'] for n in ('motion.json','gl.json','resources.json','zeus-wide-depth.json','zeus-depth-mirror.json'))
e=read('native-export.json');assert e['passed'] and e['patch_count']==179 and e['candidate_sha256'].startswith('ebb8602d') and e['personal_sha256'].startswith('87d04de4')
print('PASS source/frame coverage, repeated3989-command journal hashes, retained failure and hash-bound345Python/47native/132command,25completed4K/original-route/resources,independent original/private page-playback receipts. No future or deployment acceptance.')
