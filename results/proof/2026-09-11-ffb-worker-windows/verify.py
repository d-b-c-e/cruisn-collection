"""Check code hashes and window-measurement receipts, without private traces."""
from pathlib import Path
import hashlib,json,math,sys
here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes
def read(name):return json.loads((here/name).read_text(encoding='utf-8'))
def require(value,why):
    if not value:raise ValueError(why)
manifest=read('manifest.json');require(manifest['schema']==1,'schema')
for name,digest in manifest['files'].items():
    require(Path(name).name==name,'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt '+name)
for name,digest in read('source.json').items():
    path=(root/name).resolve();require(path.is_relative_to(root),'source path')
    require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source '+name)
p=read('measurements.json');require(p['passed'] and not p['normalization_accepted']
    and not p['physical_acceptance'] and not p['windows_reviewed'],'scope')
require(p['common_2second_bins']==['40-60mps/center/steady'],'common coverage')
expected={'usa':(840,316,5012),'world':(2290,1004,9269),'offroad':(1907,904,9644),'exotica':(1587,789,8860)}
require(set(p['games'])==set(expected),'four games')
for game,item in p['games'].items():
    require((item['merged_windows'],item['known_interiors'],item['input_join_frames'])==expected[game],'coverage '+game)
    require(0<item['known_host_seconds'] and 0<item['largest_internal_anchor_gap_seconds']<.1,'anchors '+game)
    require('emulated_seconds' in item['input_join_fields'] and 'frame' in item['input_join_fields']
        and not {'host_seconds','speed_percent'}.intersection(item['input_join_fields']),'input projection '+game)
    for name,m in item['groups'].items():
        require(0<m['seconds']<=item['known_host_seconds'] and 0<m['intervals']<=item['known_interiors'],'group coverage')
        require(abs(m['positive_seconds']+m['negative_seconds']+m['zero_seconds']-m['seconds'])<1e-8,'duration partition')
        require(0<=m['absolute_p50']<=m['absolute_p90']<=m['peak_abs']<=1,'quantiles')
        require(0<=m['rms']<=m['peak_abs'] and 0<=m['requested_ceiling_fraction']<=m['within_one_percent_of_ceiling_fraction']<=1,'output bounds')
        require(abs(m['signed_impulse_normalized_seconds'])<=m['absolute_impulse_normalized_seconds']+1e-12,'impulse bounds')
turn='40-60mps/negative-medium/slow';exo=p['games']['exotica']['groups'][turn]
require(exo['seconds']<1 and exo['requested_ceiling_fraction']==0
    and exo['within_one_percent_of_ceiling_fraction']>.65,'small near-ceiling sample')
require(sum(item['groups'][turn]['seconds']>=2 for item in p['games'].values())==1,'turn coverage insufficient')
c=read('checks.json');require(c['passed'] and c['groups']==['python'] and c['python']['passed']
    and c['python']['tests']==424 and c['python']['skipped']==0,'Python checks')
print('PASS source/hash/aggregate receipts; only centered input has common 2-second coverage; calibration remains open')
