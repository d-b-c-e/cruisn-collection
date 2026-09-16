from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from offroad_billboard_source import descriptor
from offroad_billboard import quad


class SourceTests(unittest.TestCase):
    def test_damaged_and_other_classes_do_not_become_static_sources(self):
        d=[0]*11;d[0]=0x800804;d[1]=0xc01000;d[3]=67<<16;b=[0xc02000,100,200]
        self.assertEqual(descriptor(d,7,2,10,b,67,0)[6],0x07078000)
        self.assertIsNone(descriptor(d,7,2,10,b,67,8))
        with self.assertRaises(ValueError):descriptor(d,7,2,10,b,68,0)
        for flags in (0x04004004,0x10000804,0x806):
            d[0]=flags;self.assertIsNone(descriptor(d,7,2,10,b,67,0))
        d[0]=0x804;self.assertIsNotNone(descriptor(d,7,2,10,b,0,0xffffffff))
        with self.assertRaises(ValueError):descriptor(d,7,10,10,b,0,0)
        d[1]=0x1ffff
        with self.assertRaises(ValueError):descriptor(d,7,2,10,b,0,0)

    def test_first_billboard_quad_preserves_orientation_and_uv(self):
        obj=[0]*22;obj[5]=4;obj[18]=100;obj[19]=200
        polygon=[0x00010100,0x02030405,0x06070809,10,0x00030000,0x00090006]
        xyz=[0,0,100,0,10,100,10,10,100,10,0,100]
        result=quad(obj,polygon,xyz,3,0x2000)
        self.assertEqual(result,[0x2100,103,0,0,0,10,10,10,10,0,0x0405,0x0203,0x0809,0x0607,210,0])
        polygon[4]=1
        with self.assertRaises(ValueError):quad(obj,polygon,xyz,3,0)


if __name__=='__main__':unittest.main()
