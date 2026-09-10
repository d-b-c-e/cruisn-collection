from pathlib import Path
from types import SimpleNamespace
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_rasterize import QUAD_DTYPE
from zeus_sky_repeat import plan
from zeus_sky_options import configure,verify_receipt


def fixture(start=-3020,page=0):
    rows=[]
    for i in range(14):
        q=np.zeros(1,QUAD_DTYPE)[0];q['numverts']=4;q['texdata']=1;q['texwidth']=32
        q['tex_src']=(i%6)*512;q['srcAlpha']=256;q['transcolor']=256;q['flags']=52
        q['rr04']=page;q['clip']=[0,0,511,399];left=start+i*256;right=left+256
        q['verts'][:4]=[[left,-15,123,0,0,1],[right,-15,123,256,0,1],
                         [right,400,123,256,256,1],[left,400,123,0,256,1]]
        rows.append(q)
    return rows


class SkyTests(unittest.TestCase):
    def test_period_and_unchanged_shape_outside_original_view(self):
        for start,side in [(-3020,'right'),(-40,'left')]:
            rows=fixture(start);p=plan(rows);self.assertTrue(p['accepted'])
            self.assertEqual(p['period'],1536);self.assertEqual(p['overlap_comparisons'],16)
            self.assertEqual(len(p['copies']),1);copy=p['copies'][0];self.assertEqual(copy['side'],side)
            q=rows[copy['index']];translated=q['verts'][:4].copy();translated[:,0]+=copy['shift']
            self.assertTrue(np.array_equal(translated[:,1:],q['verts'][:4,1:]))
            self.assertTrue(translated[:,0].min()>=512 if side=='right' else translated[:,0].max()<=0)
        self.assertEqual(plan(fixture(-500))['copies'],[])

    def test_incomplete_or_conflicting_pattern_is_rejected(self):
        for field,index,value in [('verts',(0,3),.25),('verts',(0,0),1),('verts',(2,2),1),
                                  ('rr04',None,400),('flags',None,-24)]:
            rows=fixture()
            if index is None:rows[7][field]=int(rows[7][field])+value
            else:rows[7][field][index]+=value
            with self.subTest(field=field,index=index):self.assertFalse(plan(rows)['accepted'])
        self.assertFalse(plan(fixture()[:7])['accepted'])

    def test_diagnostic_dependencies_and_receipts(self):
        state=dict(MIDZ_GL='1');self.assertIsNone(configure(SimpleNamespace(),'crusnexo',state))
        for mode in ('off','repeat'):
            settings=dict(state,MIDZ_PALETTE_GUARD='1',MIDZ_GL_MARGIN_PAGE_CLEAR='1')
            r=configure(SimpleNamespace(zeus_sky=mode,candidate=Path('test.exe')),'crusnexo',settings)
            self.assertEqual(configure(SimpleNamespace(),'crusnexo',settings),dict(enabled=r['enabled'],explicit=False))
        for missing in ('MIDZ_GL','MIDZ_PALETTE_GUARD','MIDZ_GL_MARGIN_PAGE_CLEAR'):
            state=dict(MIDZ_GL='1',MIDZ_PALETTE_GUARD='1',MIDZ_GL_MARGIN_PAGE_CLEAR='1',MIDZ_SKY_REPEAT='1');state.pop(missing)
            with self.assertRaises(ValueError):configure(SimpleNamespace(),'crusnexo',state)
        good='MIDZ_SKY_REPEAT=1\nMIDZ_SKY_REPEAT_RESULT enabled=1 groups=22 accepted=21 copied=4 budget_rejected=0\n'
        self.assertEqual(verify_receipt(dict(enabled=1),good)['copied'],4)
        for text in ('',good+good,good.replace('accepted=21','accepted=23'),good.replace('copied=4','copied=999'),good.replace('RESULT enabled=1','RESULT enabled=0')):
            with self.assertRaises(ValueError):verify_receipt(dict(enabled=1),text)
