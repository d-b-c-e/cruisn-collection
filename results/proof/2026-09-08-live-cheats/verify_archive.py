"""Recompute recorded timer/restoration verdicts; verify other evidence receipts.

No ROMs, cheat XML, emulator execution or physical output required.
"""
import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import zipfile

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha((root/'evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'evidence.zip') as archive:
    assert set(archive.namelist())==set(manifest['files'])
    files={name:archive.read(name) for name in archive.namelist()}
for name,digest in manifest['files'].items():assert sha(files[name])==digest,name
report=json.loads(files['checks/report.json'])
assert report['passed'] and report['source_identity']==report['source_identity_after']==manifest['source_identity']
assert len(report['steps'])==39 and all(step['returncode']==0 for step in report['steps'])
for name,digest in report['artifacts'].items():assert sha(files['checks/'+name])==digest,name
assert json.loads(files['checks/unit-tests.json'])==dict(passed=True,tests=196,errors=0,failures=0,skipped=0)
gpu=json.loads(files['checks/gpu-quality.json'])
assert gpu['passed'] and len(gpu['checks'])==24 and all(row['passed'] for row in gpu['checks'])
math=json.loads(files['checks/world-host-math.json'])
assert math['passed'] and math['math_passed'] and math['math_vectors']==10081

# Execute only the two archived pure CSV analyzers; no CLI, imports or launch path.
tree=ast.parse(files['analyzer.py'])
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('inspect','inspect_restoration')]
assert len(functions)==2
namespace={'csv':csv,'Path':Path,'sha256_file':lambda path:sha(Path(path).read_bytes())}
exec(compile(ast.Module(body=functions,type_ignores=[]),'archived CSV analyzers','exec'),namespace)
native=json.loads(files['native-patch.json'])
assert native['passed'] and native['patch_count']==134
with tempfile.TemporaryDirectory(prefix='cruisn-cheat-proof-') as temp:
    for rom in ('crusnusa','crusnwld24','crusnwld','offroadc','crusnexo'):
        original=json.loads(files[rom+'/report.json'])
        assert original['passed'] and original['physical_force'] is False
        assert original['candidate_sha256']==native['candidate_sha256']
        directory=Path(temp)/rom;directory.mkdir()
        for name in ('cheat-probe.csv','cheat-code-probe.csv'):(directory/name).write_bytes(files[rom+'/'+name])
        finish=rom!='offroadc'
        assert json.loads(json.dumps(namespace['inspect'](directory,rom,finish)))==original['timer']
        assert namespace['inspect_restoration'](directory,rom,finish)==original['restoration']
        observed=files[rom+'/actions.csv']
        assert observed==files[rom+'/replay-actions.csv']
        assert sha(observed)==original['actions_sha256']
        actions=[{key:int(value) for key,value in row.items()} for row in csv.DictReader(io.StringIO(observed.decode()))]
        assert actions==original['actions']
        expected_frames=[2600,3000]
        if rom!='crusnwld24':expected_frames.extend([2700,2800])
        if finish:expected_frames.append(3200)
        assert [row['frame'] for row in actions]==sorted(expected_frames)

package=json.loads(files['package/check.json'])
candidate=json.loads(files['package/manifest.json'])
defaults=json.loads(files['package/defaults.json'])
assert package['passed'] and defaults['passed'] and candidate['source_clean']
assert candidate['source_identity']==manifest['source_identity']
assert candidate['candidate_sha256']==package['candidate_sha256']==native['candidate_sha256']
assert candidate['package_sha256']==package['package_sha256']
assert candidate['file_hashes']==package['file_hashes']
deployment=json.loads(files['deployment.json'])
assert deployment['candidate_deployed'] is False and deployment['physical_force'] is False
print('PASS: five timer/restoration/action verdicts recomputed; 196 tests, 24 GPU checks and clean-package receipts verified. Visible menu/default driving acceptance remains pending.')
