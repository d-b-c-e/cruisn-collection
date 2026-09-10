from pathlib import Path
import csv,hashlib,json,statistics
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for name,digest in read('manifest.json').items():
 p=(root/name).resolve();assert p.is_relative_to(root.resolve())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
identity=read('source-identity.json');checks=read('report.json')
payload=''.join(f'{n}\0{h}\n' for n,h in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==identity['sha256']
assert len(checks['steps'])==107 and all(s['returncode']==0 for s in checks['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=311,skipped=0,errors=0,failures=0)
for name,counts in [('captured.json',[4096,4,4,1376,1376]),('page-images.json',[4096,3,0,1,4])]:
 r=read(name);assert r['passed'] and r['reverse_serialization'] and len(r['malformed_rejections'])==6
 assert [s['pages'] for s in r['snapshots']]==counts and r['total_image_bytes']==83886080
rows=list(csv.DictReader((root/'benchmark.csv').open(encoding='utf-8-sig')))
bench=read('benchmark.json');assert bench['passed'] and len(rows)==bench['samples']==705
for phase,values in bench['phases'].items():
 group=[r for r in rows if r['phase']==phase];assert len(group)==values['count']
 assert sorted({int(r['pages']) for r in group})==values['page_counts']
 for field,expected in values['timing'].items():
  samples=sorted(float(r[field]) for r in group)
  actual=dict(mean=statistics.mean(samples),p99=samples[min(len(samples)-1,int(len(samples)*.99))],max=max(samples))
  assert actual==expected
print('PASS seven receipt hashes and recomputed CPU timing; raw textures/packets/builds remain receipts.')
