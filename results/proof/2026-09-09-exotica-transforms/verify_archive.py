"""Recompute publishable input/motion/pixel evidence; raw transform operands are local."""
from pathlib import Path
import csv,hashlib,io,json,zipfile
from decimal import Decimal
from PIL import Image,ImageChops

root=Path(__file__).parent
manifest=json.loads((root/'manifest.json').read_text())
digest=lambda b:hashlib.sha256(b).hexdigest()
assert digest((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as archive:
 data={name:archive.read(name) for name in archive.namelist()}
assert set(data)==set(manifest['files'])
for name,value in data.items():assert digest(value)==manifest['files'][name],name
read=lambda name:json.loads(data[name])
def csv_rows(name):return list(csv.DictReader(io.StringIO(data[name].decode())))
def inputs(name):
 rows=csv_rows(name);assert [int(r['frame']) for r in rows]==list(range(1,len(rows)+1))
 return [(int(r['frame']),Decimal(r['emulated_seconds']),tuple((k,v) for k,v in r.items() if k.startswith(':'))) for r in rows]
original=inputs('original/frames.csv')[:6000]
control=csv_rows('runs/control/exotica-camera.csv');adc=csv_rows('runs/control/exotica-adc.csv')
assert len(control)==4191 and [int(r['frame']) for r in control]==list(range(1800,5991))
assert len(adc)==12573 and all(0x9c0000<=int(r['address'],16)<=0x9c000f for r in adc)
assert all(Decimal(b['time'])>=Decimal(a['time']) for a,b in zip(adc,adc[1:]))
images={}
resources=read('runs/control/report.json')['zeus_capture']['sha256']
for name in manifest['runs']:
 assert inputs('runs/'+name+'/frames.csv')==original
 assert csv_rows('runs/'+name+'/exotica-camera.csv')==control
 assert csv_rows('runs/'+name+'/exotica-adc.csv')==adc
 report=read('runs/'+name+'/report.json');assert report['passed'] and report['zeus_capture']['sha256']==resources
 rows=read('runs/'+name+'/captures.json');assert [int(r['completed_frame']) for r in rows]==[5400,5410,5420]
 for row in rows:
  frame=int(row['completed_frame']);im=Image.open(io.BytesIO(data['images/'+row['sha256']+'.png'])).convert('RGB')
  assert im.size==(3840,2160)
  if name=='control':images[frame]=im
  else:assert ImageChops.difference(images[frame],im).getbbox() is None
receipt=read('receipts/canonical-native-v2.json')
assert receipt['passed'] and receipt['native_verified']
assert (receipt['calls'],receipt['ordinary_emissions'],receipt['special_transforms_only'])==(40093,39541,552)
assert receipt['matrix_updates']==13693 and receipt['far_model_selections']==3051
assert receipt['emissions_crossing_native_frame']==2
assert not read('failures/initial-transform-summary.json')['passed']
for name in ('canonical-python-v1.json','canonical-python-v2.json','canonical-native.json'):
 assert not read('receipts/'+name)['passed']
checks=read('checks/report.json');assert checks['passed']
assert checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
for name,value in checks['artifacts'].items():assert digest(data['checks/'+name])==value
assert read('checks/unit-tests.json')['tests']==253 and read('checks/unit-tests.json')['skipped']==0
print('PASS: four input/motion traces, three selected4K images per run; transform/resource/build/GPU results remain receipts.')
