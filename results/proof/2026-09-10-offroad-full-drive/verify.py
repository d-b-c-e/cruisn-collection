"""Check source identity and scalar/hash receipt consistency, not raw MAME output."""
from pathlib import Path
import hashlib,json,sys
d=Path(__file__).resolve().parent;root=d.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import source_identity
read=lambda name:json.loads((d/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read('manifest.json')
assert set(manifest)=={p.name for p in d.iterdir() if p.is_file() and p.name!='manifest.json'}
for name,digest in manifest.items():assert Path(name).name==name and sha(d/name)==digest,name
identity=read('source-identity.json');assert source_identity(root)==identity
checks=read('checks.json');assert checks['passed'] and checks['unit']==dict(errors=0,failures=0,passed=True,skipped=0,tests=352)
assert checks['native_programs']==48 and checks['commands']==136 and checks['source_identity']==identity['sha256']
runs=read('runs.json');assert len(runs)==7
reference=runs['original-control'];expected=list(range(1800,9601,120))
def images(r):return {c['frame']:c['sha256'] for c in r['captures']}
for name,r in runs.items():
 assert r['replay_passed'] and r['comparison']['passed'] and r['comparison']['input_or_time_mismatches']==r['comparison']['pixel_mismatches']==0
 assert r['input_frames']==9644 and r['native_snapshots']==160 and r['physical_ffb']==0
 assert [c['frame'] for c in r['captures']]==expected
 assert all(c['frame']==c['received'] and c['dropped']==0 and c['size']==[3824,2073] for c in r['captures'])
 assert r['motion']==reference['motion']
 assert r['motion']['camera']['rows']==7831 and r['motion']['adc']['rows']==31324
 assert r['motion']['camera']['first']==1800 and r['motion']['camera']['last']==9630
for name in ('original-repeat','candidate-control','failure-scene-control'):
 assert images(runs[name])==images(reference)
assert images(runs['final-frontier-draw3'])==images(runs['final-frontier-repeat3'])
a,b=images(runs['final-frontier-draw2']),images(runs['final-frontier-draw3'])
pair=read('distance-comparison.json');assert pair['frames']==66 and pair['images_identical'] is False
assert pair['different_frames']==[n for n in expected if a[n]!=b[n]] and len(pair['different_frames'])==22
repeat=read('repeat.json');assert repeat['passed'] and repeat['host_equal'] and repeat['gl']['passed']
assert all(r['scenes']==3865 for r in repeat['host'])
prefix=read('prefix.json');assert prefix['passed'] and prefix['equal_completed_prefix_frames']==60 and prefix['equal_ordered_scene_prefix']==3542
trace=read('section-trace.json');assert trace['passed'] and trace['scenes']==3864 and len(trace['partial_frames'])==54
assert [r['frame'] for r in trace['final_section_delays']]==[8987,9087]
assert all(r['lead']==r['actual_lead']+1 and r['front']==r['sections']-1 for r in trace['final_section_delays'])
oracle=read('scene-oracles.json');assert oracle['passed'] and len(oracle['results'])==18
assert all(r['cold_warm_equal'] for r in oracle['results'])
live=read('live-oracle.json');assert live['passed'] and live['scenes']['scenes']==61
assert [r['native_frame'] for r in live['snapshots']]==[8982,8984,8986,9086]
assert [r['quads'] for r in live['snapshots']]==[131,130,132,0]
joined=read('live-full-join.json');assert joined['passed'] and joined['scenes']==61 and joined['quads']==4332
build=read('native-build.json');assert build['passed'] and build['patch_count']==184
assert sha(root/'patch/vunit-poc-patches.patch')==build['patch_sha256']
assert all(runs[n]['native_sha256']==build['candidate_sha256'] for n in ('final-frontier-draw2','final-frontier-draw3','final-frontier-repeat3'))
failure=read('retained-failure.json');assert failure['error']=='emulator exit code 3' and failure['native_frame']==8986 and failure['completed_captures']==60
print('PASS source, capture coverage, hash pairs and receipt consistency; raw execution/pixels/geometry are not recomputed')
