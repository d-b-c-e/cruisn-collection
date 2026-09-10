from pathlib import Path
import csv,hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
i=read('source-identity.json');c=read('report.json')
assert hashlib.sha256(''.join(f'{k}\0{v}\n' for k,v in sorted(i['files'].items())).encode()).hexdigest()==i['sha256']==c['source_identity']==c['source_identity_after']
assert c['passed'] and len(c['steps'])==132 and all(s['returncode']==0 for s in c['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=342,skipped=0,errors=0,failures=0)
assert len(read('source-changes.json')['files'])==4
tables={}
for name in ('compat','control','repeat'):
    r=read(name+'.json');m=r['mirror'];v=m['result'];assert r['passed'] and v['passed']
    assert m['mode']==('observe' if name=='compat' else 'wide') and v['pixel_depth_policy_verified']==(name=='compat')
    rows=list(csv.DictReader((root/(name+'.csv')).open(encoding='utf-8')));tables[name]=rows
    assert [int(r['frame']) for r in rows]==list(range(2,5991)) and len(v['snapshots'])==7
    previous=(0,0,0)
    for row in rows:
        current=tuple(int(row[k]) for k in ('vertices','clears','batches'));assert all(a<=b for a,b in zip(previous,current));previous=current
        assert int(row['color_differences'])==0 and (name!='compat' or int(row['depth_differences'])==0)
    for snapshot in v['snapshots']:
        row=rows[snapshot['frame']-2];assert int(row['snapshot'])==1 and snapshot['color_differences']==0
        assert snapshot['depth_differences']==int(row['depth_differences']) and snapshot['passed']
    assert all(read(name+'-'+check+'.json')['passed'] for check in ('motion','gl','resources'))
repeat=read('repeat-identity.json');assert repeat['passed'] and len(repeat['files'])==28 and all(a==b for a,b in repeat['files'].values())
for a,b in zip(tables['control'],tables['repeat']):assert all(a[k]==b[k] for k in repeat['compared_fields'])
e=read('native-export.json');assert e['passed'] and e['patch_count']==178 and e['candidate_sha256'].startswith('05b132f9') and e['personal_sha256'].startswith('87d04de4')
assert all(read(n)['passed'] for n in ('zeus-wide-depth.json','zeus-depth-domain.json','zeus-depth-mirror.json'))
print('PASS source identity/5989-frame coverage/repeat counters and hash-bound342Python/47native/132command,75completed4K,21raw-snapshot,original-resource/route receipts. Wide readback integrity only; no future/deployment acceptance.')
