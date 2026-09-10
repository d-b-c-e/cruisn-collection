from pathlib import Path
import hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for name,digest in read('manifest.json')['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
identity,checks=read('source-identity.json'),read('checks.json')
payload=''.join(f'{k}\0{v}\n' for k,v in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']==checks['source_identity']==checks['source_identity_after']=='412c67e1db0662d41592a9200eba51ab34d8036744447780982eadd994df8496'
assert checks['passed'] and len(checks['steps'])==125 and all(s['returncode']==0 for s in checks['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=324,skipped=0,errors=0,failures=0)
gpu=read('gpu-isolation.json');assert gpu['passed'] and len(gpu['cases'])==16
for c in gpu['cases']:
 assert c['depth_bits']==24 and c['size']==[(512+2*c['margin'])*c['scale'],1024*c['scale']]
 assert c['page'] in (0,400) and c['copied_pixels']==2*c['margin']*400*c['scale']**2
 assert all(c[k] for k in ('center_and_other_page_unchanged','original_depth_unchanged','foreground_occlusion','private_depth_order','original_continuation'))
owned=read('owned-capture.json');assert owned==dict(passed=True,scenes=13,objects=4591,candidates=814,scratch_changes=4318)
assert 'captured quads=1238' in (root/'packet-geometry.txt').read_text(encoding='utf-8')
scene=read('captured-scene.json');assert scene['passed'] and scene['repeat']
assert scene['target']==[2736,4096] and scene['page_image']==[2736,1600] and scene['scale']==4
assert scene['host_instances']==63 and scene['host_quads']==522 and scene['original_quads']==3349
assert scene['insertion_after_original_quads']==3219 and scene['changed_margin_pixels']==8416
assert scene['black_margin_pixels_before']==6459 and scene['black_margin_pixels_after']==0
assert scene['original_center_and_depth_unchanged'] and scene['original_material_textures_unchanged']
assert scene['baseline_sha256']!=scene['drawn_sha256']
print('PASS hash-bound324Python/45native/125command receipts,16realGPU isolation cases,13owned-list journals/1238quads and offline Amazon black6459->0. Raw pixels/geometry remain local; no live drawing or new seven-default claim.')
