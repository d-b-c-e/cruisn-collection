"""Recompute archived Off Road native, replay and cross-game telemetry checks using only the standard library."""
from collections import Counter
import csv,hashlib,io,json,math,sys,tempfile,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((root/'derived-evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'derived-evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['entries'])
 for name,digest in manifest['entries'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts
  assert sha(z.read(name))==digest,name
 read=lambda name:json.loads(z.read(name))
 def trace(name):
  reader=csv.DictReader(io.StringIO(z.read(name).decode('utf-8')))
  rows=list(reader);assert rows and all(None not in r and all(v is not None for v in r.values()) for r in rows)
  assert [int(r['frame']) for r in rows]==list(range(1,len(rows)+1))
  return reader.fieldnames,rows
 def inputs(name):
  fields,rows=trace(name);fields=[k for k in fields if k not in ('host_seconds','speed_percent')]
  return fields,[tuple(r[k] for k in fields) for r in rows]
 reference=inputs('reference/frames.csv')
 def invocation(prefix,native=None):
  r=read(prefix+'invocation.json')
  assert r['executable_sha256']==(native or manifest['native_sha256'])
  assert r['environment']['MIDV_FFB']=='0'
  return r
 def completed(prefix,frames=6000):
  r=read(prefix+'report.json');assert not r.get('error') and r['evidence']['frames']==frames
  assert r['comparison']['input_or_time_mismatches']==0
  assert inputs(prefix+'frames.csv')==(reference[0],reference[1][:frames])
  invocation(prefix)
  return r
 def captures(prefix,expected,size):
  rows=list(csv.DictReader(io.StringIO(z.read(prefix+'captures.csv').decode('utf-8'))))
  assert [int(r['completed_frame']) for r in rows]==list(expected)
  assert all((int(r['width']),int(r['height']))==tuple(size) and int(r['dropped_messages'])==0 for r in rows)
 def timing(prefix,report):
  _,rows=trace(prefix+'frames.csv');a=rows[report['first_frame']-1];b=rows[report['last_frame']-1]
  ratio=(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
  assert math.isclose(ratio,report['emulation_ratio'],rel_tol=1e-12)
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)
  for name in manifest['entries']:
   if name.startswith('source/'):
    dest=p/name.removeprefix('source/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
  sys.path.insert(0,str(p/'harness'))
  from analyze_offroad_native import summarize
  from compare_world_motion import compare
  from analyze_drivetrain import analyze as drivetrain
  from analyze_force_gate import analyze as force
  def materialize(prefix,names):
   directory=p/'runtime'/prefix;directory.mkdir(parents=True,exist_ok=True)
   for name in names:(directory/name).write_bytes(z.read(prefix+name))
   return directory
  native_names=['offroad-native.csv','offroad-native-projection.csv']
  motion_names=['offroad-camera.csv','offroad-adc.csv']
  matrix=read('matrix/report.json');assert matrix['completed'] and len(matrix['trials'])==4
  assert matrix['candidate_sha256']==manifest['native_sha256']
  assert matrix['motion_sha256']==sha(z.read('matrix/motion.lua'))
  for index,row in enumerate(matrix['trials']):
   name=f'{index}-x{[1,2,3,2][index]}';assert row['name']==name
   prefix='matrix/'+name+'/';directory=materialize(prefix,native_names+motion_names)
   assert summarize(directory,6000)==row['native_distance']
   assert compare(p/'runtime/matrix/0-x1',directory,'offroad')==row['motion']
   assert row['motion']['camera_equal'] and row['motion']['adc_frame_value_pc_equal']
   r=completed(prefix);assert r['passed']==(index==0)
   assert r['probe_script']['sha256']==sha(z.read(prefix+'probe.lua'))==matrix['motion_sha256']
   captures(prefix,range(1800,5901,100),(512,451));timing(prefix,row['timing'])
  repeat=read('checks/matrix-repeat.json');assert repeat['passed'] and repeat['native_logs_equal'] and repeat['gl']['passed']
  assert compare(p/'runtime/matrix/1-x2',p/'runtime/matrix/3-x2','offroad')==repeat['motion']
  for name in native_names:assert z.read('matrix/1-x2/'+name)==z.read('matrix/3-x2/'+name)
  for name in ('two-vs-three-gl.json','0-x1-lua-gl.json','1-x2-lua-gl.json'):assert read('checks/'+name)['passed']
  derived=read('candidate/report.json');assert derived['passed'] and derived['identity_replay_passed']
  assert read('candidate/replay-report.json')['passed']
  counts=read('checks/derived-native.json');assert counts['native_logs_equal']
  for label in ('record','replay'):
   prefix='candidate/'+label+'/';d=materialize(prefix,native_names)
   assert summarize(d,6000)==counts[label]
   assert inputs(prefix+'frames.csv')==reference
   invocation(prefix);captures(prefix,range(3500,4701,100),(3824,2073))
  for name in native_names:assert z.read('candidate/record/'+name)==z.read('candidate/replay/'+name)
  for name in ('scene-stock','scene-two-times'):
   prefix='scenes/'+name+'/';completed(prefix,4402);summarize(materialize(prefix,native_names),4402)
   captures(prefix,(4399,4400),(3824,2073))
  for name in ('stock','two-times'):
   prefix='rejected/'+name+'/';d=materialize(prefix,native_names)
   invocation(prefix,manifest['initial_native_sha256'])
   try:summarize(d,6000)
   except ValueError as error:assert 'missing/duplicate frame' in str(error)
   else:raise AssertionError('initial duplicate-frame log was incorrectly accepted')
  suite=read('source/suite.json');reg=read('regressions/report.json')
  assert reg['passed'] and len(reg['cases'])==len(suite['cases'])==7
  for case,item in zip(suite['cases'],reg['cases']):
   assert case['id']==item['id'] and item['passed']
   prefix='regressions/'+item['id']+'/';r=read(prefix+'report.json');assert r['passed'] and not r.get('error')
   assert inputs(prefix+'frames.csv')==inputs(prefix+'reference-frames.csv')
   invocation(prefix);assert r['telemetry_loopback']['passed'] and r['telemetry_loopback']['local_only']
   names=['frames.csv','drivetrain.csv','drivetrain-memory.csv','forza.csv','telemetry.jsonl','force-gate.csv','force-source.csv']
   d=materialize(prefix,names);t=drivetrain(d,d/'drivetrain-memory.csv')
   expected=dict(item['telemetry']);assert expected.pop('coverage_passed')
   assert t==expected
   options=case['telemetry']
   assert t['game_state_samples']>=options.get('minimum_active_frames',500)
   assert t['wire']['maximum_speed_mph']>=options.get('minimum_speed_mph',10)
   if options.get('force_gate_game'):
    assert force(d,d/'drivetrain-memory.csv',options['force_gate_game'],options.get('force_gate_policy','driving'),options.get('force_polarity',False))==item['force_gate']
   assert r['probe_script']['sha256']==sha(z.read(prefix+'probe.lua'))
   for t in item['timings']:timing(prefix,t);assert t['passed'] and t['emulation_ratio']>=t['minimum_ratio']
 q=read('checks/scene-quads.json');a,b=Counter(q['reference']),Counter(q['candidate']);common=a&b
 assert len(q['reference'])==716 and len(q['candidate'])==739 and sum((a-b).values())==1 and sum((b-a).values())==24
 def retained(keys):
  c=common.copy();result=[]
  for key in keys:
   if c[key]:result.append(key);c[key]-=1
  return result
 assert retained(q['reference'])==retained(q['candidate']) and q['common_order_equal']
 assert [i for i,(a,b) in enumerate(zip(q['original_quad'],q['nearest_quad'])) if a!=b]==q['changed_old_words']==[6,7,8]
 assert q['resources']=={'textureram.bin':True,'paletteram.bin':True}
 g=read('checks/scene-geometry.json');assert not g['passed'] and g['geometry']['removed_or_changed_quads']==1
 assert g['native_attribution']['outside_added_coverage']==384 and q['native_page_attribution']['target_outside_added_coverage']==0
 identity=read('checks/source-identity.json')
 assert read('regressions/report.json')['source_identity']==identity['sha256']
 assert identity==read('checks/source-identity-ubuntu-latest.json')==read('checks/source-identity-windows-latest.json')
 assert len(identity['files'])==262
 for name in ('ci-code.json','ci-menu.json'):
  ci=read('checks/'+name);assert ci['conclusion']=='success' and len(ci['jobs'])==4 and all(j['conclusion']=='success' for j in ci['jobs'])
 assert 'Ran 163 tests' in z.read('checks/tests-menu.log').decode('utf-8-sig')
 deployment=read('checks/deployment.json');assert deployment['native']['sha256']==manifest['native_sha256']
 assert deployment['release_zip']['sha256']=='fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a'
 assert read('checks/export.json')['patch_count']==129
print('PASS: Off Road counters, original inputs, repeat motion, seven actual telemetry/memory and force checks; strict geometry failure retained')
