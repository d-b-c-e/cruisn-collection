"""Recompute all Exotica CPU sphere decisions without ROMs; GL agreement is a receipt."""
import csv,hashlib,io,json,sys,tempfile,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((root/'derived-evidence.zip').read_bytes())==m['archive_sha256']
with zipfile.ZipFile(root/'derived-evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(m['entries'])
 for name,digest in m['entries'].items():assert sha(z.read(name))==digest,name
 read=lambda name:json.loads(z.read(name))
 invocation=read('invocation.json');report=read('report.json');summary=read('summary.json')
 assert invocation['executable_sha256']==m['native_sha256'] and invocation['environment']['MIDV_FFB']=='0'
 assert invocation['returncode']==0 and invocation['error'] is None
 assert report['passed'] and report['evidence']['frames']==6000
 assert report['gl_comparison']['passed'] and report['gl_comparison']['frames']==21
 assert sha(z.read('probe.lua'))==sha(z.read('source/exotica_frustum.lua'))==report['probe_script']['sha256']
 def inputs(name):
  reader=csv.DictReader(io.StringIO(z.read(name).decode('utf-8')))
  fields=[k for k in reader.fieldnames if k not in ('host_seconds','speed_percent')]
  rows=[tuple(r[k] for k in fields) for r in reader]
  assert [int(r[0]) for r in rows]==list(range(1,6001))
  return fields,rows
 assert inputs('frames.csv')==inputs('reference/frames.csv')
 captures=list(csv.DictReader(io.StringIO(z.read('captures.csv').decode('utf-8'))))
 assert [int(r['completed_frame']) for r in captures]==list(range(5400,5421))
 assert all((r['width'],r['height'])==('3840','2160') and r['dropped_messages']=='0' for r in captures)
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)
  for name in ('analyze_exotica_frustum.py','verification.py'):(p/name).write_bytes(z.read('source/'+name))
  (p/'trace.csv').write_bytes(z.read('trace.csv'));sys.path.insert(0,td)
  from analyze_exotica_frustum import summarize,evaluate
  assert summarize(p/'trace.csv')==summary
  bad=read('rejected/sample.json')
  try:evaluate(bad['row'])
  except ValueError as error:assert str(error)==bad['error']
  else:raise AssertionError('branch-delay negative control unexpectedly passed')
 assert summary['samples']==339018 and summary['predicted_additions']==4051 and summary['predicted_losses']==0
print('PASS: archive/native bindings, all339018 sphere tests, input identity,21GL receipt and rejected delay-slot sample')
