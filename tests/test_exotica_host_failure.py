from pathlib import Path
from types import SimpleNamespace
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_host_failure import configure,verify_receipt


class ExoticaFailureTests(unittest.TestCase):
    def test_continuous_failure_extends_reference_but_bounds_injection_and_drain(self):
        args=SimpleNamespace(candidate='x',exotica_host_failure='original',exotica_host_inject_failure_frame=5300,
            exotica_runtime='continuous',exotica_bootstrap='scenes',exotica_journals='quiet')
        env=dict(MIDV_FFB='0',MIDZ_GL='1',MIDZ_HOST_FUTURE='2',MIDZ_HOST_COMPOSE='1',
            MIDZ_HOST_FUTURE_PRESENT='1',MIDZ_HOST_FIRST='1800',MIDZ_HOST_LAST='5240',MIDZ_MODEL_ENDPOINT_SNAPSHOT='0')
        trial=configure(args,'crusnexo',env.copy(),5400)
        self.assertEqual((trial['first'],trial['last'],trial['reference_last']),(1,5399,5240))
        for frame in (1,1799,5397):
            self.assertEqual(configure(SimpleNamespace(**(vars(args)|{'exotica_host_inject_failure_frame':frame})),
                                       'crusnexo',env.copy(),5400)['inject'],frame)
        for update in ({'exotica_bootstrap':None},{'exotica_journals':None},
                       {'exotica_host_inject_failure_frame':5398},{'exotica_host_inject_failure_frame':True},
                       {'exotica_host_inject_failure_frame':0}):
            with self.assertRaises(ValueError):configure(SimpleNamespace(**(vars(args)|update)),'crusnexo',env.copy(),5400)
        with self.assertRaises(ValueError):
            configure(SimpleNamespace(**(vars(args)|{'exotica_host_inject_failure_frame':16001})),'crusnexo',env.copy(),18000)

    def test_selection_and_late_snapshot_rejection(self):
        args=SimpleNamespace(candidate='x',exotica_host_failure='original',exotica_host_inject_failure_frame=5230)
        settings=dict(MIDV_FFB='0',MIDZ_GL='1',MIDZ_HOST_FUTURE='2',MIDZ_HOST_COMPOSE='1',
            MIDZ_HOST_FUTURE_PRESENT='1',MIDZ_HOST_FIRST='1800',MIDZ_HOST_LAST='5288',
            MIDZ_HOST_SNAPSHOTS='5072,5219',MIDZ_MODEL_ENDPOINT_SNAPSHOT='5219')
        self.assertEqual(configure(args,'crusnexo',settings.copy(),5300)['inject'],5230)
        for key,value in [('MIDV_FFB','1'),('MIDZ_HOST_COMPOSE','0'),('MIDZ_HOST_FUTURE_PRESENT','0'),
                          ('MIDZ_HOST_SNAPSHOTS','5280'),('MIDZ_MODEL_ENDPOINT_SNAPSHOT','5230')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                configure(args,'crusnexo',settings|{key:value},5300)
        for update in [dict(candidate=None),dict(headless=True),dict(native_renderer=True),
                       dict(exotica_host_inject_failure_frame=5290)]:
            with self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args)|update)),'crusnexo',settings.copy(),5300)
        with self.assertRaises(ValueError):configure(args,'crusnwld',settings.copy(),5300)
        with self.assertRaises(ValueError):configure(args,'crusnexo',settings.copy(),5289)
        with self.assertRaises(ValueError):configure(SimpleNamespace(),'crusnexo',{'MIDZ_HOST_FAILURE_POLICY':'0'},5300)
        self.assertIsNone(configure(SimpleNamespace(),'crusnexo',{},5300))

    def test_retirement_ownership_and_both_streams(self):
        trial=dict(policy='original',inject=5230,first=1800,last=5288)
        lines=['EXOTICA_HOST_FAILURE_POLICY original=1 inject=5230',
               'EXOTICA_HOST_PREP_FAILURE frame=5230 scene=4000 injected=1 fallback=1',
               'EXOTICA_HOST_RETIRE_QUEUED frame=5231 scene=4000',
               'EXOTICA_HOST_RETIRE_GPU frame=5231 scene=4000',
               'EXOTICA_HOST_RETIRE_PRESENT frame=5231 scene=4000']
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            def write(items):
                (root/'stdout.log').write_text('\n'.join(items[::2])+'\n',encoding='utf-8')
                (root/'stderr.log').write_text('\n'.join(items[1::2])+'\n',encoding='utf-8')
            write(lines);result=verify_receipt(trial,root)
            self.assertTrue(result['degraded']);self.assertEqual(result['presented_frame'],5231)
            for i in range(len(lines)):
                for variant in [lines[:i]+lines[i+1:],lines+[lines[i]]]:
                    write(variant)
                    with self.assertRaises(ValueError):verify_receipt(trial,root)
            for i,replacement in [(3,lines[3].replace('4000','4001')),
                                  (4,lines[4].replace('5231','5235')),
                                  (1,lines[1].replace('injected=1','injected=0')),
                                  (3,lines[3]+' malformed')]:
                variant=list(lines);variant[i]=replacement;write(variant)
                with self.assertRaises(ValueError):verify_receipt(trial,root)
            write(lines)
            with self.assertRaises(ValueError):verify_receipt(None,root)
            write([lines[0].replace('5230','0')])
            self.assertFalse(verify_receipt(dict(trial,inject=0),root)['degraded'])
            strict=[lines[0].replace('original=1','original=0'),lines[1].replace('fallback=1','fallback=0')]
            write(strict);self.assertTrue(verify_receipt(dict(trial,policy='strict'),root)['degraded'])


if __name__=='__main__':unittest.main()
