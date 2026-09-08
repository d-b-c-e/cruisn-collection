import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from release_gate import regression_check,acceptance_check,fresh_boot_check
from check_release_package import FREEPLAY
from verification import sha256_file


class ReleaseGateTests(unittest.TestCase):
    def test_maintainer_waiver_preserves_unperformed_status_and_build_binding(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'approval.md';path.write_text('Maintainer: release the current state; second wheel untested.')
            approval={'decision':'release-current-state','reviewer':'maintainer','date':'2026-09-08',
                'notes':'Explicit release approval; second wheel remains untested.',
                'waived_checks':['wheel'],'evidence':[{'path':path.name,'sha256':sha256_file(path)}]}
            ledger={'candidate_sha256':'binary','source_identity':'source','maintainer_approval':approval,
                    'checks':{'wheel':{'status':'waived','notes':'Second vendor not tested; accepted for this release.'}}}
            def check(value=ledger): return acceptance_check(value,{'wheel':'required'},'binary','source',td)
            result=check()
            self.assertTrue(result['passed']);self.assertFalse(result['all_checks_passed'])
            self.assertEqual(result['waived'],['wheel'])
            for field,value in [('candidate_sha256','old'),('source_identity','old')]:
                bad=copy.deepcopy(ledger);bad[field]=value;self.assertFalse(check(bad)['passed'])
            for field,value in [('decision',''),('waived_checks',[]),('waived_checks',['wheel','extra']),
                                ('waived_checks',['wheel','wheel']),('reviewer',''),('evidence',[])]:
                bad=copy.deepcopy(ledger);bad['maintainer_approval'][field]=value
                self.assertFalse(check(bad)['passed'])
            bad=copy.deepcopy(ledger);bad['checks']['wheel']['notes']=''
            self.assertFalse(check(bad)['passed'])
            path.write_text('Changed approval');self.assertFalse(check()['passed'])

    def test_blanket_approval_does_not_clear_pending_or_failed_checks(self):
        for status in ('pending','fail'):
            ledger={'candidate_sha256':'binary','source_identity':'source',
                'maintainer_approval':{'decision':'release-current-state','waived_checks':['drive']},
                'checks':{'drive':{'status':status}}}
            result=acceptance_check(ledger,{'drive':'required'},'binary','source','.')
            self.assertFalse(result['passed']);self.assertEqual(result['pending'],['drive'])

    def test_replay_success_cannot_hide_failed_setting_persistence(self):
        report={'passed':True,'physical_force':False,'candidate_sha256':'binary','source_identity':'source',
                'cases':[{'rom':rom,'passed':True,'replay_exit':0,
                          'persisted':[{'passed':True},{'passed':True}]} for rom in FREEPLAY]}
        self.assertTrue(fresh_boot_check(report,'binary','source'))
        bad=copy.deepcopy(report);bad['cases'][3]['persisted'][0]['passed']=False
        self.assertFalse(fresh_boot_check(bad,'binary','source'))
        bad=copy.deepcopy(report);bad['cases'].pop()
        self.assertFalse(fresh_boot_check(bad,'binary','source'))
        self.assertFalse(fresh_boot_check(report,'binary','old'))

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
