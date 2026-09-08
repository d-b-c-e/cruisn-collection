"""Verify bindings and recompute USA distance/motion/input conclusions without ROMs.
Completed image agreement is a hashed run receipt; the full BMPs remain local.
"""
import ast,csv,hashlib,io,json,tempfile,zipfile
from decimal import Decimal,InvalidOperation
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((root/'derived-evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'derived-evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['entries'])
 for name,digest in manifest['entries'].items():assert sha(z.read(name))==digest,name
 read=lambda n:json.loads(z.read(n))
 native=manifest['native_sha256']
 def invocation(name):
  r=read(name);assert r['executable_sha256']==native and r['environment']['MIDV_FFB']=='0'
 def functions(source,names,constants=()):
  tree=ast.parse(z.read('source/'+source).decode('utf-8'))
  nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names
   or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
  ns=dict(csv=csv,Path=Path,Decimal=Decimal,InvalidOperation=InvalidOperation,
   sha256_file=lambda p:sha(Path(p).read_bytes()),__doc__=ast.get_docstring(tree),FAR_VALUES=(80000,100000,160000,240000))
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'archived analyzer','exec'),ns)
  return ns
 distance=functions('analyze_usa_distance.py',('summarize',),('FIELDS','COUNTERS'))['summarize']
 motion=functions('compare_world_motion.py',('compare','read_trace'),('CAMERA','ADC'))['compare']
 def inputs(name):
  reader=csv.DictReader(io.StringIO(z.read(name).decode('utf-8')))
  fields=[f for f in reader.fieldnames if f not in ('host_seconds','speed_percent')]
  rows=[tuple(row[k] for k in fields) for row in reader]
  assert [int(r[0]) for r in rows]==list(range(1,len(rows)+1))
  return fields,rows
 reference_inputs=inputs('reference/frames.csv');reference=read('reference/case.json')
 trials=read('trials/report.json');assert trials['completed'] and trials['candidate_sha256']==native
 assert len(trials['trials'])==5
 assert sha(z.read('trials/motion.lua'))==trials['motion_script_sha256']
 with tempfile.TemporaryDirectory() as td:
  for row in trials['trials']:
   prefix='trials/'+row['name']+'/'
   directory=Path(td)/row['name'];directory.mkdir()
   for name in ('usa-distance.csv','usa-camera.csv','usa-adc.csv'): (directory/name).write_bytes(z.read(prefix+name))
   assert distance(directory/'usa-distance.csv')==row['native_distance']
   assert motion(Path(td)/'original',directory,'usa')==row['motion']
   r=read(prefix+'report.json');assert r['evidence']['frames']==5012
   assert inputs(prefix+'frames.csv')==reference_inputs
   assert r['comparison']['input_or_time_mismatches']==0
   bad=[int(n) for n,v in reference['evidence']['snapshots'].items() if r['evidence']['snapshots'][n]!=v]
   assert r['comparison']['pixel_mismatches']==len(bad)
   assert r['passed']==(row['name']=='original')
   assert row['gl']['frames']==19 and not row['gl']['size_mismatches']
   invocation(prefix+'invocation.json')
  assert motion(Path(td)/'far2-residency',Path(td)/'far3-residency','usa')==read('two-three-motion.json')
 assert read('two-times-case/report.json')['passed']
 repeat=read('two-times-case/replay.json');assert repeat['passed']
 assert repeat['gl_comparison']['passed'] and repeat['gl_comparison']['frames']==19
 assert inputs('two-times-case/record-frames.csv')==inputs('two-times-case/replay-frames.csv')
 for name in ('record','replay'):invocation('two-times-case/'+name+'-invocation.json')
 assert not read('two-three-gl.json')['passed'] and not read('two-three-motion.json')['passed']
 controls=read('defaults/report.json');assert controls['passed'] and len(controls['cases'])==7
 assert controls['candidate_sha256']==native
 for row in controls['cases']:
  assert row['passed'];invocation('defaults/'+row['id']+'/invocation.json')
  r=read('defaults/'+row['id']+'/report.json');assert r['passed']
  if row['id']=='exotica':assert r['gl_comparison']['passed'] and r['gl_comparison']['frames']==21
 ids=[read('checks/'+n) for n in ('source-identity.json','windows-identity.json','linux-identity.json')]
 assert ids[0]==ids[1]==ids[2] and controls['source_identity']==ids[0]['sha256']==manifest['source_identity']
 ci=read('checks/ci.json');assert ci['conclusion']=='success' and len(ci['jobs'])==4
 assert all(j['conclusion']=='success' for j in ci['jobs'])
 assert read('checks/export.json')['passed'] and read('checks/export.json')['patches']==126
 assert read('checks/native-vectors.json')['passed']
 assert not read('checks/native-vectors-missing-runtime.json')['passed']
 off=read('offroad-table/recomputed.json');assert off['negative_mismatches']==0
 assert off['nonnegative_mismatches_by_decimals']=={'6':62856,'7':56246,'8':0,'9':48268}
 assert read('offroad-table/python-round-failed.json')['nonnegative_mismatches_by_decimals']['8']==2
print('PASS: bytes/bindings, five USA distance/motion/input trials, repeatability receipts and seven defaults')
