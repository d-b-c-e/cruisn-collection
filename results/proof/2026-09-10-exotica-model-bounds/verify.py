"""Check receipt consistency; unarchived game geometry is not recomputed."""
from pathlib import Path
import hashlib
import json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for name,digest in read('manifest.json').items():
    path=(root/name).resolve();assert path.is_relative_to(root.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
identity=read('source-identity.json');checks=read('report.json')
payload=''.join(f'{n}\0{h}\n' for n,h in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==identity['sha256']
assert len(identity['files'])==454 and len(checks['steps'])==103
assert all(s['returncode']==0 for s in checks['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=305,skipped=0,errors=0,failures=0)
for name,counts in [('5000.json',(1515,725,4741,9596,4740)),('5072.json',(1622,1535,15881,16408,382)),('5990.json',(818,740,4598,5478,457)),('zeus-bounds.json',(5000,808,159,3701,3307))]:
    row=read(name)
    assert row['passed'] and row['native_python_exact'] and row['false_rejections']==0
    assert row['malformed_batches_rejected']==4
    assert tuple(row[k] for k in ('cases','rejected','avoided_polygons','decoded_polygons','visible_polygons'))==counts
    assert row['native_sha256']=='11579692674e424625898959030cffc76eff29fcf5d875b1b9808eccdf67869c'
print('PASS seven hash-bound receipts; raw geometry is not recomputed.')
