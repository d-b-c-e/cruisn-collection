"""Recheck archived byte hashes, then recompute telemetry and force verdicts without ROMs."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile

root = Path(__file__).resolve().parent
index = json.loads((root/'archive.json').read_text(encoding='utf-8'))
archive = root/'derived-evidence.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == index['zip_sha256']
with tempfile.TemporaryDirectory(prefix='cruisn-feedback-proof-') as td:
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == set(index['files'])
        for name,digest in index['files'].items():
            assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and ':' not in name
            assert hashlib.sha256(z.read(name)).hexdigest() == digest, name
        z.extractall(td)
    work = Path(td)
    sys.path.insert(0, str(work/'analyzers'))
    from analyze_drivetrain import analyze
    from analyze_force_gate import analyze as analyze_gate
    suite = json.loads((work/'analyzers/suite.json').read_text(encoding='utf-8'))
    accepted = {r['id']:r for r in json.loads((work/'regressions/report.json').read_text(encoding='utf-8'))['cases']}
    for case in suite['cases']:
        run = work/'regressions'/case['id']/'run'
        memory = run/case['telemetry']['memory']
        expected = dict(accepted[case['id']]['telemetry'])
        assert expected.pop('coverage_passed') is True
        assert analyze(run,memory) == expected, case['id']
        game = case['telemetry'].get('force_gate_game')
        if game: assert analyze_gate(run,memory,game) == accepted[case['id']]['force_gate']
        print(case['id'], 'PASS')
print(f"PASS: {len(index['files'])} exact archived files; seven telemetry and four force-gate verdicts recomputed")
