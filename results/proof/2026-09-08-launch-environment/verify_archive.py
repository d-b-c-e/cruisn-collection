"""Verify launch-fix evidence bytes and verdicts; no emulator execution."""
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
    data = {n: z.read(n) for n in z.namelist()}
for name, digest in manifest['files'].items():
    assert hashlib.sha256(data[name]).hexdigest() == digest, name
report = json.loads(data['checks/report.json'])
assert report['passed'] and report['source_identity'] == report['source_identity_after'] == manifest['source_identity']
assert len(report['steps']) == 37 and all(s['returncode'] == 0 for s in report['steps'])
for name, digest in report['artifacts'].items():
    assert hashlib.sha256(data['checks/'+name]).hexdigest() == digest, name
assert json.loads(data['checks/unit-tests.json']) == dict(passed=True, tests=187, errors=0, failures=0, skipped=0)
gpu = json.loads(data['checks/gpu-quality.json'])
assert gpu['passed'] and len(gpu['checks']) == 24 and all(c['passed'] for c in gpu['checks'])
math = json.loads(data['checks/world-host-math.json'])
assert math['passed'] and math['math_passed'] and math['math_vectors'] == 10081
assert b"UnboundLocalError: cannot access local variable 'env'" in data['before-fix.log']
assert b'FAILED (errors=10)' in data['before-fix.log']
print('PASS: archived failure, 187 passing tests, 37 commands and 24 GPU receipts')
