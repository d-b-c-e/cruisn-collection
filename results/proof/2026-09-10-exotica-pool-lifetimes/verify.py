"""Source/hash and receipt consistency; raw lifetime reconstruction stays local."""
from pathlib import Path
import hashlib
import json
import sys
d = Path(__file__).resolve().parent
root = d.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import source_identity
read = lambda name: json.loads((d/name).read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = read('manifest.json')
assert set(manifest) == {p.name for p in d.iterdir() if p.is_file() and p.name != 'manifest.json'}
for name,digest in manifest.items():
    assert Path(name).name == name and sha(d/name) == digest
assert source_identity(root) == read('source-identity.json')
runs = read('runs.json')
assert set(runs) == {'pool-owner-amazon-reset','pool-owner-amazon-repeat'}
for name,r in runs.items():
    assert r['native_sha256'] == 'ca7e814bcb62efa15e2192c857bd4dd24a69fbe8660a895b1a2aafcc5917105c'
    assert r['input_frames'] == 8860 and r['comparison']['passed'] and r['physical_ffb'] == 0 and r['crt'] == 1
    assert r['comparison']['input_or_time_mismatches'] == r['comparison']['pixel_mismatches'] == 0
    assert r['motion']['passed'] and r['motion']['camera_samples'] == [7060,7060]
    assert r['motion']['actual_adc_reads'] == [21180,21180] and r['motion']['adc_times_equal']
    assert r['original_pixels_equal'] and [v['frame'] for v in r['captures']] == list(range(4650,4751,5))
    assert all(v['frame'] == v['received'] and v['dropped'] == 0 and v['size'] == [3840,2160] for v in r['captures'])
    assert all(a == b for a,b in r['original_traces'].values())
    p = r['pool']
    assert p['complete'] and not p['error'] and p['events'] == 48481
    assert (p['allocations'],p['frees'],p['resets']) == (24693,23787,1)
    j = r['join']
    assert j['passed'] and j['pool_events'] == p['events']
    assert j['counts']['section_allocations_joined'] == 4018 and j['counts']['fades_in_same_live_generation'] == 2539
    assert j['counts']['other_pool_allocations'] == 20675 and j['counts']['live_generations_invalidated_by_reset'] == 882
    assert j['distinct_faded_generations'] == 116
a,b = runs.values()
assert a['captures'] == b['captures'] and a['join']['lifetime_join_sha256'] == b['join']['lifetime_join_sha256']
repeat = read('repeat.json')
assert repeat['passed'] and len(repeat['files']) == 6 and all(a == b for a,b in repeat['files'].values())
prefix = read('prefixes.json')
assert prefix['passed'] and [r['events'] for r in prefix['checks']] == [40000,48430]
assert all(r['equal'] for r in prefix['checks'])
failures = read('retained-failures.json')
assert [r['stopped_frame'] for r in failures.values()] == [5888,8443]
print('PASS source, capture/hash pairs and lifetime receipt consistency; raw reconstruction is not repeated')
