"""Public scalar, selected-pixel and telemetry proof; raw resources stay local."""
from pathlib import Path
import csv
from decimal import Decimal
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import zipfile
from PIL import Image, ImageChops

root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text())
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as archive:
    assert len(archive.namelist())==len(set(archive.namelist()))
    assert set(archive.namelist())==set(manifest['files'])
    data={name:archive.read(name) for name in archive.namelist()}
for name,digest in manifest['files'].items():assert sha(data[name])==digest,name
read=lambda name:json.loads(data[name])
rows=lambda name:list(csv.DictReader(io.StringIO(data[name].decode())))

def inputs(name):
    trace=rows(name)
    assert [int(r['frame']) for r in trace]==list(range(1,len(trace)+1))
    return [(int(r['frame']),Decimal(r['emulated_seconds']),tuple((k,v) for k,v in r.items() if k.startswith(':'))) for r in trace]
original=inputs('original/frames.csv')[:6000]
control=rows('runs/control/exotica-camera.csv');adc=rows('runs/control/exotica-adc.csv')
assert len(control)==4191 and [int(r['frame']) for r in control]==list(range(1800,5991))
assert len(adc)==12573 and all(0x9c0000<=int(r['address'],16)<=0x9c000f for r in adc)
assert all(Decimal(b['time'])>=Decimal(a['time']) for a,b in zip(adc,adc[1:]))
images={}
resources=read('runs/control/report.json')['zeus_capture']['sha256']
for name in manifest['runs']:
    prefix='runs/'+name+'/'
    assert inputs(prefix+'frames.csv')==original
    assert rows(prefix+'exotica-camera.csv')==control
    assert rows(prefix+'exotica-adc.csv')==adc
    report=read(prefix+'report.json');assert report['passed']
    if name in ('control','sources-4700','repeat-4700'):assert report['zeus_capture']['sha256']==resources
    complete=rows(prefix+'captures.csv')
    assert [int(c['completed_frame']) for c in complete]==list(range(5400,5421))
    assert all(int(c['completed_frame'])==int(c['last_received_frame']) and int(c['dropped_messages'])==0 and (int(c['width']),int(c['height']))==(3840,2160) for c in complete)
    captures=read(prefix+'captures.json');assert [int(r['completed_frame']) for r in captures]==[5400,5410,5420]
    for row in captures:
        frame=int(row['completed_frame'])
        assert {k:v for k,v in row.items() if k!='sha256'}==next(v for v in complete if int(v['completed_frame'])==frame)
        im=Image.open(io.BytesIO(data['images/'+row['sha256']+'.png'])).convert('RGB');assert im.size==(3840,2160)
        if name=='control':images[frame]=im
        else:assert ImageChops.difference(images[frame],im).getbbox() is None
total=[0]*7
for name in ('sources-3500-oracle','oracle-4700-final','sources-5410-oracle','repeat-4700-oracle'):
    r=read('receipts/'+name+'.json');n=r['native']
    assert r['passed'] and n['passed'] and r['covered_quads']==r['total_quads']==n['covered_quads']==n['total_quads']
    assert r['models']==n['models']==sum(r['quad_sizes'].values())
    assert n['polygons']==r['counts']['cmd0x38']==n['covered_quads']+n['backfaces']+n['near_rejected']
    if name!='repeat-4700-oracle':
        for i,key in enumerate(('models','polygons','covered_quads','near_rejected','backfaces','near_clipped','register_writes')):total[i]+=n[key]
assert total==[939,13876,8126,131,5619,50,1732]
first=read('receipts/oracle-4700-final.json');repeat=read('receipts/repeat-4700-oracle.json')
assert first['sources']==repeat['sources'] and first['native']==repeat['native']
assert read('receipts/acceptance.json')['passed']
assert not read('failures/initial-geometry-summary.json')['passed']
export=read('receipts/native-export.json');assert export['passed'] and export['patch_count']==147
assert export['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
checks=read('checks/report.json');reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==reg['source_identity']==manifest['source_identity']
identity=read('checks/source-identity.json')
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==384
for name,content in data.items():
    if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==69 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=257,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['candidate_sha256']=='ee2bd4d0070f3b2126c9971b30074e1160bc3f4bece76839f30559a9cff0017f'
with tempfile.TemporaryDirectory(prefix='cruisn-exotica-model-proof-') as temporary:
    extracted=Path(temporary)
    assert extracted.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
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
print('PASS: five input/motion traces, three selected4K images per run, seven telemetry/four software-force verdicts. Full geometry/state, resources, remainingGL and builds remain receipts.')
