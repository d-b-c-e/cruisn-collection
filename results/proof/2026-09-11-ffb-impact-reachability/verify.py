"""Source/hash and aggregate receipts; no raw game or wheel execution."""
from pathlib import Path
import hashlib,json,sys
here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes
def read(n):return json.loads((here/n).read_text())
def require(value,why):
 if not value:raise ValueError(why)
manifest=read('manifest.json');require(manifest['schema']==1,'schema')
for name,digest in manifest['files'].items():
 require(Path(name).name==name,'receipt path')
 require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt '+name)
for name,digest in read('source.json').items():
 path=(root/name).resolve();require(path.is_relative_to(root),'source path')
 require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source '+name)
p=read('comparison.json');require(p['passed'] and not p['normalization_accepted'] and not p['physical_output'],'scope')
require(p['native_tests']['passed'] and p['native_tests']['exit_code']==0
 and p['native_tests']['new_cases']==35 and p['native_tests']['old_adapter_and_alias_cases']==6,'compiled test receipt')
require(p['new_analyzer_sha256']!=p['old_analyzer_sha256'],'distinct analyzer builds')
for game,item in p['games'].items():
 for name,mode in item['modes'].items():
  d=mode['detector'];require(mode['unchanged_old_metrics'] and mode['requested_strength']==50,'reference metrics')
  require(mode['effective_strength']==(40 if game=='exotica' else 50),'explicit trim')
  require(d['input']==('raw_motor' if name=='enhanced' else 'adapted_motor'),'detector source')
  require(0<=d['sampled_peak_abs']<=d['source_peak_abs']<=1,'detector range')
  require(d['source_arrival_reachable']==(d['source_peak_abs']>=d['arrival']),'source bound')
exo=p['games']['exotica'];d=exo['modes']['enhanced']['detector']
require(exo['source_rows']==7476 and (exo['raw_min'],exo['raw_max'])==(-60,62),'Amazon source coverage')
require(not d['source_arrival_reachable'] and d['sampled_arrival_ticks']==0
 and exo['modes']['enhanced']['idealized_event_count']==0,'unreachable enhanced arrival')
require(exo['modes']['legacy']['detector']['source_arrival_reachable'],'legacy path distinguished')
print('PASS code/hash/aggregate receipts; Exotica enhanced arrival is unreachable on this captured source')
