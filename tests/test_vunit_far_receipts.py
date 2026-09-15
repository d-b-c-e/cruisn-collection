from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from scenery_c31 import F
from verify_vunit_far_receipts import PACKET,expected_masks,compare

class FarReceiptTests(unittest.TestCase):
    def fixture(self,root,frames=(10,11)):
        q=[0x100,0,0,0,10,1,10,11,0,10,0,1,257,256,0,0]
        depths=[F.integer(n).store() for n in (200000,300000,300000,200000)]
        packets=[(frame,513,1,*q,240000,*depths) for frame in frames]
        raw=[PACKET.pack(*v) for v in packets]
        masks=expected_masks(packets,86)
        a=root/'producer.bin';b=root/'gpu.bin'
        a.write_bytes(b'VFP1'+b''.join(raw))
        b.write_bytes(b'VFG1'+b''.join(v+m.tobytes() for v,m in zip(raw,masks)))
        return a,b

    def test_ordered_delivery_and_masks(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=self.fixture(Path(tmp));result=compare(a,b,9,12)
            self.assertTrue(result['passed']);self.assertEqual(result['packets'],2)
            self.assertEqual((result['first'],result['last']),(10,11))

    def test_changed_delivery_or_mask_rejected(self):
        for offset in (4+8,4+60+16):
            with self.subTest(offset=offset),tempfile.TemporaryDirectory() as tmp:
                a,b=self.fixture(Path(tmp));data=bytearray(b.read_bytes());data[offset]^=1;b.write_bytes(data)
                with self.assertRaises(ValueError):compare(a,b,9,12)

    def test_missing_or_reordered_receipts_rejected(self):
        for kind in ('empty','truncated','missing','order','scope'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                a,b=self.fixture(Path(tmp),(11,10) if kind=='order' else (10,11))
                if kind=='empty':a.write_bytes(b'VFP1');b.write_bytes(b'VFG1')
                if kind=='truncated':b.write_bytes(b.read_bytes()[:-1])
                if kind=='missing':b.write_bytes(b.read_bytes()[:-124])
                with self.assertRaises(ValueError):compare(a,b,11 if kind=='scope' else 9,12)

    def test_equal_invalid_depths_do_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=self.fixture(Path(tmp));source=bytearray(a.read_bytes());gpu=bytearray(b.read_bytes())
            # Both sides claim the same impossible C31 depth; byte equality is insufficient.
            source[4+44:4+48]=b'\0'*4;gpu[4+44:4+48]=b'\0'*4
            a.write_bytes(source);b.write_bytes(gpu)
            with self.assertRaisesRegex(ValueError,'depth'):compare(a,b,9,12)
