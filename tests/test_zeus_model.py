from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_model import decode


def fixture():
    bits=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
    regs=[0]*128;regs[0x66]=0x8e;regs[0x68]=0x9d;regs[0x6c]=9
    regs[0x6a]=bits(256);regs[0x6b]=bits(200)
    render=[0]*80;render[1]=511;render[2]=399;render[0xc]=256
    return dict(frame=1,quad_size=10,texture=0,yscale=0,regs=regs,render=render,
        matrix=[1.,0.,0.,0.,1.,0.,0.,0.,1.],translation=[0.,0.,100.,0.],
        words=[0x229d0000,1,0x38000000,0,0x0001ffff,0xffffffff,0,0,0,0,0xffff0001,0x00010001])


class ZeusModelTests(unittest.TestCase):
    def test_state_isolation_and_material_flags(self):
        r=fixture();r['words']=[0x36200000,0x05000005]+r['words'];original=deepcopy(r)
        quads,stats=decode(r)
        self.assertEqual(r,original);self.assertEqual(stats['draw'],1)
        fields,vertices=quads[0]
        self.assertEqual((fields[3],fields[9],fields[15],fields[16]),(5,28,511,399))
        self.assertLess(vertices[0][0],256);self.assertGreater(vertices[2][0],256)
        r=fixture();r['words'][1]=0x82;fields=decode(r)[0][0][0]
        self.assertTrue(fields[9]&64);self.assertFalse(fields[9]&24)
        r=fixture();r['words']=[0x36200000,0x15ffffff]+r['words']
        self.assertEqual(decode(r)[0][0][0][10],0xffffffff)

    def test_near_clip_and_variable_record_sizes(self):
        r=fixture();baseline=decode(r)[0][0]
        r['quad_size']=14;r['words'] += [0x12345678]*4
        changed=decode(r)[0][0]
        self.assertEqual(changed[0],baseline[0]);self.assertEqual(changed[1].tobytes(),baseline[1].tobytes())
        r=fixture();r['translation'][2]=-100
        self.assertEqual(decode(r)[1]['near'],1)
        r=fixture();r['translation'][2]=0;r['words'][8]=0x0001ffff;r['words'][9]=0x00010001
        self.assertEqual(decode(r)[0][0][0][1],5)

    def test_truncation_unknown_commands_and_palette_load_fail(self):
        for words in (fixture()['words'][:-1],[0xff000000,0],[0x36200000,0x08000000]):
            r=fixture();r['words']=words
            with self.assertRaises(ValueError):decode(r)
        r=fixture();r['regs'][0x6c]=31
        with self.assertRaises(ValueError):decode(r)


if __name__=='__main__':unittest.main()
