from pathlib import Path
from types import SimpleNamespace
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_render_policy import material,configure,verify_receipt
from zeus_rasterize import Replay,QUAD_DTYPE
from test_zeus_model import fixture
from zeus_model import decode


class ZeusPolicyTests(unittest.TestCase):
    def test_independent_depth_alpha_blend_controls(self):
        for mask in range(8):
            m=material(mask,0x82,0x4000,0x20204,64)
            self.assertEqual(m,dict(blend=bool(mask&4),source_alpha=256 if mask&4 else 64,
                depth_test=bool(mask&2),depth_write=bool(mask&2)))
            disabled=material(mask,0x82,0x1020,0x20202,512)
            self.assertFalse(disabled['depth_test']);self.assertFalse(disabled['depth_write'])
            self.assertEqual(disabled['source_alpha'],256)
            r=fixture();r['render_policy']=mask;r['words'][1]=0x82
            fields=decode(r)[0][0][0]
            self.assertEqual(fields[9]&512,512 if mask&1 else 0)
            self.assertEqual(fields[9]&24,24 if mask&2 else 0)

    def test_depth_floor_occlusion_and_clear_precedence(self):
        r=np.zeros(1,QUAD_DTYPE)[0];r['zbuf_min']=50;r['solidcolor']=0x7c00;r['srcAlpha']=256
        def run(flags,z=100):
            replay=Replay.__new__(Replay);replay.stat_pixels=0
            replay.color=np.zeros(3,np.uint32);replay.depth=np.full(3,125,np.int32)
            replay.wave=np.zeros(16,np.uint8);replay.wave16=replay.wave.view(np.uint16)
            replay.pal=np.zeros(256,np.uint32)
            replay.extent(r,flags,0,0,3,np.array([z,0,0,1],np.float32),np.zeros(4,np.float32))
            return replay
        self.assertTrue(np.all(run(1|4|8|16).color==0)) # 100+50 behind125
        floor=run(1|4|8|16|512)
        self.assertTrue(np.all(floor.color==0xf80000));self.assertTrue(np.all(floor.depth==100))
        self.assertTrue(np.all(run(1|4|8|16|512,z=25).depth==50))
        self.assertTrue(np.all(run(1|4|16|32|512).depth==0xffffff))

    def test_recording_compatibility_and_candidate_acknowledgment(self):
        settings={};self.assertIsNone(configure(SimpleNamespace(),'crusnexo',settings));self.assertEqual(settings,{})
        a=SimpleNamespace(zeus_upstream='all',candidate=Path('test.exe'))
        trial=configure(a,'crusnexo',settings);self.assertEqual(settings,{'MIDZ_UPSTREAM_RENDER':'7'})
        verify_receipt(trial,'MIDZ_UPSTREAM_RENDER=7 PR=16094\n')
        for text in ('','MIDZ_UPSTREAM_RENDER=1 PR=16094'):
            with self.assertRaises(ValueError):verify_receipt(trial,text)
        self.assertEqual(configure(SimpleNamespace(),'crusnexo',settings)['mask'],7)
        for rom,args,s in [('crusnusa',a,{}),('crusnexoa',a,{}),('crusnexo',SimpleNamespace(zeus_upstream='all'),{}),
                           ('crusnexo',SimpleNamespace(),{'MIDZ_UPSTREAM_RENDER':'8'})]:
            with self.assertRaises(ValueError):configure(args,rom,s)
