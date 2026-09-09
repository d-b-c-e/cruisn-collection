"""Verify archived local check evidence; does not rerun compilers or the GPU."""
import hashlib
import json
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_text())
archive = root/'evidence.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256']
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist()) == set(manifest['files'])
    data = {name: z.read(name) for name in z.namelist()}
for name, digest in manifest['files'].items():
    assert hashlib.sha256(data[name]).hexdigest() == digest, name
def read(name):
    return json.loads(data[name])
report = read('checks/report.json')
assert report['passed'] and report['groups'] == ['python', 'native', 'gpu']
assert report['source_identity'] == report['source_identity_after'] == manifest['source_identity']
assert len(report['steps']) == 37 and all(s['returncode'] == 0 for s in report['steps'])
for name, digest in report['artifacts'].items():
    assert hashlib.sha256(data['checks/'+name]).hexdigest() == digest, name
units = read('checks/unit-tests.json')
assert units == dict(passed=True, tests=185, errors=0, failures=0, skipped=0)
gpu = read('checks/gpu-quality.json')
assert gpu['passed'] and len(gpu['checks']) == 24 and all(c['passed'] for c in gpu['checks'])
math = read('checks/world-host-math.json')
assert math['passed'] and math['math_passed'] and math['math_vectors'] == 10081
gate = read('gate-incomplete.json')
assert gate['local_checks']['passed'] and not gate['ready_for_release']
assert not read('missing-compiler/report.json')['passed']
receipts = read('github-and-baseline.json')
assert all(w['state'] == 'disabled_manually' for w in receipts['collection_workflows']['workflows'])
assert not receipts['new_commit_runs'] and receipts['fork_workflows']['total_count'] == 0
assert all(r['sha256'] == r['expected'] for r in receipts['preserved'].values())
print('PASS: 47 hashed files; 37 steps, 185 tests, 24 GPU receipts; negative gates retained')
