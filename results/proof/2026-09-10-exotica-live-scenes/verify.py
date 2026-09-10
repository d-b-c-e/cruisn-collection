"""Verify archived receipt hashes/consistency; raw game execution stays local."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).parent
read = lambda name: json.loads((root/name).read_text(encoding='utf-8'))
manifest = read('manifest.json')
for name, digest in manifest['files'].items():
    path = (root/name).resolve()
    assert path.is_relative_to(root.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
checks = read('checks/report.json');identity = read('checks/source-identity.json')
payload = ''.join(f'{name}\0{digest}\n' for name, digest in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest() == identity['sha256'] == manifest['source_identity']
assert len(identity['files']) == 448
assert checks['passed'] and checks['source_identity'] == checks['source_identity_after'] == identity['sha256']
assert len(checks['steps']) == 99 and all(s['returncode'] == 0 for s in checks['steps'])
assert read('checks/unit-tests.json') == dict(errors=0, failures=0, passed=True, skipped=0, tests=301)
native = read('native-export.json')
assert native['passed'] and native['patch_count'] == 161
assert native['native_commit'] == 'f49e8acc7d3b2da5beb0c7815804fa0a79117ab0'
assert native['candidate_sha256'] == '9c7dcd272ea609e1b28fa86c9cdd07f2dfca0b089edcbf198e3dfee8caa1d606'
assert native['personal_sha256'] == '87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
for frame, images, counts in ((5000, 21, (1515, 9595, 4740)),
                               (5072, 17, (1611, 16335, 401)),
                               (5990, 17, (818, 5478, 452))):
    for mode in ('control', 'observe'):
        run = read(f'{frame}/{mode}-run.json');assert run['passed']
        gl = read(f'{frame}/{mode}-gl.json')
        assert gl['passed'] and gl['different_frames'] == [] and gl['frames'] == images
        motion = read(f'{frame}/{mode}-motion.json')
        assert motion['passed'] and motion['camera_equal'] and motion['adc_times_equal']
        assert motion['adc_frame_value_pc_equal'] and motion['camera_samples'] == [4191, 4191]
        assert motion['actual_adc_reads'] == [12573, 12573]
    run = read(f'{frame}/observe-run.json')['exotica_host_scene']['result']
    assert run['passed'] and run['scenes'] == 2457 and run['guest_cycles_unchanged'] and run['game_scene_boundary']
    resources = read(f'{frame}/resources.json')
    assert resources['passed'] and len(resources['files']) == 10
    assert all(a == b for a, b in resources['files'].values())
    oracle = read(f'{frame}/oracle.json')
    assert oracle['passed'] and oracle['immutable_inputs'] and oracle['original_context']['exact_context']
    assert oracle['game_scene_boundary']['passed'] and oracle['game_scene_boundary']['first_supported_model']
    assert tuple(oracle['counts'][k] for k in ('instances', 'quads', 'viewport_quads')) == counts
for name, quads in (('boundary5072-repeat.json', 20343986), ('boundary-hongkong-repeat.json', 30411603)):
    repeat = read(name);assert repeat['passed'] and repeat['scenes'] == 2457 and repeat['quads'] == quads
bounds = read('bounds-prototype.json')
assert bounds['passed'] and len(bounds['cases']) == 3
assert all(c['passed'] and c['false_rejections'] == 0 for c in bounds['cases'])
draft = read('bounds-native-draft.json')
assert draft['passed'] and draft['native_python_exact'] and draft['cases'] == 3955 and draft['culled'] == 3000
print(f"PASS {len(manifest['files'])} hash-bound receipts; raw geometry/resources/pixels are not recomputed.")
