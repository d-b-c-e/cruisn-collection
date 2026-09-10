import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_state import transition,floating
from scenery_c31 import F


def context():
    return dict(quad_size=10,ucode=0xc0,palette=0,texture=0,yscale=0,zoffset=0,
                matrix=[float(i%4==0) for i in range(9)],translation=[0.]*4,light=[0.]*3,
                regs=[0]*128,render=[0]*80)


class ZeusStateTests(unittest.TestCase):
    def test_private_inheritance_and_explicit_reset(self):
        ctx=context();before=copy.deepcopy(ctx);f=lambda n:F.integer(n).store()
        model=[0x36200000,0x150007ff,0x36200000,0x05000123]
        state=[0x16000000,f(-2),f(5),f(100)]
        after,loads=transition(ctx,model,state,0x123456)
        self.assertEqual(ctx,before);self.assertEqual(loads,[])
        self.assertEqual(after['render'][0x15],2047);self.assertEqual(after['texture'],0x123)
        self.assertEqual(after['translation'],[-2.,5.,100.,0.])
        self.assertEqual(after['regs'][8],0x123456)
        self.assertEqual(after['regs'][0x18:0x1a],[6,4])
        cleared,_=transition(after,[],[0x05200000,0x15000000,*state],1)
        self.assertEqual(cleared['render'][0x15],0);self.assertEqual(after['render'][0x15],2047)

    def test_material_requests_are_explicit(self):
        ctx=context();state=[0x32000000,0x05410000,0x136,0x05400000,0x00050003,
                            0x05410000,0x00010002,0x05400000,0x00840001,
                            0x16000000,*([0x80000000]*3)]
        after,loads=transition(ctx,[],state,2)
        self.assertEqual(after['quad_size'],14);self.assertEqual(after['ucode'],0x136)
        self.assertEqual(after['palette'],1026)
        self.assertEqual(loads,[dict(kind=5,source=0x136,control=0x50003),dict(kind=4,source=0x10002,control=0x840001)])
        self.assertEqual(ctx['palette'],0)

    def test_unsupported_or_partial_commands_do_not_mutate(self):
        ctx=context();before=copy.deepcopy(ctx);state=[0x16000000,*([0x80000000]*3)]
        for model,setup in (([0x38000000,0],state),([0x36200000,0x08000001],state),
                            ([],[0x07000000,0,0,0]),([],state+[0x99000000]),
                            ([],[0x05400000,0x90000,*state])):
            with self.assertRaises(ValueError):transition(ctx,model,setup,0)
            self.assertEqual(ctx,before)
        self.assertEqual(floating(F.integer(-10).store()),-10.)


if __name__=='__main__':unittest.main()
