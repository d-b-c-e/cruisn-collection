from pathlib import Path
from types import SimpleNamespace
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from vunit_runtime import configure,verify


class RuntimeTests(unittest.TestCase):
    def test_explicit_continuous_scope(self):
        args=SimpleNamespace(candidate='x',vunit_runtime='continuous')
        settings={'MIDV_HOST_BOOTSTRAP':'1','MIDV_GL':'1','MIDV_FFB':'0'}
        bootstrap={'last':200,'first':100}
        trial=configure(args,'crusnusa',settings,302,bootstrap)
        self.assertEqual(trial['reference_last'],200)
        self.assertEqual(bootstrap['runtime_last'],301)
        self.assertEqual(bootstrap['last'],200)
        for change in ({'candidate':None},{'headless':True},{'vunit_runtime':None}):
            with self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args)|change)),'crusnusa',settings.copy(),302,bootstrap.copy())
        for rom in ('crusnexo','unknown'):
            with self.assertRaises(ValueError):configure(args,rom,settings.copy(),302,bootstrap.copy())
        with self.assertRaises(ValueError):configure(args,'crusnusa',settings.copy(),302,None)
        self.assertIsNone(configure(SimpleNamespace(),'crusnusa',{},302,None))

    def test_owned_stop_is_not_a_finite_capture(self):
        trial=dict(rom='crusnusa',reference_last=200,verification_last=301)
        bootstrap=dict(verified=True,first=100,last_prepared=300,scenes=2)
        cpu='VUNIT_RUNTIME_CPU frame=300 scenes=2 quads=7 failed=0\n'
        gpu='VUNIT_RUNTIME_GPU joined=1 ready=1 written=128 read=128 dropped=0 failed=0 pending_quads=0 gl_errors=0 completed=301 presented=301\n'
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'stdout.log').write_text('VUNIT_RUNTIME cpu=continuous end=none\n'+cpu)
            (root/'stderr.log').write_text('VUNIT_RUNTIME gpu=owned\n'+gpu)
            (root/'usa-host-scenes.csv').write_text('frame,quads\n100,3\n300,4\n')
            result=verify(trial,root,bootstrap)
            self.assertTrue(result['verified'] and result['beyond_reference_end'])
            self.assertFalse(result['capture_completed'])
            with self.assertRaises(ValueError):verify(None,root,None)
            for old,new in [('joined=1','joined=0'),('ready=1','ready=0'),('read=128','read=120'),
                            ('dropped=0','dropped=1'),('failed=0','failed=1'),
                            ('pending_quads=0','pending_quads=2'),('gl_errors=0','gl_errors=1280'),
                            ('presented=301','presented=302')]:
                (root/'stderr.log').write_text('VUNIT_RUNTIME gpu=owned\n'+gpu.replace(old,new))
                with self.subTest(old=old),self.assertRaises(ValueError):verify(trial,root,bootstrap)
            (root/'stderr.log').write_text('VUNIT_RUNTIME gpu=owned\n'+gpu+gpu)
            with self.assertRaises(ValueError):verify(trial,root,bootstrap)
            (root/'stderr.log').write_text('VUNIT_RUNTIME gpu=owned\n'+gpu)
            (root/'usa-host-scenes.csv').write_text('frame,quads\n100,3\n300,5\n')
            with self.assertRaises(ValueError):verify(trial,root,bootstrap)


if __name__=='__main__':unittest.main()
