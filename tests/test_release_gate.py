import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from release_gate import regression_check,acceptance_check
from verification import sha256_file


class ReleaseGateTests(unittest.TestCase):
    def test_partial_stale_and_force_enabled_suites_cannot_clear_release(self):
        report={'passed':True,'physical_force':False,'candidate_sha256':'binary','source_identity':'source',
                'suite_sha256':'suite','subset':None,'cases':[{'id':'a','passed':True},{'id':'b','passed':True}]}
        suite={'cases':[{'id':'a'},{'id':'b'}]}
        self.assertTrue(regression_check(report,'binary','source',suite,'suite'))
        for key,val in [('candidate_sha256','old'),('source_identity','old'),('suite_sha256','old'),
                        ('physical_force',True),('subset',['a','b']),('cases',[{'id':'a','passed':True}])]:
            bad=copy.deepcopy(report);bad[key]=val
            self.assertFalse(regression_check(bad,'binary','source',suite,'suite'))

    def test_attended_acceptance_requires_current_hashed_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'notes.md';path.write_text('Human observations')
            ledger={'candidate_sha256':'binary','source_identity':'source','checks':{'drive':{'status':'pass',
                'reviewer':'tester','date':'2026-09-07','notes':'Manual shift checked in gameplay',
                'evidence':[{'path':path.name,'sha256':sha256_file(path)}]}}}
            self.assertTrue(acceptance_check(ledger,{'drive':'required'},'binary','source',td)['passed'])
            self.assertFalse(acceptance_check(ledger,{'drive':'required'},'other','source',td)['passed'])
            self.assertFalse(acceptance_check(ledger,{'drive':'required','ffb':'required'},'binary','source',td)['passed'])
            path.write_text('Changed evidence')
            self.assertFalse(acceptance_check(ledger,{'drive':'required'},'binary','source',td)['passed'])
