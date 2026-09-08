"""Verify immutable release receipts without running a game or treating waivers as tests."""
import hashlib
import json
from pathlib import Path
import zipfile

base = Path(__file__).resolve().parent
manifest = json.loads((base / 'manifest.json').read_text())
path = base / 'release-evidence.zip'
assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['archive_sha256']
with zipfile.ZipFile(path) as archive:
    assert len(archive.namelist()) == len(manifest['files'])
    assert set(archive.namelist()) == set(manifest['files'])
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == digest, name
    read = lambda name: json.loads(archive.read(name))
    package = read('package/manifest.json')
    downloaded = read('download-verification.json')
    assert downloaded['passed'] and downloaded['sha256'] == package['package_sha256'] == manifest['package_sha256']
    assert downloaded['tag_commit'] == package['commit']
    readiness = read('readiness.json')
    assert readiness['ready_for_release'] and readiness['automated_pass']
    assert readiness['candidate_sha256'] == package['candidate_sha256']
    assert readiness['source_identity'] == package['source_identity']
    assert len(readiness['attended']['waived']) == 41
    assert readiness['attended']['all_checks_passed'] is False
    assert read('regressions/report.json')['passed']
    assert read('fresh-boots/report.json')['passed']
    assert read('frozen/report.json')['passed'] and read('upgrade/report.json')['passed']
print('PASS: archive bytes, release identity and recorded receipts; human waivers remain explicit.')
