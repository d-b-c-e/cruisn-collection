"""Verify Off Road diagnostic conclusions without ROMs or graphics libraries."""
from collections import Counter
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
 def inputs(name):
  reader=csv.DictReader(io.StringIO(z.read(name).decode('utf-8')))
  fields=[k for k in reader.fieldnames if k not in ('host_seconds','speed_percent')]
  rows=[tuple(r[k] for k in fields) for r in reader]
  assert [int(r[0]) for r in rows]==list(range(1,len(rows)+1))
  return fields,rows
 reference=inputs('reference/frames.csv')
 def invocation(prefix):
  r=read(prefix+'invocation.json')
  assert r['executable_sha256']==m['native_sha256'] and r['environment']['MIDV_FFB']=='0'
 def completed(prefix,frames=6000):
  r=read(prefix+'report.json');assert r['evidence']['frames']==frames and not r.get('error')
  assert r['comparison']['input_or_time_mismatches']==0
  assert inputs(prefix+'frames.csv')==(reference[0],reference[1][:frames])
  assert r['probe_script']['sha256']==sha(z.read(prefix+'probe.lua'))
  invocation(prefix)
  return r
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)
  for n in ('analyze_offroad_distance.py','compare_world_motion.py','verification.py'):
   (p/n).write_bytes(z.read('source/'+n))
  sys.path.insert(0,td)
  from analyze_offroad_distance import summarize
  from compare_world_motion import compare
  def materialize(prefix):
   directory=p/prefix;directory.mkdir(parents=True)
   for n in ('offroad-distance.csv','offroad-projection.csv','offroad-camera.csv','offroad-adc.csv','offroad-limit-writes.csv'):
    if prefix+n in m['entries']:(directory/n).write_bytes(z.read(prefix+n))
   return directory
  trials=read('trials/report.json');assert trials['completed'] and trials['candidate_sha256']==m['native_sha256']
  assert [r['name'] for r in trials['trials']]==['original','far2','far3']
  for i,row in enumerate(trials['trials'],1):
   prefix='trials/'+row['name']+'/'
   directory=materialize(prefix)
   assert summarize(directory)==row['distance']
   assert compare(p/'trials/original',directory,'offroad')==row['motion']
   assert row['motion']['camera_equal'] and row['motion']['adc_frame_value_pc_equal']
   r=completed(prefix);assert r['passed']==(i==1)
   source=z.read('source/offroad_distance.lua').decode('utf-8').replace('\r\n','\n')
   for key,default,value in [('FIRST',1800,1800),('LAST',5990,5990),('MULTIPLIER',0,i)]:
    source=source.replace(f"os.getenv('CRUISN_OFFROAD_{key}') or '{default}'",str(value))
   assert source==z.read(prefix+'probe.lua').decode('utf-8').replace('\r\n','\n')
   assert row['gl']['frames']==42 and not row['gl']['size_mismatches']
  assert compare(p/'trials/far2',p/'trials/far3','offroad')==read('trials/two-three-motion.json')
  assert read('trials/two-three-gl.json')['passed']
  for name in ('original','far125'):
   prefix='culler125/'+name+'/'
   directory=materialize(prefix);assert summarize(directory)==read(prefix+'summary.json')
   completed(prefix)
  assert compare(p/'culler125/original',p/'culler125/far125','offroad')==read('culler125/motion.json')
  for name in ('scene-original-v2','scene-far2-v2'):
   prefix='scenes/'+name+'/';materialize(prefix);completed(prefix,4402)
  assert compare(p/'scenes/scene-original-v2',p/'scenes/scene-far2-v2','offroad')==read('checks/scene-motion.json')
 for name in ('resource-read','reset'):
  prefix='rejected/'+name+'/';assert read(prefix+'report.json')['error'];invocation(prefix)
 assert 'pc=1ea8 offset=cd9f4f IR0=bc2' in z.read('rejected/resource-read/stderr.log').decode('utf-8')
 assert 'far changed during observation' in z.read('rejected/reset/stderr.log').decode('utf-8')
 q=read('checks/scene-quads.json');a,b=Counter(q['reference']),Counter(q['candidate']);common=a&b
 assert len(q['reference'])==716 and len(q['candidate'])==739
 assert sum((a-b).values())==1 and sum((b-a).values())==24
 def retained(keys):
  counts=common.copy();result=[]
  for key in keys:
   if counts[key]:result.append(key);counts[key]-=1
  return result
 assert retained(q['reference'])==retained(q['candidate']) and q['common_order_equal']
 g=read('checks/geometry.json');assert not g['passed']
 assert g['unchanged_resources']['textureram.bin'] and g['unchanged_resources']['paletteram.bin']
 assert q['native_page_attribution']['target_outside_added_coverage']==0
 ci=read('checks/ci.json');assert ci['conclusion']=='success' and len(ci['jobs'])==4
 assert all(j['conclusion']=='success' for j in ci['jobs'])
 assert 'Ran 147 tests' in z.read('checks/tests-final.log').decode('utf-8-sig')
print('PASS: native/probe bindings, five distance/input/motion trials, ordered quad hashes and retained negative controls')
