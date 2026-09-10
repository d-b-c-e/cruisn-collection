import math,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from page_image import HEADER as PAGE_HEADER
from zeus_wide_packet import HEADER,QUAD,MAX_DEPTH,parse,validate_quad


class WidePacketTests(unittest.TestCase):
    def fixture(self,z=50000000):
        page=PAGE_HEADER.pack(0x314d4950,16777216,4096,0,1,2,9,9,0,0,0,0)
        materials=struct.pack('<IIQ4I',0x31544d48,5000,12,len(page),1,0,0)+page
        materials+=struct.pack('<II256I',0,0x84003f,*([0]*256))
        state=[5000,4,0,0,128,0,0,256,0,28,0,400,0,0,0,511,399]
        vertices=[[-80,50,z,0,0,1],[-40,50,z,0,0,1],[-40,90,z,0,0,1],[-80,90,z,0,0,1]]+[[0]*6 for _ in range(4)]
        wire=HEADER.pack(0x31445758,len(materials),1,86,400,3,1,0)+materials+QUAD.pack(0,*state,*sum(vertices,[]))
        return wire,state,vertices

    def test_owned_geometry_header_and_palette_rejection(self):
        wire,_,_=self.fixture();p=parse(wire)
        self.assertEqual((p['page'],p['multiplier'],len(p['quads']),p['quads'][0]['vertices'][0][2]),(400,3,1,50000000))
        for offset in range(0,32,4):
            bad=bytearray(wire);struct.pack_into('<I',bad,offset,0xffffffff)
            with self.assertRaises(ValueError):parse(bad)
        for bad in (wire[:31],wire[:-1],wire+b'\0',struct.pack('<I',0x31444d58)+wire[4:]):
            with self.assertRaises(ValueError):parse(bad)
        bad=bytearray(wire);struct.pack_into('<I',bad,len(wire)-QUAD.size,1)
        with self.assertRaisesRegex(ValueError,'palette'):parse(bad)

    def test_depth_range_bias_and_unsupported_sources(self):
        _,state,vertices=self.fixture(MAX_DEPTH)
        validate_quad(state,vertices,5000,400)
        for flags in (20,28|32,28|256,28|1024):
            s=state.copy();s[9]=flags
            with self.assertRaises(ValueError):validate_quad(s,vertices,5000,400)
        for z in (-1,MAX_DEPTH+4,math.inf,math.nan):
            v=[r.copy() for r in vertices];v[0][2]=z
            with self.assertRaises(ValueError):validate_quad(state,v,5000,400)
        for bias in (1,0x7fffffff):
            s=state.copy();s[10]=bias
            with self.assertRaisesRegex(ValueError,'biased'):validate_quad(s,vertices,5000,400)
        s=state.copy();s[9]|=512;s[10]=MAX_DEPTH;validate_quad(s,vertices,5000,400)
        s[10]=MAX_DEPTH+4
        with self.assertRaises(ValueError):validate_quad(s,vertices,5000,400)
        with self.assertRaises(ValueError):validate_quad(state,vertices,5001,400)
        with self.assertRaises(ValueError):validate_quad(state,vertices,5000,0)

    def test_empty_packet_is_bounded_and_explicit(self):
        wire,_,_=self.fixture();wire=bytearray(wire[:-QUAD.size]);struct.pack_into('<I',wire,8,0)
        self.assertEqual(parse(wire)['quads'],[])


if __name__=='__main__':unittest.main()
