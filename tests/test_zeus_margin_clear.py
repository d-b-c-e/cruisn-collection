from pathlib import Path
from types import SimpleNamespace
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_margin_clear import configure,verify_receipt


class ZeusMarginClearTests(unittest.TestCase):
    def test_recording_compatibility_and_explicit_scope(self):
        old={'MIDZ_GL':'1'}
        self.assertIsNone(configure(SimpleNamespace(),'crusnexo',old))
        self.assertEqual(old,{'MIDZ_GL':'1'})
        for mode,page in [('legacy',0),('page',1)]:
            settings=dict(old)
            result=configure(SimpleNamespace(zeus_margin_clear=mode,candidate=Path('test.exe')),'crusnexo',settings)
            self.assertEqual(result,dict(page=page,explicit=True))
            self.assertEqual(configure(SimpleNamespace(),'crusnexo',settings),dict(page=page,explicit=False))
        for rom,args,settings in [('crusnusa',SimpleNamespace(),dict(MIDZ_GL='1',MIDZ_GL_MARGIN_PAGE_CLEAR='1')),
                ('crusnexo',SimpleNamespace(zeus_margin_clear='page'),dict(old)),
                ('crusnexo',SimpleNamespace(),dict(MIDZ_GL_MARGIN_PAGE_CLEAR='1')),
                ('crusnexo',SimpleNamespace(),dict(MIDZ_GL='1',MIDZ_GL_MARGIN_PAGE_CLEAR='2')),
                ('crusnexo',SimpleNamespace(headless=True),dict(MIDZ_GL='1',MIDZ_GL_MARGIN_PAGE_CLEAR='0')),
                ('crusnexo',SimpleNamespace(native_renderer=True),dict(MIDZ_GL='1',MIDZ_GL_MARGIN_PAGE_CLEAR='1'))]:
            with self.subTest(rom=rom,args=args,settings=settings):
                with self.assertRaises(ValueError):configure(args,rom,settings)

    def test_requested_native_policy_and_valid_completion_required(self):
        self.assertIsNone(verify_receipt(None,''))
        for page,clears,expanded in [(0,123,0),(1,456,123),(1,0,0)]:
            text=f'MIDZ_GL_MARGIN_PAGE_CLEAR={page}\nMIDZ_MARGIN_RESULT page={page} clears={clears} expanded={expanded}\n'
            self.assertEqual(verify_receipt(dict(page=page),text),dict(page=page,clears=clears,expanded=expanded))
            for broken in ('',text.splitlines()[0]+'\n',text+text,
                    text.replace(f'RESULT page={page}',f'RESULT page={1-page}'),
                    text.replace(f'expanded={expanded}',f'expanded={clears+1}')):
                with self.subTest(broken=broken):
                    with self.assertRaises(ValueError):verify_receipt(dict(page=page),broken)
