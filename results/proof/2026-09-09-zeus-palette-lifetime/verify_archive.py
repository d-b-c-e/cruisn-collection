"""Recompute published route and selected-pixel evidence; raw resources remain local."""
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
def picture(name):
 r=read(name)
 if r['encoding']=='png':im=Image.open(io.BytesIO(data[r['archive_file']])).convert('RGB')
 else:
  assert r['encoding']=='rgb-xor-zlib'
  base=Image.open(io.BytesIO(data[r['base_file']])).convert('RGB')
  delta=zlib.decompress(data[r['archive_file']]);assert len(delta)==3840*2160*3
  rgb=np.bitwise_xor(np.frombuffer(base.tobytes(),np.uint8),np.frombuffer(delta,np.uint8)).tobytes()
  im=Image.frombytes('RGB',(3840,2160),rgb)
 assert im.size==(3840,2160) and sha(im.tobytes())==r['rgb_sha256']
 return im
def equal(a,b):return ImageChops.difference(a,b).getbbox() is None
original=inputs('original/frames.csv');assert len(original)==8860
camera=rows('original/exotica-camera.csv');adc=rows('original/exotica-adc.csv')
assert len(camera)==7051 and len(adc)==21153
specs=[]
for center,first,last,end in [(3600,3576,3624,3800),(4200,4190,4210,4400)]:
 for mode in ('legacy','guard','repeat'):specs.append((f'palette-dense-v2-{center}-{mode}',end,first,last,1,center))
for mode in ('legacy','guard','repeat','upstream'):specs.append(('palette-'+mode,8860,1800,8760,120,None))
for mode in ('guard','repeat'):specs.append(('drain-amazon-'+mode,3650,3576,3624,1,3600))
images={}
for name,end,first,last,every,center in specs:
 prefix='runs/'+name+'/'
 report=read(prefix+'report.json');assert report['passed']
 assert inputs(prefix+'frames.csv')==original[:end]
 assert rows(prefix+'exotica-camera.csv')==[r for r in camera if int(r['frame'])<end]
 assert rows(prefix+'exotica-adc.csv')==[r for r in adc if int(r['frame'])<end]
 complete=rows(prefix+'captures.csv')
 assert [int(c['completed_frame']) for c in complete]==list(range(first,last+1,every))
 assert all(c['completed_frame']==c['last_received_frame'] and c['dropped_messages']=='0'
            and (int(c['width']),int(c['height']))==(3840,2160) for c in complete)
 counter=report['zeus_palette']['result']
 assert counter['guard']==int(not name.endswith('legacy'))
 assert counter['flushes']==(counter['conflicts'] if counter['guard'] else 0)
 if center:images[name]=picture(prefix+'selected.json')
 build='drain' if name.startswith('drain-') else 'palette'
 invocation=read(prefix+'invocation.json')
 assert invocation['executable_sha256']==read('receipts/'+build+'-native-export.json')['candidate_sha256']
 assert invocation['environment']['MIDV_FFB']=='0' and invocation['returncode']==0 and not invocation['error']
for center in (3600,4200):
 legacy,guard,repeat=(images[f'palette-dense-v2-{center}-{mode}'] for mode in ('legacy','guard','repeat'))
 assert not equal(legacy,guard) and equal(guard,repeat)
 repeat_report=read(f'receipts/palette-dense-v2-{center}-repeat-gl.json')
 assert repeat_report['passed'] and repeat_report['frames']==(49 if center==3600 else 21)
 assert len(read(f'receipts/palette-dense-v2-{center}-guard-gl.json')['different_frames'])==(25 if center==3600 else 16)
 for mode in ('guard','repeat'):
  resources=read(f'receipts/palette-dense-v2-{center}-{mode}-resources.json')
  assert resources['passed'] and len(resources['files'])==10
  assert all(v['reference']==v['candidate'] for v in resources['files'].values())
good=picture('original/good.json');bad=picture('original/bad.json')
assert not equal(good,bad) and equal(good,images['palette-dense-v2-3600-guard'])
for name in ('drain-amazon-guard','drain-amazon-repeat'):
 assert equal(good,images[name])
 assert read('receipts/'+name+'-gl.json')['passed']
 assert read('receipts/'+name+'-resources.json')['passed']
 assert read('receipts/'+name+'-geometry.json')['passed']
failure=read('receipts/palette-dense-3600-legacy/report.json')
assert not failure['passed'] and failure['capture_diagnostics']['captured_count']==47
assert failure['capture_diagnostics']['missing_frames']==[3623,3624]
failure=read('receipts/repeat-gl-details.json')
assert not failure['passed'] and failure['different_frames']==[3600]
boundary=read('receipts/drain-boundary-receipt.json')
assert boundary['passed'] and boundary['complete'] and boundary['target']==298 and boundary['wait_ms']>0
stopped=read('receipts/drain-consumer-stop-receipt.json')
assert stopped['passed'] and stopped['expected_failure'] and not stopped['complete'] and stopped['wait_ms']==0
oracle=read('receipts/cpu-legacy-3600-cli-verdict.json')
assert oracle['passed'] and oracle['color']['pixels']==1048576 and oracle['depth']['pixels']==1048576
checks=read('checks/report.json');identity=read('checks/source-identity.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
content=''.join(f'{name}\0{digest}\n' for name,digest in sorted(identity['files'].items())).encode()
assert sha(content)==identity['sha256']==manifest['source_identity'] and len(identity['files'])==415
for name,content in data.items():
 if name.startswith('source/'):assert sha(content.replace(b'\r\n',b'\n'))==identity['files'][name[7:]],name
assert len(checks['steps'])==84 and all(r['returncode']==0 for r in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=276,errors=0,failures=0,skipped=0)
regressions=read('regressions/report.json')
assert regressions['passed'] and len(regressions['cases'])==7
assert regressions['source_identity']==manifest['source_identity']
assert regressions['candidate_sha256']==read('receipts/drain-native-export.json')['candidate_sha256']
for case in regressions['cases']:assert case['passed'] and read('regressions/'+case['id']+'.json')['passed']
print('PASS: twelve original Amazon input/motion prefixes, selected4K palette corrections and retained failures. Full image sequences, native geometry/resources/CPU/GPU/build/seven-default checks remain receipts; no deployment or extended-scenery claim.')
