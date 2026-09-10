from pathlib import Path
import json,csv,hashlib
root=Path(__file__).parent;read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for n,h in read('manifest.json')['files'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
r=read('active-summary.json');assert r['passed'] and len(r['scenes'])==13
assert r['counts']['objects']==4591 and r['counts']['classified']==4591 and r['counts']['exact_cull_operands']==4019
assert r['counts']['emissions']==2238 and r['counts']['exact_rom_selection']==2206 and r['counts']['special']==143
assert r['end_field_changes']=={'20':4318,'31':1}
with (root/'device-joins.csv').open(encoding='utf-8',newline='') as f:joins=list(csv.DictReader(f))
assert len(joins)==201
assert all(int(j['frame'])==5080 and 0<=float(j['device_time'])-float(j['cpu_time'])<.0176 for j in joins)
assert [int(j['model_id']) for j in joins]==sorted({int(j['model_id']) for j in joins})
assert all(float(a['cpu_time'])<float(b['cpu_time']) and float(a['device_time'])<=float(b['device_time']) for a,b in zip(joins,joins[1:]))
assert sum(float(j['device_time'])>float(j['ordinary_end']) for j in joins)==r['after_cpu_end']==1
receipts=read('receipts.json')['files'];get=lambda n:receipts[n]['receipt']
assert get('active-control5081-gl.json')['passed'] and get('active-control5081-gl.json')['frames']==17
assert get('active-probe5081-gl.json')['passed'] and get('active-probe5081-gl.json')['frames']==25
for name in ('active-control5081','active-probe5081'):
    assert get(name+'/report.json')['passed']
    motion=get(name+'-motion.json');assert motion['passed'] and motion['camera_samples']==[4191,4191] and motion['actual_adc_reads']==[12573,12573]
    assert get(name+'-5080-oracle.json')['original_context']['exact_context']
assert get('active-probe5081-resources.json')['passed']
texture=get('active-texture-footprints.json');assert texture['passed'] and texture['unique_bytes']==463610 and texture['changed_footprint_bytes']==0
material=get('active-material-assessment.json');assert material['materials_passed'] and material['later_uses']==58 and material['palette_uses']==499 and material['unobserved_candidates']==9
assert not material['original_geometry_passed'] and material['exact_geometry_instances']==198 and len(material['failures'])==3
print('PASS13 scene/count receipts,201 uniquely ordered actual emissions, one late device model,58 later material uses/499 palette uses, and17+25 paired4K receipts. Broad current geometry FAIL retained. Raw cull/material/route/resource/pixel bytes remain local.')
