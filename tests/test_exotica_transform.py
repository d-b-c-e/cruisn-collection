import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_transform import prepare, packet, select_model, matrix_update
from scenery_c31 import F


class ExoticaTransformTests(unittest.TestCase):
    def test_transform_and_modes(self):
        f=lambda x:F.integer(x).store()
        identity=[f(i%4==0) for i in range(9)]
        rot=identity.copy();rot[0]=rot[8]=f(-1)
        args=([f(10),f(20),f(30)],[f(1),f(2),f(3)],identity,rot,identity)
        r=prepare(*args,0)
        self.assertEqual(r,dict(matrix=rot,translation=[f(9),f(18),f(27)],depth=27))
        self.assertEqual(prepare(*args,0x80),r)
        self.assertEqual(prepare(*args,0x80000)['matrix'],identity)
        self.assertEqual(packet(r,f(1),0),[0x16000000,*r['translation']])
        self.assertEqual(packet(r,f(1),1),[0x07000000,*rot,*r['translation']])
        direct=prepare(*args,3)
        self.assertEqual(direct['translation'],args[0])
        self.assertEqual(direct['matrix'],rot)
        self.assertEqual(direct['depth'],30)
        for mode in (1,2):
            with self.assertRaises(ValueError):prepare(*args,mode)
        with self.assertRaises(ValueError):prepare(args[0][1:],*args[1:],0)
        with self.assertRaises(ValueError):packet(r,f(1),2)

    def test_lod_signed_strict_boundary(self):
        for depth in (-2147483648,-1,0,25000):self.assertEqual(select_model(10,20,depth),10)
        self.assertEqual(select_model(10,20,25001),20)
        self.assertEqual(select_model(10,0,2147483647),10)
        with self.assertRaises(ValueError):select_model(10,20,0xffffffff)

    def test_matrix_cache_forced_and_alternate_cases(self):
        f=lambda x:F.integer(x).store()
        self.assertEqual(matrix_update(0,f(255),f(255)),1)
        self.assertEqual(matrix_update(0x10,f(255),f(255)),0)
        self.assertEqual(matrix_update(0x10,f(255),f(100)),1)
        self.assertEqual(matrix_update(0x80000,f(254),f(100)),0)
        self.assertEqual(matrix_update(0x80000,f(255),f(100)),1)


if __name__=='__main__':unittest.main()
