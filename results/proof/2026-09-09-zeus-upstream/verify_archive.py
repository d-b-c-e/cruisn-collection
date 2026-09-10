"""Recompute public inputs/motion/selected pixels; raw-resource/build gates remain receipts."""
from pathlib import Path
from decimal import Decimal
import csv,hashlib,io,json,zipfile,zlib
import numpy as np
from PIL import Image,ImageChops
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
 trace=rows(name);assert [int(r['frame']) for r in trace]==list(range(1,len(trace)+1))
 return [(int(r['frame']),Decimal(r['emulated_seconds']),tuple((k,v) for k,v in r.items() if k.startswith(':'))) for r in trace]
original=inputs('original/amazon.csv');assert len(original)==8860
controls=None;images={}
for name,mask in [('legacy',0),('depth',1),('alpha',2),('blend',4),('all',7),('all-repeat',7)]:
 prefix=f'runs/amazon/{name}/';report=read(prefix+'report.json')
 assert report['passed'] and report['zeus_upstream']['mask']==mask
 assert inputs(prefix+'frames.csv')==original
 camera=rows(prefix+'exotica-camera.csv');adc=rows(prefix+'exotica-adc.csv')
 assert len(camera)==7051 and len(adc)==21153
 assert [int(r['frame']) for r in camera]==list(range(1800,8851))
 if controls is None:controls=(camera,adc)
 else:assert controls==(camera,adc)
 complete=rows(prefix+'captures.csv')
 assert [int(c['completed_frame']) for c in complete]==list(range(1800,8761,120))
 assert all(c['completed_frame']==c['last_received_frame'] and c['dropped_messages']=='0' and (int(c['width']),int(c['height']))==(3840,2160) for c in complete)
 selected=read(prefix+'captures.json');assert [int(r['completed_frame']) for r in selected]==[2520,7200]
 images[name]={}
 for r in selected:
  frame=int(r['completed_frame'])
  assert {k:r[k] for k in complete[0]}==next(c for c in complete if int(c['completed_frame'])==frame)
  if r['encoding']=='png':im=Image.open(io.BytesIO(data[r['archive_file']])).convert('RGB')
  else:
   assert r['encoding']=='rgb-xor-zlib'
   base=Image.open(io.BytesIO(data[r['base_file']])).convert('RGB')
   delta=zlib.decompress(data[r['archive_file']]);assert len(delta)==3840*2160*3
   rgb=np.bitwise_xor(np.frombuffer(base.tobytes(),np.uint8),np.frombuffer(delta,np.uint8)).tobytes()
   im=Image.frombytes('RGB',(3840,2160),rgb)
  assert im.size==(3840,2160) and sha(im.tobytes())==r['rgb_sha256']
  images[name][frame]=im
 for kind in ('geometry','resources'):assert read(f'receipts/upstream-{name}-{kind}.json')['passed']
 geometry=read(f'receipts/upstream-{name}-geometry.json')
 assert geometry['models']==223 and geometry['total_quads']==3380 and geometry['native']['passed']
for frame in (2520,7200):
 assert ImageChops.difference(images['legacy'][frame],images['alpha'][frame]).getbbox() is None
 assert ImageChops.difference(images['all'][frame],images['all-repeat'][frame]).getbbox() is None
 assert bool(ImageChops.difference(images['legacy'][frame],images['blend'][frame]).getbbox())==(frame==2520)
assert ImageChops.difference(images['legacy'][7200],images['all'][7200]).getbbox() is None
cpu_control=None
for name in ('legacy','all'):
 prefix=f'cpu/{name}/';report=read(prefix+'report.json')
 assert not report['passed'] and report['comparison']['input_or_time_mismatches']==0
 assert report['comparison']['pixel_mismatches']>0 and report['evidence']['frames']==3650
 assert inputs(prefix+'frames.csv')==original[:3650]
 current=(rows(prefix+'exotica-camera.csv'),rows(prefix+'exotica-adc.csv'))
 assert len(current[0])==1850 and len(current[1])==5550
 if cpu_control is None:cpu_control=current
 else:assert cpu_control==current
 assert current[0]==controls[0][:1850] and current[1]==controls[1][:5550]
 oracle=read(prefix+'oracle.json');assert oracle['passed'] and oracle['palettes']==288
 assert oracle['color']['differing_pixels']==oracle['depth']['differing_pixels']==0
regressions=read('regressions/report.json')
assert regressions['passed'] and len(regressions['cases'])==7
assert regressions['source_identity']==manifest['source_identity']
for case in regressions['cases']:assert case['passed'] and read('regressions/'+case['id']+'.json')['passed']
assert read('receipts/upstream-repeat-gl.json')['passed']
assert read('receipts/upstream-alpha-gl.json')['passed']
assert read('receipts/upstream-blend-gl.json')['different_frames']==[2520,2640,2760,2880]
failure=read('receipts/repeat-gl-details.json');assert not failure['passed'] and failure['different_frames']==[3600]
assert read('receipts/palette-lifetime.json')['passed'] and read('receipts/palette-captured.json')['passed']
checks=read('checks/report.json');identity=read('checks/source-identity.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==409
for name,content in data.items():
 if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==81 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=273,errors=0,failures=0,skipped=0)
print('PASS: six full Amazon input/motion traces, two CPU prefixes and two selected4K windows per policy. Hong Kong/geometry/resources/59GL/native/GPU/CPU pixels/default gates remain receipts. Original intermittent3600 failure remains open; no deployment or extra-scenery claim.')
