from pathlib import Path
import csv,hashlib,json,re,collections
root=Path(__file__).parent;read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for name,digest in read('manifest.json')['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
identity=read('source-identity.json');checks=read('checks.json');native=read('native-export.json');defaults=read('defaults.json')
payload=''.join(f'{k}\0{v}\n' for k,v in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']==checks['source_identity']==checks['source_identity_after']==defaults['source_identity']
assert checks['passed'] and len(checks['steps'])==120 and all(s['returncode']==0 for s in checks['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=324,skipped=0,errors=0,failures=0)
assert native['passed'] and native['patch_count']==168 and native['native_commit']=='2eac1821916bf4f2f7975b48b45c2e48da993a15'
assert native['candidate_sha256']==defaults['candidate_sha256']=='cef7160a13440afaf8b865a9ee1421d10cfad1fe6143bdb89a21a8b9a0174b63'
assert native['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
assert defaults['passed'] and defaults['subset'] is None and len(defaults['cases'])==7 and not defaults['physical_force']
assert all(c['passed'] and c['telemetry']['passed'] for c in defaults['cases'])
assert len([c for c in defaults['cases'] if 'force_gate' in c])==4 and all(c['force_gate']['passed'] for c in defaults['cases'] if 'force_gate' in c)
cases=read('evidence.json')['cases'];assert len(cases)==6
with (root/'native-completions.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
images=0;counts={};by_time={}
for name,case in cases.items():
 for path,data in case['reports'].items():
  r=data['receipt'];assert r.get('passed',True),path
  if path.endswith('-gl.json'):assert not r['different_frames'];images+=r['frames']
  if path.endswith('-motion.json'):assert r['adc_times_equal'] and r['camera_equal']
 current=[r for r in rows if r['run']==name]
 if name.endswith('-off'):assert not current;continue
 assert current and len({r['scene'] for r in current})==len(current)
 completed=immediate=0
 for r in current:
  end,ready=float(r['end_time']),float(r['ready_time'])
  consumer,target,words=map(int,(r['consumer'],r['target'],r['words']))
  assert int(r['guest_cycles'])==0 and 0<=ready-end<.0176
  assert int(r['end_frame'])<=int(r['ready_frame'])<=int(r['end_frame'])+1
  assert 0x30000<=consumer<0x32000 and 0x30000<=target<0x32000
  assert words==(target-consumer)%0x2000
  assert int(r['immediate'])==int(words==0)
  if not words:assert ready==end
  immediate+=int(r['immediate']);completed+=1
  assert (name,end) not in by_time
  by_time[name,end]=r
 ack=[re.fullmatch(r'MIDZ_HOST_FENCE_RESULT complete=1 requested=(\d+) completed=(\d+) immediate=(\d+)',s) for s in case['acknowledgments']]
 ack=[m for m in ack if m];assert len(ack)==1
 assert tuple(map(int,ack[0].groups()))==(completed,completed,immediate)
 counts[name]=dict(completed=completed,immediate=immediate)
assert images==330
probes=read('independent-cursors.json');assert len(probes)==5
scenes=words_checked=0
for probe in probes:
 name=probe['run'];summary=probe['summary'];assert summary['complete'] and not summary['pending'] and not summary['failure']
 events=probe['events'];assert all(a['time']<=b['time'] for a,b in zip(events,events[1:]))
 groups=collections.defaultdict(list)
 for e in events:groups[e['scene']].append(e)
 assert len(groups)==summary['scenes'] and len(events)+len(groups)==summary['events'] #one omitted raw tail per scene
 for group in groups.values():
  assert group[0]['kind']=='begin'
  ends=[e for e in group if e['kind']=='end'];assert len(ends)==1;end=ends[0]
  r=by_time[name,end['time']];ready=float(r['ready_time'])
  assert (int(r['consumer']),int(r['target']),int(r['words']))==(end['a'],end['target'],end['c'])
  if not end['c']:
   assert ready==end['time'] and len([e for e in group if e['kind']=='immediate'])==1
  else:
   words=[e for e in group if e['kind'] in ('word_before','target_before')]
   assert len(words)==end['c'] and words[-1]['kind']=='target_before'
   cursor=end['a']
   for i,e in enumerate(words,1):
    cursor=0x30000+(cursor-0x30000+1)%0x2000
    assert e['a']==cursor and e['c']==i
   assert cursor==end['target'];words_checked+=len(words)
   after=[e for e in group if e['kind'] in ('after_read','after_commit')];assert len(after)==1
   assert words[-1]['time']<=ready<=after[0]['time'] and abs(ready-words[-1]['time'])<1e-11
  scenes+=1
assert scenes==69
print('PASS six comparisons/330paired4K/seven default receipts;',sum(x['completed'] for x in counts.values()),'native completions,',scenes,'independent scenes,',words_checked,'ordered pending words. No extra drawing claimed.')
print(json.dumps(counts,indent=2))
