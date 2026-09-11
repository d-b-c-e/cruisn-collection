"""Source and scalar/hash receipt consistency; raw execution is not repeated."""
from pathlib import Path
import hashlib
import json
import sys

d = Path(__file__).resolve().parent
root = d.parents[2]
sys.path.insert(0, str(root / 'harness'))
from release_identity import source_identity
read = lambda name: json.loads((d / name).read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = read('manifest.json')
assert set(manifest) == {p.name for p in d.iterdir() if p.is_file() and p.name != 'manifest.json'}
for name, digest in manifest.items():
    assert Path(name).name == name and sha(d / name) == digest
identity = read('source-identity.json')
assert source_identity(root) == identity
checks = read('checks.json')
assert checks['passed'] and checks['unit'] == dict(errors=0, failures=0, passed=True, skipped=0, tests=352)
assert checks['native_programs'] == 48 and checks['commands'] == 136 and checks['source_identity'] == identity['sha256']
build = read('native-build.json')
assert build['passed'] and build['patch_count'] == 184
assert sha(root / 'patch/vunit-poc-patches.patch') == build['patch_sha256']
runs = read('presentation.json')
assert set(runs) == {'packet-present2', 'packet-present3', 'packet-present3-repeat'}
for name, run in runs.items():
    assert run['native_sha256'] == build['candidate_sha256'] and run['physical_ffb'] == 0 and run['crt'] == 1
    assert run['input_frames'] == 8860 and run['comparison']['passed']
    assert run['comparison']['input_or_time_mismatches'] == run['comparison']['pixel_mismatches'] == 0
    assert run['captures'][0] == run['captures'][1]
    assert [row['frame'] for row in run['captures'][0]] == list(range(1800, 8761, 30))
    assert all(row['frame'] == row['received'] and row['dropped'] == 0 and row['size'] == [3840, 2160]
               for row in run['captures'][0])
    assert run['motion']['passed'] and run['motion']['camera_samples'] == [7060, 7060]
    assert run['motion']['actual_adc_reads'] == [21180, 21180] and run['motion']['adc_times_equal']
    assert len(run['resources']['files']) == 10 and all(a == b for a, b in run['resources']['files'].values())
    assert run['identity']['passed'] and len(run['identity']['completed']) == 14 and len(run['identity']['immediate']) == 5
    assert all(row['rows'] == 6953 for row in run['identity']['streams'].values())
    assert run['oracles']['passed'] and [row['frame'] for row in run['oracles']['samples']] == [3900, 5072, 5644, 6330, 7187]
    assert all(row['passed'] and row['color_differences'] == row['depth_differences'] == 0 for row in run['oracles']['samples'])
fade = read('fade.json')
assert fade['passed'] and fade['original_pixels_equal'] and fade['completed_images'] == 21
assert fade['capture'] == dict(complete=True, error=None, allocations=4018, fades=2539, unowned=0)
assert fade['fade']['passed'] and fade['fade']['events'] == 2539 and fade['fade']['native_verified']
assert fade['fade']['counts']['completed'] == 86
assert fade['analysis']['counts']['reused_slots'] == 3221 and fade['analysis']['distinct_faded_allocations'] == 116
assert fade['future_join']['passed'] and len(fade['future_join']['results']) == 3
for row in fade['future_join']['results']:
    assert row['descriptors'] == 4286 and row['native_python_equal'] and row['failure_count'] == 0
    assert row['counts']['allocation_equal'] == 3932 and row['counts']['custom_excluded'] == 86
    assert row['counts']['fade_equal'] == 2539 and row['faded_owners'] == 116
performance = read('performance.json')
assert performance['passed'] and len(performance['runs']) >= 3
for row in performance['runs'].values():
    assert 0 < row['speed_percent'] <= 110 and row['motion']['passed']
    assert all(value['rows'] == 6953 and value['passed'] for value in row['geometry'].values())
print('PASS source, capture/hash pairs and scalar receipt consistency; raw execution/geometry/pixels remain receipts')
