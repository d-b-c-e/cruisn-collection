"""Verify source/hash/aggregate consistency, without private game/GPU evidence."""
from pathlib import Path
import hashlib,json,sys
here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes
def read(name):return json.loads((here/name).read_text())
def require(value,why):
    if not value:raise ValueError(why)
manifest=read('manifest.json');require(manifest['schema']==1,'schema')
for name,digest in manifest['files'].items():
    require(Path(name).name==name,'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt digest: '+name)
for name,digest in read('source.json').items():
    p=(root/name).resolve();require(p.is_relative_to(root),'source path')
    require(hashlib.sha256(canonical_bytes(p,p.read_bytes())).hexdigest()==digest,'source digest: '+name)
fences=read('fences.json');require(fences['passed'] and fences['scenes']==6953,'scene coverage')
require(fences['total_first_commits_after_proposal_before_end']==2692 and fences['total_first_commits_end_to_ready']==0,'admission windows')
require(fences['nonimmediate_scenes']==5514 and fences['maximum_end_to_ready_ps']==16975900000,'fence waits')
frames=[3900,5072,5644,6330,7187];proposed=[252,155,298,52,1];retained=[252,145,298,52,1]
require([s['frame'] for s in fences['snapshots']]==frames,'sample order')
for row,a,b in zip(fences['snapshots'],proposed,retained):
    require(row['candidate_count']==a and row['removed_at_cpu_end']==a-b,'candidate counts')
    require(row['end_records']==row['ready_records'] and row['between_cpu_end_and_device_ready']==0,'completion prefixes')
cohorts=read('cohorts.json');require(cohorts['passed'] and len(cohorts['cases'])==30,'geometry cases')
seen=set()
for row in cohorts['cases']:
    key=(row['frame'],row['multiplier'],row['complete_fade']);require(key not in seen,'duplicate case');seen.add(key)
    i=frames.index(row['frame']);require(row['captured']==proposed[i] and row['retained']==retained[i]
        and row['submitted']==proposed[i]-retained[i] and row['retired']==0,'reconciled ownership')
require(seen=={(f,m,a) for f in frames for m in (1,2,3) for a in (0,1)},'geometry coverage')
join=read('command-join.json');require(join['passed'] and join['all_original_quads_exact']==3349
    and join['original_quads_before_fence']==3219 and join['command_index']==3358 and join['last_original_model']==160,'CPU/GPU fence join')
placement=read('placement.json');require(placement['passed'] and len(placement['cases'])==6,'GPU cases')
cases={r['name']:r for r in placement['cases']}
for row in cases.values():
    require(row['passed'] and row['insertion']['other_page_exact'] and row['insertion']['integrity'],'GPU isolation/depth receipt')
require(cases['2-3x']['actual_sha256']==cases['3-3x']['actual_sha256']==cases['1-2x']['actual_sha256'],'repeat and 2/3 relation')
require(cases['early-control']['actual_sha256'][1]==cases['2-3x']['actual_sha256'][1]
    and cases['early-control']['actual_sha256'][0]!=cases['2-3x']['actual_sha256'][0],'composition remains order-sensitive')
require([p['command_index'] for p in cases['2-3x']['packets']]==[32,3358],'split placement')
visual=read('visual.json');last=visual['checks'][-1]
require(visual['passed'] and last['changed_rgb_vs_future_only']==73346 and last['changed_center_rgb']==72385
    and last['newly_black']==0 and last['raw_sha256']==cases['2-3x']['actual_sha256'][0],'completed visual metrics')
replay=read('replay.json');require(replay['passed'] and replay['comparison']['passed'] and replay['frames']==8860,'original replay')
require(replay['physical_ffb']=='0' and replay['display']==dict(frames=21,passed=True,requested_size=[3840,2160]),'display scope')
require(replay['unchanged_observer']['passed'] and len(replay['unchanged_observer']['exact_files'])==17,'observer repeat')
require(replay['unchanged_observer']['exact_files']['exotica-lifetime-events.csv']==fences['inputs']['exotica-lifetime-events.csv']==cohorts['input_sha256'],'same lifetime evidence')
checks=read('checks.json');require(checks['passed'] and checks['source_identity']==checks['source_identity_after'],'tested source')
require(checks['commands']==144 and checks['native_tests']==51
    and checks['tests']==dict(passed=True,tests=390,skipped=0,errors=0,failures=0),'full local check receipt')
print('PASS source/hash/aggregate consistency; raw game/GPU execution and live handover acceptance remain external')
