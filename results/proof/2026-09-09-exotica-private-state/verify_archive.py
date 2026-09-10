"""Recompute public motion/pixels; state/raw-resource and build checks are receipts."""
from pathlib import Path
from decimal import Decimal
import csv,hashlib,io,json,zipfile
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
 trace=rows(name)
 assert [int(r['frame']) for r in trace]==list(range(1,len(trace)+1))
 return [(int(r['frame']),Decimal(r['emulated_seconds']),tuple((k,v) for k,v in r.items() if k.startswith(':'))) for r in trace]
for group,names,count,camera_count,adc_count in [('hong-kong',('control','state'),6000,4191,12573),
 ('amazon',('reference','repeat','state'),8860,7051,21153)]:
 original=inputs('original/'+group+'.csv')[:count];control=None;images={}
 for name in names:
  prefix=f'runs/{group}/{name}/'
  assert read(prefix+'report.json')['passed']
  assert inputs(prefix+'frames.csv')==original
  camera=rows(prefix+'exotica-camera.csv');adc=rows(prefix+'exotica-adc.csv')
  assert len(camera)==camera_count and len(adc)==adc_count
  assert [int(r['frame']) for r in camera]==list(range(1800,1800+camera_count))
  assert all(0x9c0000<=int(r['address'],16)<=0x9c000f for r in adc)
  assert all(Decimal(b['time'])>=Decimal(a['time']) for a,b in zip(adc,adc[1:]))
  if control is None:control=(camera,adc)
  else:assert (camera,adc)==control
  if prefix+'captures.csv' not in data:continue
  complete=rows(prefix+'captures.csv')
  expected=list(range(5400,5421)) if group=='hong-kong' else list(range(1800,8761,120))
  assert [int(c['completed_frame']) for c in complete]==expected
  assert all(int(c['completed_frame'])==int(c['last_received_frame']) and int(c['dropped_messages'])==0 and (int(c['width']),int(c['height']))==(3840,2160) for c in complete)
  selected=read(prefix+'captures.json')
  assert [int(r['completed_frame']) for r in selected]==([5400,5410,5420] if group=='hong-kong' else [3600])
  for r in selected:
   frame=int(r['completed_frame'])
   assert {k:v for k,v in r.items() if k!='sha256'}==next(c for c in complete if int(c['completed_frame'])==frame)
   im=Image.open(io.BytesIO(data['images/'+r['sha256']+'.png'])).convert('RGB');assert im.size==(3840,2160)
   if name==names[0]:images[frame]=im
   else:
    changed=ImageChops.difference(images[frame],im).getbbox()
    assert bool(changed)==(group=='amazon' and frame==3600),(group,name,frame)
failure=read('receipts/repeat-gl-details.json')
assert not failure['passed'] and failure['different_frames']==[3600]
assert failure['pixel_changes'][0]['changed_pixels']==1039949
assert not read('receipts/state-canonical-oracle.json')['passed']
for name,calls,contexts in [('state-final',40093,278),('state-native',537,170)]:
 setup=read('receipts/'+name+'-setup.json');context=read('receipts/'+name+'-context.json')
 assert setup['passed'] and setup['native_verified'] and setup['calls']==calls
 assert context['passed'] and context['native_verified'] and context['consecutive_contexts']==contexts
 assert sum(setup['branches'].values())==calls
checks=read('checks/report.json');identity=read('checks/source-identity.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==404
for name,content in data.items():
 if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==78 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=269,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==32
print('PASS: five motion/input traces, selected4K pairs and retained Amazon frame3600 visual FAIL. State/resource/build results remain receipts; no host-drawing or deployment claim.')
