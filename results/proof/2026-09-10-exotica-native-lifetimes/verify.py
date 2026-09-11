from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'harness'))
from release_identity import source_identity
here=Path(__file__).parent
read=lambda name:json.loads((here/name).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read('manifest.json')
assert set(manifest)=={p.name for p in here.iterdir() if p.is_file() and p.name!='manifest.json'}
for name,digest in manifest.items():assert sha(here/name)==digest,name
identity=source_identity(root);assert identity==read('source-identity.json')
local=read('local-checks.json');units=read('unit-tests.json')
assert local['passed'] and local['source_identity']==local['source_identity_after']==identity['sha256']
assert local['groups']==['python','native','gpu'] and all(r['returncode']==0 for r in local['steps'])
assert units['passed'] and units['tests']>=358 and units['skipped']==units['errors']==units['failures']==0
native=read('native-export.json');assert native['passed'] and native['patch_sha256']==sha(root/'patch/vunit-poc-patches.patch')
assert native['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
runs=read('runs.json');assert len(runs)==3
for name,run in runs.items():
    assert run['input_frames']==8860 and run['comparison']['passed'] and run['original_pixels_equal']
    assert run['native_sha256']==native['candidate_sha256'] and run['physical_ffb']==0 and run['crt']==1
    assert run['motion']['passed']
    assert [r['frame'] for r in run['captures']]==list(range(4650,4751,5))
    assert all(r['size']==[3840,2160] for r in run['captures'])
    if name=='native-lifetime-disabled':
        assert run['observer']=={'mode':'off'}
    else:
        events=run['events'];assert events['passed'] and events['matched_events']==86375
        assert events['all_event_fields_including_actual_times_exact'] and events['initial_head_and_count_match']
        counts=events['counts']
        for key,value in dict(records=86376,transitions=48481,bindings=4018,emissions=1010130,owned=948739,
            draws=33876,first_draws=3573,fading=30308,opaque=1126,epochs=2,unknown_frees=26).items():
            assert counts[key]==value,(name,key)
        assert run['observer']['result']==counts
a=runs['native-lifetime-amazon'];b=runs['native-lifetime-amazon-repeat']
assert a['events']['native_csv_sha256']==b['events']['native_csv_sha256']
assert [r['sha256'] for r in a['captures']]==[r['sha256'] for r in b['captures']]
defaults=read('defaults.json')
assert defaults['candidate_sha256']==native['candidate_sha256'] and defaults['source_identity']==identity['sha256']
assert defaults['subset'] is None and len(defaults['cases'])==7 and not defaults['physical_force']
assert defaults['passed']==all(r['passed'] for r in defaults['cases'])
print('PASS source/file hashes, three full-drive receipts, exact native event/repeat hashes,63completed4K and explicit default-suite outcome; raw execution remains receipts')
