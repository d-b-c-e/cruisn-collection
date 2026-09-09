"""Release checks must fail closed on partial, stale or damaged local evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from local_checks import commands, GROUPS, run_command, validate_report
from verification import sha256_file


class LocalCheckEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.report = dict(schema=1, passed=True, groups=list(GROUPS), platform='win32',
                           source_identity='source', source_identity_after='source', steps=[])
        for group in GROUPS:
            for name, _ in commands(group, self.directory, 'g++'):
                log = name+'.log'
                (self.directory/log).write_text('test evidence')
                self.report['steps'].append(dict(name=name, returncode=0, log=log))
        self.write('source-identity.json', dict(sha256='source'))
        self.write('unit-tests.json', dict(passed=True, tests=180, skipped=0, errors=0, failures=0))
        self.write('gpu-quality.json', dict(passed=True, checks=[dict(passed=True)]))
        self.write('world-host-math.json', dict(passed=True, math_passed=True, math_vectors=10081))
        for name in ('stages.csv', 'impacts.csv'):
            (self.directory/name).write_text('ms,force\n0,0\n')
        self.rehash()

    def write(self, name, value):
        (self.directory/name).write_text(json.dumps(value))

    def rehash(self):
        self.report['artifacts'] = {p.name: sha256_file(p) for p in self.directory.iterdir()}

    def test_stale_partial_and_non_windows_reports_cannot_clear_release(self):
        self.assertTrue(validate_report(self.report, 'source', self.directory))
        for change in ({'groups': ['python']}, {'platform': 'linux'}, {'passed': False},
                       {'source_identity': 'old'}, {'source_identity_after': 'changed'},
                       {'steps': self.report['steps'][:-1]}):
            with self.subTest(change=change):
                self.assertFalse(validate_report(dict(self.report, **change), 'source', self.directory))
        bad = copy.deepcopy(self.report)
        bad['steps'][0]['returncode'] = 1
        self.assertFalse(validate_report(bad, 'source', self.directory))

    def test_missing_or_changed_evidence_is_not_a_pass(self):
        bad = copy.deepcopy(self.report)
        del bad['artifacts']['gpu-quality.json']
        self.assertFalse(validate_report(bad, 'source', self.directory))
        (self.directory/'python-tests.log').write_text('different run')
        self.assertFalse(validate_report(self.report, 'source', self.directory))

    def test_skipped_tests_and_empty_or_failed_gpu_checks_block_release(self):
        self.write('unit-tests.json', dict(passed=True, tests=180, skipped=1, errors=0, failures=0))
        self.rehash()
        self.assertFalse(validate_report(self.report, 'source', self.directory))
        self.write('unit-tests.json', dict(passed=True, tests=180, skipped=0, errors=0, failures=0))
        for checks in ([], [dict(passed=False)]):
            self.write('gpu-quality.json', dict(passed=True, checks=checks))
            self.rehash()
            self.assertFalse(validate_report(self.report, 'source', self.directory))

    def test_evidence_cannot_escape_its_directory(self):
        self.report['artifacts']['../unrelated.log'] = 'hash'
        self.assertFalse(validate_report(self.report, 'source', self.directory))

    def test_failed_process_and_missing_tool_retain_failure_logs(self):
        import os
        for name, command in (('failure', [sys.executable, '-c', 'raise SystemExit(7)']),
                              ('missing', [str(self.directory/'absent-tool.exe')])):
            row = run_command(name, command, self.directory, dict(os.environ))
            self.assertNotEqual(row['returncode'], 0)
            self.assertTrue((self.directory/row['log']).is_file())
