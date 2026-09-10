"""Verify archived receipts, not unarchived native execution or game pixels."""
from pathlib import Path
import hashlib,json

root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
m=read('manifest.json')
for name,digest in m['files'].items():
    path=(root/name).resolve()
    assert path.is_relative_to(root.resolve()) and hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
assert len(m['files'])==58
checks=read('checks/report.json');units=read('checks/unit-tests.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==m['source_identity']
assert len(checks['steps'])==96 and all(r['returncode']==0 for r in checks['steps'])
assert units==dict(errors=0,failures=0,passed=True,skipped=0,tests=291)
identity=read('checks/source-identity.json')
payload=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']==m['source_identity']
assert m['changed_files_since_native_acceptance']==['harness/verify_exotica_future.py','tests/test_exotica_future_evidence.py']
for frame,images,instances,polygons in [(5000,21,1515,9596),(5072,17,1622,16408),(5990,17,818,5478)]:
    prefix=f'scene{frame}-'
    for kind in ('control','source'):
        motion=read(prefix+kind+'-motion.json')
        assert motion['passed'] and motion['camera_equal'] and motion['adc_times_equal']
        assert motion['camera_samples']==[4191,4191] and motion['actual_adc_reads']==[12573,12573]
    gl=read(prefix+'gl.json');assert gl['passed'] and gl['frames']==images and not gl['different_frames']
    resources=read(prefix+'resources.json');assert resources['passed'] and len(resources['files'])==10
    assert all(a==b for a,b in resources['files'].values())
    geometry=read(prefix+'future-native.json')['native']
    assert geometry['passed'] and geometry['models']==instances and geometry['covered_quads']==geometry['total_quads']==polygons
    wire=read(prefix+'future-wire.json')
    assert not wire['errors'] and wire['counts']['instances']==instances and wire['counts']['polygons']==polygons
    for tool in ('verify_exotica_transforms','verify_exotica_state','verify_zeus_state','verify_zeus_models','verify_exotica_future'):
        suffix='-v2' if frame==5072 and tool=='verify_exotica_future' else ''
        assert read(prefix+tool+suffix+'.json')['passed']
    for kind in ('','unsubmitted-'):
        composition=read(prefix+kind+'occlusion-v3.json')
        assert composition['passed'] and composition['original_depth_unchanged']
        assert composition['repeat_multipliers']==[2,0] and composition['additional_color_changes_3_over_2']==0
        assert composition['color_changed_over_control']['2']==composition['color_changed_over_control']['3']
assert read('scene5000-occlusion-v3.json')['additional_color_changes_2_over_1']==1
assert read('scene5072-occlusion-v3.json')['additional_color_changes_2_over_1']==1790
assert read('scene5072-unsubmitted-occlusion-v3.json')['additional_color_changes_2_over_1']==8762
for failure in ('depth-layer-prototype-failure','scene5072-verify_exotica_future','scene5072-occlusion-failure','scene5072-occlusion-v2-failure'):
    assert read(failure+'.json')['passed'] is False
depth=read('depth-layer-prototype-v2.json');assert depth['passed'] and depth['actual_float_roundtrip_exact']
assert any(not r['order_independent'] for r in depth['cases'][0]['pairs'])
assert all(r['order_independent'] for r in depth['cases'][1]['pairs'])
ground=read('scene5072-ground-roi.json')['cases']
assert ground[0]['black_before']==ground[0]['black_after']==ground[1]['black_before']==1951
assert ground[1]['black_after']==0
print('PASS 58 hash-bound receipts. Raw executions, pixels, geometry and routes are not recomputed.')
