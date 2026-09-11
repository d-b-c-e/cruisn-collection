import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import ffb_worker as w


class ForceWorkerTests(unittest.TestCase):
    def args(self, **kw):
        return SimpleNamespace(**dict(dict(ffb_worker='observe',candidate=Path('vunit.exe'),
            ffb_worker_strength=50,ffb_worker_impacts='off'),**kw))

    def candidate(self, root):
        shutil.copy2(w.ROOT/'lib/toolkit/profiles/force-profiles.ini',root/'force-profiles.ini')
        return root/'vunit.exe'

    def test_explicit_candidate_and_observer(self):
        with self.assertRaises(ValueError):w.configure(self.args(candidate=None),'crusnusa',{})
        with self.assertRaises(ValueError):w.configure(self.args(),'unknown',{})
        with self.assertRaises(ValueError):w.configure(self.args(ffb_worker=None),'crusnusa',{'MIDV_FFB_OBSERVE_WORKER':'1'})
        with self.assertRaises(ValueError):w.configure(self.args(ffb_worker='off'),'crusnusa',{})

    def test_nominal_strength_trim_and_polarity_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=self.candidate(Path(tmp))
            for game in ('crusnusa','crusnwld24','offroadc','crusnexo'):
                for nominal in (0,25,50,80,100):
                    settings={'MIDV_FFB':'1','MIDV_FFB_GAME_GATE':'0','MIDV_FFB_INVERT':'1','MIDV_FFB_SMOOTH':'80'}
                    t=w.configure(self.args(candidate=candidate,ffb_worker_strength=nominal),game,settings)
                    expected=(nominal*80+50)//100 if game=='crusnexo' else nominal
                    self.assertEqual(t['effective_strength'],expected)
                    self.assertEqual(settings['MIDV_FFB'],'0')
                    self.assertEqual(settings['MIDV_FFB_GAME_GATE'],'0')
                    self.assertTrue(t['expected']['invert'])
                    self.assertNotIn('MIDV_FFB_SMOOTH',settings)

    def test_user_override_or_changed_profile_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);candidate=self.candidate(root)
            (root/'force-profiles.user.ini').write_text('')
            with self.assertRaises(ValueError):w.configure(self.args(candidate=candidate),'crusnusa',{})
            (root/'force-profiles.user.ini').unlink()
            (root/'force-profiles.ini').write_text('bad')
            with self.assertRaises(ValueError):w.configure(self.args(candidate=candidate),'crusnusa',{})

    def test_setting_ranges(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=self.candidate(Path(tmp))
            for value in (-1,101):
                with self.assertRaises(ValueError):w.configure(self.args(candidate=candidate,ffb_worker_strength=value),'crusnusa',{})
            for k in ('HOLD_MS','DAMPER','FRICTION','SPRING','RUMBLE','INVERT'):
                with self.assertRaises(ValueError):w.configure(self.args(candidate=candidate),'crusnusa',{'MIDV_FFB_'+k:'-1'})

    def test_disabled_does_not_accept_observer_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ('stdout.log','stderr.log'):(root/name).write_text('')
            self.assertIsNone(w.verify_receipt(None,root))
            (root/w.FILES[0]).write_text('{}')
            with self.assertRaises(ValueError):w.verify_receipt(None,root)

    def test_source_clocks_shape_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.csv'
            def write(rows):
                with path.open('w',newline='') as f:
                    writer=csv.writer(f);writer.writerow(w.SOURCE_FIELDS);writer.writerows(rows)
            row=[1,.001,0,1,-128,0,1,0,0]
            write([row]);self.assertEqual(w.bounded_sources(path)[0]['raw'],-128)
            for index,value in ((0,2),(1,'nan'),(2,-1),(4,128),(6,2)):
                bad=row.copy();bad[index]=value;write([bad])
                with self.assertRaises(ValueError):w.bounded_sources(path)
            write([row,[2,0,0,1,0,0,1,0,0]])
            with self.assertRaises(ValueError):w.bounded_sources(path)
            write([row+[0]])
            with self.assertRaises(ValueError):w.bounded_sources(path)


if __name__=='__main__':unittest.main()
