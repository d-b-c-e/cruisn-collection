"""Verify source and compact receipts; no private game/GPU execution is replayed."""
from pathlib import Path
import hashlib,json,sys
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
r=read('measurements.json');require(r['passed'] and not r['live_waiting_draw_accepted'],'scope')
expected=[(3900,1690,19),(5072,849,14),(5644,1906,14),(6330,338,5),(7187,18,1)]
require([(s['frame'],s['quads'],s['palettes']) for s in r['samples']]==expected,'five actual samples')
for s in r['samples']:
    require(s['passed'] and s['generation']==2 and s['pages']==0,'retained transition')
    require(s['old_bytes']-s['retained_bytes']==4096*4100,'avoided full image')
    require(s['retained_bytes']==32+32+64+s['palettes']*1032+s['quads']*264,'packet extent')
    require(s['retained_sha256']==s['expected_sha256'],'independent packet bytes')
require(len(r['rejections'])==6 and all(s['returncode']!=0 for s in r['rejections']),'input rejections')
g=read('gpu.json');require(g['passed'] and len(g['cases'])==4,'GPU receipt')
require(g['cases'][1]['actual_sha256']==g['cases'][2]['actual_sha256']==g['cases'][3]['actual_sha256'],'full/retained/repeat buffers')
for s in g['cases']:
    require(s['passed'] and s['width']==2736 and s['height']==4096,'target')
    require(s['other_page_exact'] and s['integrity'],'depth/page isolation')
require(all(v['differences']==0 for s in g['old_order_comparisons'] for v in s['buffers'].values()),'this sample old-order comparison')
c=read('checks.json');require(c['passed'] and c['groups']==['python','native','gpu'],'local checks')
require(c['python']['passed'] and c['python']['tests']==424 and c['python']['skipped']==0,'Python checks')
require(c['native_tests']==52 and c['commands']==149,'native/check inventory')
print('PASS source/hash/aggregate receipts; five retained packets and one completed GPU comparison; live integration remains open')
