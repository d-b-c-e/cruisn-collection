from pathlib import Path
from types import SimpleNamespace
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_runtime as runtime
import exotica_bootstrap as bootstrap
import exotica_journals as journals

class RuntimeTests(unittest.TestCase):
    def test_explicit_configuration_and_quiet_bootstrap(self):
        args=SimpleNamespace(candidate='candidate.exe',exotica_runtime='continuous',exotica_bootstrap='scenes')
        settings=dict(journals.REQUIRED,MIDZ_BOOTSTRAP='3',MIDZ_SHUTDOWN_OBSERVE='1',MIDZ_HOST_JOURNALS='quiet',MIDZ_DEPTH_FIRST='2',
                      MIDZ_HOST_FIRST='1800',MIDZ_MODEL_ENDPOINT_FIRST='1800',MIDZ_MODEL_ADMIT_FIRST='1800',**{k:'5200' for k in runtime.ENDS})
        trial=runtime.configure(args,'crusnexo',settings.copy())
        self.assertIsNone(trial['end']);self.assertFalse(trial['capture_completed'])
        for key in settings:
            with self.subTest(key=key):
                if key in ('MIDZ_HOST_FIRST','MIDZ_MODEL_ENDPOINT_FIRST','MIDZ_MODEL_ADMIT_FIRST'):continue
                with self.assertRaises(ValueError):runtime.configure(args,'crusnexo',dict(settings,**{key:'bad'}))
        for changes in (dict(candidate=None),dict(headless=True),dict(native_renderer=True),dict(exotica_runtime='bad')):
            with self.assertRaises(ValueError):runtime.configure(SimpleNamespace(**(vars(args)|changes)),'crusnexo',settings.copy())
        with self.assertRaises(ValueError):runtime.configure(args,'crusnusa',settings.copy())
        with self.assertRaises(ValueError):runtime.configure(SimpleNamespace(),'crusnexo',{runtime.KEY:'continuous'})
        bt=bootstrap.configure(args,'crusnexo',settings.copy(),5300)
        self.assertTrue(bt['continuous'])
        proof=dict(passed=True,changes_startup=True,frame=2000,base=112061)
        self.assertEqual(bootstrap.lifetime_trial(bt,proof,dict(mode='observe',first=1799))['first'],2000)

    @staticmethod
    def lines():return [runtime.KEY+' '+side+'=continuous end=none completion=quiescence' for side in ('cpu','gpu')]+[
        'MIDZ_RUNTIME_CPU_RESULT prepared_frame=5298','MIDZ_RUNTIME_GPU_RESULT mirror_frame=5299']
    @staticmethod
    def shutdown():return dict(classification='quiescent',receipts={'CPU':{'frame':5299},'GPU':{'frame':5299}})
    @staticmethod
    def trial():return dict(mode='continuous',capture_reference_ends={k:5240 for k in runtime.ENDS})
    @staticmethod
    def write(root,lines):
        (root/'stdout.log').write_text('\n'.join(lines[::2]),encoding='utf-8')
        (root/'stderr.log').write_text('\n'.join(lines[1::2]),encoding='utf-8')

    def test_policy_agreement_progress_and_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.write(root,self.lines())
            result=runtime.verify(self.trial(),root,self.shutdown())
            self.assertTrue(result['beyond_capture_limits']);self.assertFalse(result['capture_completed'])
            for state in ('interrupted','failed'):
                with self.assertRaises(ValueError):runtime.verify(self.trial(),root,self.shutdown()|dict(classification=state))
            with self.assertRaises(ValueError):runtime.verify(None,root,self.shutdown())
            for line in self.lines():
                for lines in (self.lines()+[line],[x for x in self.lines() if x!=line]):
                    self.write(root,lines)
                    with self.assertRaises(ValueError):runtime.verify(self.trial(),root,self.shutdown())
            for old,new in (('gpu=continuous','gpu=capture'),('mirror_frame=5299','mirror_frame=5298'),
                            ('prepared_frame=5298','prepared_frame=4294967296'),('prepared_frame=5298','prepared_frame=0')):
                self.write(root,[x.replace(old,new) for x in self.lines()])
                with self.assertRaises(ValueError):runtime.verify(self.trial(),root,self.shutdown())

    def test_runtime_cannot_be_accepted_as_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            lines=(Path(__file__).parent/'fixtures/exotica-quiet-receipts.txt').read_text(encoding='utf-8').splitlines()+self.lines()
            self.write(root,lines);(root/'exotica-endpoint-inputs.txt').write_text('retained fixture',encoding='utf-8')
            trial=dict(mode='quiet',snapshots=3,depth_snapshots=3)
            with self.assertRaises(ValueError):journals.verify(trial,root)
            trial['continuous']=True
            with self.assertRaises(ValueError):journals.verify(trial,root)
            result=runtime.verify(self.trial(),root,self.shutdown())
            self.assertFalse(journals.verify(trial,root,runtime_result=result)['capture_completed'])
            self.write(root,[x.replace('complete=1','complete=0',1) for x in lines])
            with self.assertRaises(ValueError):journals.verify(trial,root,runtime_result=result)

if __name__=='__main__':unittest.main()
