"""Verify publishable host-road evidence without ROMs. Requires Pillow.

Full geometry/resources, unbundled GL images and native/GPU builds are receipts.
Only the explicitly archived pixels, driving traces and telemetry are recomputed.
"""
from pathlib import Path
import csv,io,json,hashlib,zipfile,tempfile,sys,importlib.util
from PIL import Image,ImageChops
root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['files'])
    data={n:z.read(n) for n in z.namelist()}
for n,digest in manifest['files'].items():assert sha(data[n])==digest,n
read=lambda n:json.loads(data[n])
rows=lambda n:list(csv.DictReader(io.StringIO(data[n].decode())))
reference=None;fingerprints=None
for name in ['roads-off-full-4k','roads-full-4k','roads-repeat-full-4k']:
    prefix='runs/'+name+'/'
    r=read(prefix+'report.json');assert r['passed'] and r['comparison']['passed']
    frames=rows(prefix+'frames.csv');assert [int(v['frame']) for v in frames]==list(range(1,9270))
    keys=[k for k in frames[0] if k not in ('host_seconds','speed_percent')]
    values=(keys,[[v[k] for k in keys] for v in frames])
    if reference is None:reference=values
    assert values==reference
    for file in ['world-camera.csv','world-adc.csv']:
        assert data[prefix+file]==data['runs/roads-off-full-4k/'+file]
    scenes=rows(prefix+'world-host-scenes.csv')
    assert len(scenes)==3731 and all(r['roads_enabled']==('0' if name=='roads-off-full-4k' else '1') for r in scenes)
    if name!='roads-off-full-4k':
        values=[[r[k] for k in ['frame','page','quads','quads_hash','road_objects','road_quads']] for r in scenes]
        if fingerprints is None:fingerprints=values
        assert values==fingerprints
        assert sum(int(r['quads']) for r in scenes)==10094461
for name in ['observe-full','tunnel-on','tunnel-on-v2','tunnel-on-v3']:assert not read('failures/'+name+'.json')['passed']
assert not read('receipts/tunnel-motion.json')['passed']
assert read('receipts/tunnel-motion.json')['first_camera_difference_frame']==3108
assert read('receipts/tunnel-fixed-motion.json')['passed'] and read('receipts/full-motion.json')['passed']
assert read('receipts/tunnel-resources.json')['passed']
tunnel=read('receipts/tunnel-fixed-compare.json')
assert not tunnel['passed'] and tunnel['gl']['passed'] and tunnel['gl']['frames']==51 # no tunnel benefit, preserves existing image
benefit=read('receipts/road-benefit.json');repeat=read('receipts/road-repeat.json')
assert benefit['passed'] and len(benefit['gl']['different_frames'])==18
assert repeat['passed'] and repeat['gl']['passed'] and repeat['gl']['frames']==21 and repeat['host_scene_fingerprints_equal']
for frame in [6560,6720]:
    a,b=[Image.open(io.BytesIO(data[f'images/{name}-{frame}.png'])).convert('RGB') for name in ['roads-off-full-4k','roads-full-4k']]
    assert a.size==b.size==(3824,2073)
    channels=ImageChops.difference(a,b).split()
    mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
    receipt=next(r for r in benefit['gl']['pixel_changes'] if r['frame']==frame)
    assert a.width*a.height-mask.histogram()[0]==receipt['changed_pixels']
    assert list(mask.getbbox())==receipt['bounds_xyxy_exclusive']
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==reg['source_identity']==manifest['source_identity']
assert len(checks['steps'])==44 and all(s['returncode']==0 for s in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=204,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='a2fbecfb4179a4a00f4fa90795b10729f7f178b62a7c07166be1834c76877148'
with tempfile.TemporaryDirectory(prefix='cruisn-roads-proof-') as temporary:
    extracted=Path(temporary)
    assert extracted.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()) and extracted.name.startswith('cruisn-roads-proof-')
    for name,content in data.items():
        if name.startswith(('tools/','regressions/')):
            path=extracted/name;assert path.resolve().is_relative_to(extracted.resolve())
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    sys.path.insert(0,str(extracted/'tools'))
    def module(name):
        spec=importlib.util.spec_from_file_location('archived_'+name,extracted/'tools'/(name+'.py'))
        result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
    drivetrain=module('analyze_drivetrain');force=module('analyze_force_gate');force_count=0
    for case,expected in zip(plan['cases'],reg['cases']):
        assert case['id']==expected['id'] and expected['passed']
        path=extracted/'regressions'/case['id'];config=case['telemetry'];memory=path/config['memory']
        actual=drivetrain.analyze(path,memory)
        actual['coverage_passed']=actual['game_state_samples']>=config.get('minimum_active_frames',500) and actual['wire']['maximum_speed_mph']>=config.get('minimum_speed_mph',10)
        assert json.loads(json.dumps(actual))==expected['telemetry'],case['id']
        if config.get('force_gate_game'):
            actual=force.analyze(path,memory,config['force_gate_game'],config.get('force_gate_policy','driving'),config.get('force_polarity',False))
            assert json.loads(json.dumps(actual))==expected['force_gate'],case['id'];force_count+=1
    assert force_count==4
for name in ['snapshot-roads','snapshot-legacy','tunnel-native-oracle','gap-native-oracle','math','world25-prototype']:
    assert read('receipts/'+name+'.json')['passed']
export=read('receipts/native-export.json');assert export['passed'] and export['patch_count']==139
assert export['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
print('PASS: three full driving traces, repeated host fingerprints, two selected 4K pairs, seven telemetry/four force verdicts. Remaining GPU/geometry/native checks are receipts; no cross-game parity or deployment claim.')
