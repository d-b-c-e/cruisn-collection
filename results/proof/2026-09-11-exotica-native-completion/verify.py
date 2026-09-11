"""Check tested source and receipt consistency; private live execution is not rerun."""
from pathlib import Path
import hashlib,json,sys
here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes

def read(name):return json.loads((here/name).read_text())
def require(value,why):
 if not value:raise ValueError(why)

manifest=read('manifest.json');require(manifest['schema']==1,'manifest schema')
for name,digest in manifest['files'].items():
 require(Path(name).name==name,'receipt path')
 require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt '+name)
for name,digest in read('source.json').items():
 path=(root/name).resolve();require(path.is_relative_to(root),'source path')
 require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source '+name)
build=read('build.json')
require(build['passed'] and build['patch_count']==187
 and build['native_commit']=='bc384056fd1e9cf4adf9ab6d8208bcc6d1da9463'
 and build['tree']=='bc506377e0bbfc1d74b172bbb11e008e7587b2fe','native build receipt')
for name in ('short','full','repeat','disabled'):
 p=read(name+'.json');short=name=='short'
 require(p['passed'] and p['frames']==(6000 if short else 8860),'full input lifetime')
 require(p['physical_ffb']=='0' and p['crt']=='1' and p['dimensions']==[[3840,2160]],'physical/display conditions')
 require(p['pixels']['passed'] and p['pixels']['frames']==p['completed_images']==21
  and not p['pixels']['different_frames'] and not p['pixels']['size_mismatches'],'displayed pixels')
 require(p['candidate_sha256']==build['candidate_sha256'],'candidate identity')
 require(p['unchanged_future_scenes']==(4120 if short else 6953),'original future scenes')
 require(p['motion']['exotica-camera.csv']['samples']==(4200 if short else 7060)
  and p['motion']['exotica-adc.csv']['samples']==(12600 if short else 21180),'original motion coverage')
 if name=='disabled':require(p['completion']['mode']=='off','disabled mode')
 else:
  q=p['completion']['result'];require(q['passed'] and q['complete']==1 and q['remaining']==0,'completion receipt')
  require(q['scenes']==p['unchanged_future_scenes'] and q['snapshots']==(3 if short else 5),'completion extent')
  if not short:
   require(q['captured']==1021808 and q['submitted']==2621 and q['retired']==0
    and q['owners_changed_after_cpu_end']==0 and q['bytes']==49324904,'full cohort reconciliation')
comp=read('comparisons.json')
require(all(p['passed'] for p in comp.values()),'independent/repeat/disabled receipts')
require(len(comp['repeat']['files'])==17 and comp['repeat']['unchanged_old_event_scene_fence'],'exact repeat')
require(comp['disabled']['no_handover_artifacts'] and comp['disabled']['no_waiting_artifacts'],'disabled artifacts')
checks=read('checks.json')
require(checks['passed'] and checks['source_identity']==checks['source_identity_after']
 and checks['groups']==['python','native','gpu'] and checks['commands']==144
 and checks['native_tests']==51,'local full checks')
require(checks['python']==dict(passed=True,tests=397,skipped=0,errors=0,failures=0),'Python checks')
print('PASS checked-source/hash/aggregate receipts; native execution, private geometry and pixels remain separate')
