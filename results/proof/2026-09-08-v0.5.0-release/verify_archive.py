"""Recompute telemetry/force verdicts; verify v0.5.0 release and menu receipts."""
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import zipfile

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as archive:
    assert set(archive.namelist())==set(manifest['files'])
    data={name:archive.read(name) for name in archive.namelist()}
for name,digest in manifest['files'].items():assert sha(data[name])==digest,name
read=lambda name:json.loads(data[name])
package=read('package/manifest.json');gate=read('readiness.json')
assert package['source_clean'] and package['source_identity']==manifest['source_identity']
assert gate['ready_for_release'] and gate['automated_pass']
assert gate['source_identity']==package['source_identity'] and gate['candidate_sha256']==package['candidate_sha256']
assert len(gate['attended']['waived'])==41 and gate['attended']['all_checks_passed'] is False
ledger=read('attended.json')
assert sorted(ledger['maintainer_approval']['waived_checks'])==sorted(gate['attended']['waived'])
assert any(e['sha256']==sha(data['approval.md']) for e in ledger['maintainer_approval']['evidence'])
checks=read('checks/report.json')
assert checks['passed'] and checks['source_identity']==checks['source_identity_after']==manifest['source_identity']
assert len(checks['steps'])==39 and all(s['returncode']==0 for s in checks['steps'])
for name,digest in checks['artifacts'].items():assert sha(data['checks/'+name])==digest
assert read('checks/unit-tests.json')==dict(passed=True,tests=196,errors=0,failures=0,skipped=0)
assert read('checks/gpu-quality.json')['passed'] and len(read('checks/gpu-quality.json')['checks'])==24
reg=read('regressions/report.json');plan=read('regressions/suite.json')
assert reg['passed'] and len(reg['cases'])==7 and reg['subset'] is None
assert reg['source_identity']==manifest['source_identity'] and reg['candidate_sha256']==package['candidate_sha256']

with tempfile.TemporaryDirectory(prefix='cruisn-release-proof-') as temporary:
    extracted=Path(temporary)
    for name,payload in data.items():
        if name.startswith('tools/') or name.startswith('regressions/'):
            destination=extracted/name
            assert destination.resolve().is_relative_to(extracted.resolve())
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(payload)
    sys.path.insert(0,str(extracted/'tools'))
    def module(name):
        spec=importlib.util.spec_from_file_location('archived_'+name,extracted/'tools'/(name+'.py'))
        result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
    drivetrain=module('analyze_drivetrain');force=module('analyze_force_gate')
    force_count=0
    for case,expected in zip(plan['cases'],reg['cases']):
        assert case['id']==expected['id'] and expected['passed']
        path=extracted/'regressions'/case['id'];config=case['telemetry'];memory=path/config['memory']
        observed=drivetrain.analyze(path,memory)
        observed['coverage_passed']=observed['game_state_samples']>=config.get('minimum_active_frames',500) and observed['wire']['maximum_speed_mph']>=config.get('minimum_speed_mph',10)
        assert json.loads(json.dumps(observed))==expected['telemetry'],case['id']
        if config.get('force_gate_game'):
            actual=force.analyze(path,memory,config['force_gate_game'],config.get('force_gate_policy','driving'),config.get('force_polarity',False))
            assert json.loads(json.dumps(actual))==expected['force_gate'],case['id'];force_count+=1
    assert force_count==4

for rom in ('crusnusa','crusnwld24','crusnwld','offroadc','crusnexo'):
    menu=read('menus/'+rom+'/report.json');replay=read('menus/'+rom+'/replay.json')
    assert menu['passed'] and menu['replay_passed'] and len(menu['menu'])==9
    assert replay['passed'] and replay['comparison']['passed'] and replay['gl_comparison']['passed']
    actions=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(io.StringIO(data['menus/'+rom+'/actions.csv'].decode()))]
    assert actions==menu['actions'] and len(actions)==1 and actions[0]['steps']==1
    assert actions[0]['frame']>menu['menu'][5]['frame']
assert read('menus/rejected-small-window.json')['passed'] is False
fresh=read('fresh-boots/report.json')
assert fresh['passed'] and len(fresh['cases'])==5 and fresh['source_identity']==manifest['source_identity']
assert all(r['passed'] and len(r['persisted'])==2 and all(p['passed'] for p in r['persisted']) for r in fresh['cases'])
frozen=read('frozen/report.json')
assert frozen['passed'] and len(frozen['games'])==6 and all(r['passed'] for r in frozen['games'])
assert frozen['games'][-1]['live_menu']['actions']
assert frozen['package']['package_sha256']==package['package_sha256']
upgrade=read('upgrade/report.json')
assert upgrade['passed'] and len(upgrade['stages'])==3
assert all(s['passed'] and len(s['preserved_fixtures'])==7 for s in upgrade['stages'])
deployment=read('personal-deployment.json')
assert deployment['passed'] and deployment['candidate_sha256']==package['candidate_sha256']
assert deployment['personal_hashes_before']==deployment['personal_hashes_after'] and deployment['preserved_files']==26
download=read('download-verification.json')
assert download['passed'] and download['sha256']==package['package_sha256']==manifest['package_sha256']
assert download['tag_commit']==package['commit']
companion=root.parent/'2026-09-08-live-cheats'
assert sha((companion/'evidence.zip').read_bytes())==manifest['cheat_memory_companion_sha256']
print('Checking the historical cheat-memory companion; its pending-deployment text predates v0.5.0.')
runpy.run_path(str(companion/'verify_archive.py'),run_name='archived_cheat_checks')
print('PASS: seven telemetry and four force verdicts recomputed; five live-menu/replay, fresh/frozen/upgrade/deployment/download receipts verified. 41 human waivers remain explicit.')
