"""Recompute source/hash identity and scalar receipt consistency only."""
from pathlib import Path
import hashlib,json,sys
d=Path(__file__).resolve().parent;root=d.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import source_identity
read=lambda n:json.loads((d/n).read_text(encoding='utf-8'))
manifest=read('manifest.json')
assert set(manifest)=={p.name for p in d.iterdir() if p.is_file() and p.name!='manifest.json'}
assert all(Path(n).name==n and hashlib.sha256((d/n).read_bytes()).hexdigest()==h for n,h in manifest.items())
identity=read('source-identity.json');assert source_identity(root)==identity
checks=read('local-checks.json');assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==identity['sha256']
assert checks['groups']==['python','native','gpu'] and len(checks['steps'])==140 and all(s['returncode']==0 for s in checks['steps'])
assert sum(s['name'].startswith('run-') for s in checks['steps'])==49
assert read('unit-tests.json')==dict(errors=0,failures=0,passed=True,skipped=0,tests=352)
runs=read('runs.json');assert set(runs)=={'first-draw-amazon','first-draw-amazon-repeat'}
for r in runs.values():
 assert r['input_frames']==8860 and r['physical_ffb']==0 and r['crt']==1 and r['comparison']['passed']
 assert r['native_sha256']=='ca7e814bcb62efa15e2192c857bd4dd24a69fbe8660a895b1a2aafcc5917105c'
 assert r['motion']['passed'] and r['motion']['camera_samples']==[7060,7060] and r['motion']['actual_adc_reads']==[21180,21180]
 assert r['motion']['adc_times_equal'] and r['original_pixels_equal'] and all(a==b for a,b in r['original_traces'].values())
 assert [c['frame'] for c in r['captures']]==list(range(4650,4751,5))
 assert all(c['frame']==c['received'] and c['dropped']==0 and c['size']==[3840,2160] for c in r['captures'])
 c=r['capture'];assert c['complete'] and not c['error'] and c['records']==33876 and c['emissions_seen']==1010130
 assert c['first_draws']==3573 and c['fading_draws']==30308 and c['opaque_transitions']==1126
 j=r['join'];assert j['passed'] and j['fade_trace_exact'] and j['counts']['verified_query_annotations']==33876
 assert (j['ordinary_allocations'],j['ordinary_first_draws'],j['ordinary_never_submitted'])==(3932,3487,445)
 assert (j['first_draw_fading'],j['first_draw_opaque'])==(1115,2372) and not j['changed_immutable_fields']
a,b=runs.values();assert a['captures']==b['captures'] and a['join']==b['join']
repeat=read('repeat.json');assert repeat['passed'] and len(repeat['files'])==8 and all(a==b for a,b in repeat['files'].values())
delays=read('first-draw-delays.json');assert len(delays)==3487
frames=sorted(r[3]-r[2] for r in delays);seconds=sorted(r[4] for r in delays)
def stats(v):return dict(min=v[0],median=v[len(v)//2],p90=v[int(len(v)*.9)],max=v[-1])
assert stats(frames)==a['join']['delay_frames'] and stats(seconds)==a['join']['delay_seconds']
assert sum(r[5] for r in delays)==1115 and sum(f>60 for f in frames)==2801
native=read('native-lifetimes.json');assert native['passed'] and native['full_check_binary'] and native['events']==86376
assert (native['pool_transitions'],native['section_bindings'],native['submissions'])==(48481,4018,33876)
assert native['unknown_frees']==26 and native['normalized_output_sha256']==native['python_output_sha256']
waiting=read('waiting-native.json');assert waiting['passed'] and len(waiting['cases'])==30 and len(waiting['rejected'])==9
assert {(c['frame'],c['multiplier'],c['complete_fade']) for c in waiting['cases']}=={(f,m,a) for f in (3900,5072,5644,6330,7187) for m in (1,2,3) for a in (0,1)}
assert all(c['native']['passed'] and len(c['hashes'])==2 for c in waiting['cases'])
original=read('original-gpu.json');assert original['passed'] and len(original['cases'])==2
assert all(c['passed'] and c['actual_sha256']==c['expected_sha256'] and c['color_differences']==c['depth_differences']==0 for c in original['cases'])
for name in ('waiting-gpu-current.json','waiting-gpu-completed.json'):
 r=read(name);assert r['passed'] and len(r['cases'])==4
 assert [c['insertion']['multiplier'] for c in r['cases']]==[1,2,3,3]
 assert all(c['passed'] and c['insertion']['other_page_exact'] and c['insertion']['integrity'] for c in r['cases'])
 assert r['cases'][2]['actual_sha256']==r['cases'][3]['actual_sha256']
p=read('pixels.json');assert p['passed'] and [v['changed_rgb_vs_future_only'] for v in p['checks']]==[16792,0,118226,118409]
assert all(v['newly_black']==0 for v in p['checks'])
failures=read('retained-failures.json');assert len(failures)==2 and all(v['passed'] is False for v in failures.values())
print('PASS source/file hashes, delay recomputation and receipt consistency; raw execution/geometry/pixels not repeated')
