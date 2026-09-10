"""Check public scalar receipt consistency; raw execution remains local."""
from pathlib import Path
import hashlib,json
root=Path(__file__).parent
load=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
manifest=load('manifest.json')
for name,expected in manifest['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
checks=load('receipts/checks-report.json');identity=load('receipts/checks-source-identity.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==identity['sha256']
assert len(checks['steps'])==136 and all(s['returncode']==0 for s in checks['steps'])
units=load('receipts/checks-unit-tests.json');assert units['passed'] and units['tests']==351 and units['skipped']==0
perf=load('receipts/performance.json');assert len(perf)==6
for r in perf:
    assert r['camera_samples']==[7060,7060] and r['actual_adc_reads']==[21180,21180] and r['adc_times_equal']
    for g in r['geometry_identity'].values():assert g['passed'] and g['rows']==6953
for route in ('hk','amazon'):
    for mode in ('control','probe'):
        r=load('receipts/'+route+'-'+mode+'.json');assert r['passed'] and r['motion']['passed']
        if mode=='probe':assert r['fade']['passed'] and r['gl']['passed'] and r['paired_motion']['passed']
    fade=load('receipts/'+route+'-final-native.json')
    assert fade['passed'] and fade['native_verified'] and fade['events']==fade['counts'].get('continuing',0)+fade['counts'].get('completed',0)
print('PASS archive hashes and receipt consistency; raw replay/fade/pixels/builds are not recomputed')
