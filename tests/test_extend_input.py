from pathlib import Path
import struct,sys,unittest,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from extend_input import extend
from synthesize_input import LAYOUTS,ANALOG_LAYOUTS,STEERING,generate
import test_synthetic_input as synthetic


class ExtendInputTests(unittest.TestCase):
    def test_exact_prefix_and_first_tail_interpolation_all_layouts(self):
        for rom in LAYOUTS:
            with self.subTest(rom=rom):
                axes=ANALOG_LAYOUTS[rom];wheel=STEERING[rom]
                source=generate(synthetic.SyntheticInputTests().seed(rom),dict(frames=8,analog={
                    tag:[[0,0],[3,.5],[7,-.5 if tag==wheel else .8]] for tag in axes}))
                original=zlib.decompress(source[64:]);stride=len(original)//9
                scenario=dict(frames=4,analog={tag:[[0,0],[2,.25]] for tag in axes},
                    buttons=[dict(port=LAYOUTS[rom][0],mask=4,start=1,end=4)])
                output,report=extend(source,scenario);payload=zlib.decompress(output[64:])
                self.assertEqual(output[:64],source[:64]);self.assertEqual(payload[:len(original)],original)
                self.assertEqual(len(payload),13*stride);self.assertEqual(report['first_synthetic_row'],9)
                at=16
                for tag in LAYOUTS[rom]:
                    if tag==LAYOUTS[rom][0]:
                        self.assertEqual(struct.unpack_from('<I',payload,9*stride+at+4)[0],0)
                        self.assertEqual(struct.unpack_from('<I',payload,10*stride+at+4)[0],4)
                        self.assertEqual(struct.unpack_from('<I',payload,12*stride+at+4)[0],4)
                    at+=8
                    if tag in axes:
                        self.assertEqual(struct.unpack_from('<i',payload,9*stride+at+4)[0],
                                         struct.unpack_from('<i',original,8*stride+at)[0])
                        self.assertEqual(struct.unpack_from('<i',payload,10*stride+at+4)[0],
                                         struct.unpack_from('<i',payload,9*stride+at)[0])
                        at+=13

    def test_reject_incomplete_ambiguous_and_discontinuous_sources(self):
        source=synthetic.SyntheticInputTests().seed()
        scenario=dict(frames=4,analog={tag:[[0,0]] for tag in ANALOG_LAYOUTS['crusnusa']})
        for change in ({'frames':True},{'frames':0},{'frames':36000},{'analog':{':WHEEL':[[0,0]]}},
                       {'analog':{tag:[[0,2]] for tag in ANALOG_LAYOUTS['crusnusa']}},
                       {'buttons':[dict(port=':IN0',mask=1,start=3,end=5)]}):
            with self.assertRaises(ValueError):extend(source,scenario|change)
        payload=bytearray(zlib.decompress(source[64:]))
        with self.assertRaises(ValueError):extend(source[:64]+zlib.compress(payload[:-1]),scenario)
        # Change a later time beyond the first three rows used for codec setup.
        source=generate(source,dict(frames=5));payload=bytearray(zlib.decompress(source[64:]))
        stride=len(payload)//6;payload[4*stride+4]^=1
        with self.assertRaisesRegex(ValueError,'cadence'):extend(source[:64]+zlib.compress(payload),scenario)


if __name__=='__main__':unittest.main()
