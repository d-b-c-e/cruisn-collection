from pathlib import Path
from types import SimpleNamespace
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_palette import configure,verify_receipt


class ZeusPaletteTests(unittest.TestCase):
    def test_absent_frozen_and_explicit_settings(self):
        old={'MIDZ_GL':'1'}
        self.assertIsNone(configure(SimpleNamespace(),'crusnexo',old))
        self.assertEqual(old,{'MIDZ_GL':'1'})
        for name,guard in [('legacy',0),('guard',1)]:
            settings=dict(old)
            trial=configure(SimpleNamespace(zeus_palette=name,candidate=Path('test.exe')),'crusnexo',settings)
            self.assertEqual(trial,dict(guard=guard,explicit=True))
            self.assertEqual(configure(SimpleNamespace(),'crusnexo',settings),dict(guard=guard,explicit=False))
        for rom,args,settings in [('crusnusa',SimpleNamespace(),{'MIDZ_GL':'1','MIDZ_PALETTE_GUARD':'1'}),
                ('crusnexo',SimpleNamespace(zeus_palette='guard'),dict(old)),
                ('crusnexo',SimpleNamespace(),{'MIDZ_PALETTE_GUARD':'1'}),
                ('crusnexo',SimpleNamespace(),{'MIDZ_GL':'1','MIDZ_PALETTE_GUARD':'2'}),
                ('crusnexo',SimpleNamespace(headless=True),{'MIDZ_GL':'1','MIDZ_PALETTE_GUARD':'0'})]:
            with self.subTest(rom=rom,args=args,settings=settings):
                with self.assertRaises(ValueError):configure(args,rom,settings)

    def test_native_completion_required_and_counters_agree(self):
        self.assertIsNone(verify_receipt(None,''))
        for guard,conflicts,flushes in [(0,32,0),(1,1,1),(1,0,0)]:
            text=f'MIDZ_PALETTE_GUARD={guard}\nMIDZ_PALETTE_RESULT guard={guard} conflicts={conflicts} flushes={flushes}\n'
            self.assertEqual(verify_receipt(dict(guard=guard),text),dict(guard=guard,conflicts=conflicts,flushes=flushes))
            for broken in ('',text.splitlines()[0]+'\n',text+text,text.replace('RESULT guard=',f'RESULT guard={1-guard}'),
                    text.replace(f'flushes={flushes}',f'flushes={flushes+1}')):
                with self.subTest(broken=broken):
                    with self.assertRaises(ValueError):verify_receipt(dict(guard=guard),broken)
