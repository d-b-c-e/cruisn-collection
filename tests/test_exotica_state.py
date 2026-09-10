import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_state import setup


def sample():
    obj=[0]*32;obj[18]=123;const=[0]*12;commands=[0]*46
    for address,value in {0x67d2:0xc700,0x67d3:0x40000123,0x67d4:0x40000456,
                          0x67d5:0x14000001,0x67d6:0x8100,0x67d7:0xff000000}.items():const[address-0x67d0]=value
    for address,value in {0xb47b:0x32000000,0xb47c:0x1c000000,0xb481:0x05410000,
            0xb482:0x05400000,0xb493:0x05200000,0xb498:0x14004000,0xb499:0x14004062,
            0xb49d:0x15000000,0xb4a0:0x40020202,0xb4a1:0x40020204,
            0xb4a4:0x0c000000,0xb4a6:0x0d000000}.items():commands[address-0xb479]=value
    return [obj,0,[123,10,0xffffffff],const,commands,[10,20,30,40],
            [[0x05410000,i+100,0x05400000,0x50000] for i in range(4)],
            [0x40000000,0x14004000],0x40001]


class ExoticaStateTests(unittest.TestCase):
    def test_inherited_bias_and_explicit_reset(self):
        a=sample();a[1]=0x100;a[0][16]=0x12080000
        fade=setup(*a);self.assertEqual(fade['branch'],'fade')
        self.assertIn(0x150007ff,fade['packet']);self.assertIn(0x0c000008,fade['packet'])
        a[1]=0x8100;light=setup(*a)
        self.assertEqual(light['branch'],'light');self.assertEqual(light['program'],3)
        # Regression: extra lights cannot implicitly erase an inherited depth bias.
        self.assertNotIn(0x15000000,light['packet']);self.assertNotIn(0x150007ff,light['packet'])
        a[1]=0;normal=setup(*a);self.assertEqual(normal['packet'][-1],0x15000000)

    def test_cache_reuse_palette_and_forced_invalidation(self):
        a=sample();before=copy.deepcopy(a);first=setup(*a)
        self.assertEqual(a,before);a[2]=first['cache'];self.assertEqual(setup(*a)['packet'],[])
        a[0][18]=321;palette=setup(*a)
        self.assertEqual(palette['branch'],'cached');self.assertEqual(palette['cache'],[321,10,0])
        self.assertEqual(palette['packet'],[0x32000000,0x05410000,321,0x05400000,0x40001])
        a[1]=0x800;a[2][2]=0;forced=setup(*a)
        self.assertEqual(forced['branch'],'cached')
        self.assertEqual(forced['cache'][2],0xffffffff)
        a[2]=forced['cache'];self.assertEqual(setup(*a)['branch'],'default')

    def test_program_priority_bounds_and_layout_rejection(self):
        a=sample();a[1]=0xc400;result=setup(*a)
        self.assertEqual((result['program'],result['branch']),(1,'flag400'))
        a[1]=0x200;self.assertEqual(setup(*a)['branch'],'flag200')
        for index,value in ((7,[]),(7,[0]*17),(2,[0]),(5,[0]),(6,[[0]*4]*4),(1,-1)):
            bad=copy.deepcopy(a);bad[index]=value
            with self.assertRaises(ValueError):setup(*bad)


if __name__=='__main__':unittest.main()
