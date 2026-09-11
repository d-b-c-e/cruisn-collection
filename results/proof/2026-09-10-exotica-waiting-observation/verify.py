"""Source and receipt consistency only; no raw/native/game/GPU execution."""
from pathlib import Path
import hashlib,json,sys
here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes
def read(name):return json.loads((here/name).read_text())
def require(ok,why):
    if not ok:raise ValueError(why)
manifest=read('manifest.json');require(manifest['schema']==1,'schema')
for name,digest in manifest['files'].items():
    require(Path(name).name==name,'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt digest '+name)
for name,digest in read('source.json').items():
    path=(root/name).resolve();require(path.is_relative_to(root),'source path')
    require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source digest '+name)
native=read('native.json');require(native['passed'] and native['patch_count']==186,'native receipt')
require(hashlib.sha256((root/'patch/vunit-poc-patches.patch').read_bytes()).hexdigest()==native['patch_sha256'],'patch bytes')
checks=read('checks.json')
require(checks['passed'] and checks['groups']==['python','native','gpu'] and checks['commands']==142,'checks receipt')
require(checks['source_identity']==checks['source_identity_after'],'source changed during tests')
require(checks['units']==dict(passed=True,tests=375,skipped=0,failures=0,errors=0),'unit receipt')
runs=read('runs.json')
require(set(runs)=={'waiting-observer-short','waiting-observer-full','waiting-observer-repeat','waiting-observer-disabled'},'run coverage')
for name,r in runs.items():
    require(r['passed'] and r['candidate_sha256']==native['candidate_sha256'] and r['completed_original_4k']==21,'replay receipt')
    short=name.endswith('short');require(r['input_frames']==(6000 if short else 8860),'input count')
    require(r['motion_samples']=={'exotica-camera.csv':4200 if short else 7060,'exotica-adc.csv':12600 if short else 21180},'motion counts')
    require(r['unchanged_future_scenes']==(4120 if short else 6953),'future scenes')
    if name.endswith('disabled'):require(r['waiting']=={'mode':'off'},'disabled waiting')
    else:
        result=r['waiting']['result']
        require(result['passed'] and result['complete']==1 and result['remaining']==0,'observer completion')
        if not short:require((result['scenes'],result['candidates'],result['quads'],result['snapshot_owners_verified'])==(6953,1021808,5552865,758),'full proposal totals')
independent=read('independent.json');require(independent['passed'],'independent receipt')
require([(r['frame'],r['owners']) for r in independent['samples']]==[(3900,252),(5072,155),(5644,298),(6330,52),(7187,1)],'snapshot identity counts')
for r in independent['samples']:
    require(all(a==b for a,b in r['hashes'].values()),'independent geometry hashes')
repeat=read('repeat.json');require(repeat['passed'] and len(repeat['files'])==17,'repeat receipts')
require(independent['original_lifetime_prefix_records']==86376 and independent['lifetime_sha256']==independent['reference_lifetime_sha256']==repeat['files']['exotica-lifetime-events.csv'],'original lifetime identity')
handover=read('handover.json')
require([(r['frame'],r['later_in_scene']) for r in handover['samples']]==[(3900,0),(5072,10),(5644,0),(6330,0),(7187,0)],'handover receipts')
require(all(r['consecutive_scene'] and r['device_time']<r['next_scene_time'] for r in handover['samples']),'handover interval')
print('PASS source/hash/receipt consistency; native/raw execution and waiting drawing acceptance remain separate')
