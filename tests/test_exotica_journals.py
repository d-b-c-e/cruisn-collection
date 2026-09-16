from pathlib import Path
from types import SimpleNamespace
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_journals as journals


class JournalTests(unittest.TestCase):
    def test_selection_requires_combined_candidate(self):
        args=SimpleNamespace(exotica_journals='quiet',candidate='candidate.exe')
        settings=journals.REQUIRED|dict(MIDZ_HOST_SNAPSHOTS='5072,5080,5219',MIDZ_DEPTH_SNAPSHOTS='5073,5081,5220')
        trial=journals.configure(args,'crusnexo',settings.copy())
        self.assertFalse(trial['continuous']);self.assertFalse(trial['independent_event_journals'])
        for key in journals.REQUIRED:
            for value in (None,'bad'):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                    journals.configure(args,'crusnexo',settings|{key:value})
        for update in (dict(candidate=None),dict(headless=True),dict(native_renderer=True),dict(exotica_journals='invalid')):
            with self.assertRaises(ValueError):journals.configure(SimpleNamespace(**(vars(args)|update)),'crusnexo',settings.copy())
        with self.assertRaises(ValueError):journals.configure(args,'crusnusa',settings.copy())
        with self.assertRaises(ValueError):journals.configure(SimpleNamespace(),'crusnexo',{journals.KEY:'quiet'})
        self.assertIsNone(journals.configure(SimpleNamespace(),'crusnexo',{}))

    def test_real_summary_and_independent_proof_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.write(root,self.fixture())
            result=journals.verify(self.trial(),root)
            self.assertFalse(result['independent_event_journals']);self.assertFalse(result['continuous'])
            self.assertEqual(result['receipts']['MIDZ_HOST_SCENE_RESULT']['prepared'],3429)
            (root/journals.JOURNALS[0]).write_text('unexpected',encoding='utf-8')
            with self.assertRaises(ValueError):journals.verify(self.trial(),root)

    def test_missing_duplicate_and_inconsistent_receipts(self):
        lines=self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for i,line in enumerate(lines):
                for variant in (lines[:i]+lines[i+1:],lines+[line]):
                    self.write(root,variant)
                    with self.subTest(line=line),self.assertRaises(ValueError):journals.verify(self.trial(),root)
            changes=(('complete=1','complete=0'),('gpu=quiet','gpu=capture'),
                ('received=10287','received=10286'),('commits=9695','commits=9696'),
                ('quads=4541234','quads=4541235'),('written=12','written=11'),
                ('remaining=0','remaining=1'),('rejected=0','rejected=1'))
            for old,new in changes:
                source='\n'.join(lines);self.assertIn(old,source)
                self.write(root,source.replace(old,new,1).splitlines())
                with self.subTest(change=old),self.assertRaises(ValueError):journals.verify(self.trial(),root)

    def test_explicit_capture_and_unrequested_quiet(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.write(root,[]);self.assertIsNone(journals.verify(None,root))
            self.write(root,['MIDZ_HOST_JOURNALS cpu=capture','MIDZ_HOST_JOURNALS gpu=capture'])
            self.assertTrue(journals.verify(dict(mode='capture'),root)['independent_event_journals'])
            with self.assertRaises(ValueError):journals.verify(None,root)

    def test_snapshot_failure_evidence_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.write(root,self.fixture())
            operands=root/'exotica-endpoint-inputs.txt'
            operands.unlink()
            with self.assertRaises(ValueError):journals.verify(self.trial(),root)
            operands.write_text('',encoding='utf-8')
            with self.assertRaises(ValueError):journals.verify(self.trial(),root)

    def test_no_routine_operands_requires_continuous_zero_snapshot_and_no_saved_models(self):
        lines=[line.replace('snapshots=11 bytes=50960','snapshots=0 bytes=0') for line in self.fixture()]
        trial=self.trial()|dict(continuous=True,endpoint_snapshot='0')
        runtime=dict(passed=True,capture_completed=False)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.write(root,lines)
            operands=root/'exotica-endpoint-inputs.txt';operands.unlink()
            self.assertTrue(journals.verify(trial,root,runtime_result=runtime)['continuous'])
            with self.assertRaises(ValueError):journals.verify(trial,root)
            with self.assertRaises(ValueError):journals.verify(trial|dict(endpoint_snapshot='5219'),root,runtime_result=runtime)
            operands.write_text('unexpected',encoding='utf-8')
            with self.assertRaises(ValueError):journals.verify(trial,root,runtime_result=runtime)
            operands.unlink();self.write(root,self.fixture());operands.unlink()
            with self.assertRaises(ValueError):journals.verify(trial,root,runtime_result=runtime)

    @staticmethod
    def trial():return dict(mode='quiet',snapshots=3,depth_snapshots=3)
    @staticmethod
    def fixture():
        return (Path(__file__).parent/'fixtures/exotica-quiet-receipts.txt').read_text(encoding='utf-8').splitlines()
    @staticmethod
    def write(root,lines):
        # Either producer may emit to either stream; validate both once.
        (root/'stdout.log').write_text('\n'.join(lines[::2])+'\n',encoding='utf-8')
        (root/'stderr.log').write_text('\n'.join(lines[1::2])+'\n',encoding='utf-8')
        # This verifier checks retention, not the independent operand codec.
        (root/'exotica-endpoint-inputs.txt').write_text('retained fixture operands\n',encoding='utf-8')


if __name__=='__main__':unittest.main()
