from pathlib import Path
import struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_capture import parse_records
from compare_zeus_capture import signatures


class ZeusCaptureTests(unittest.TestCase):
    def test_effective_palette_is_part_of_each_quad_signature(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'pal_table.bin').write_bytes(bytes(1024))
            quad=bytearray(260);struct.pack_into('<II',quad,0,4000,4)
            record=struct.pack('<II',1,260)+quad
            (p/'records.bin').write_bytes(record)
            original=signatures(p)[0]
            (p/'records.bin').write_bytes(struct.pack('<II',2,1024)+bytes([1])*1024+record)
            changed=signatures(p)[1]
            self.assertEqual(original[:2],changed[:2]);self.assertNotEqual(original[2],changed[2])

    def test_rejects_silently_truncated_or_unknown_records(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'records.bin';quad=bytearray(260);struct.pack_into('<II',quad,0,4000,4)
            valid=struct.pack('<II',1,260)+quad+struct.pack('<II',3,16)+bytes(16)
            p.write_bytes(valid);self.assertEqual([k for k,_ in parse_records(p)],[1,3])
            for bad in (b'',valid[:-1],valid+b'\x01',struct.pack('<II',9,16)+bytes(16),struct.pack('<II',1,259)+quad[:-1]):
                p.write_bytes(bad)
                with self.assertRaises(ValueError):parse_records(p)

    def test_rejects_invalid_used_vertices(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'records.bin'
            for count,value in ((2,0.0),(9,0.0),(4,float('nan'))):
                quad=bytearray(260);struct.pack_into('<II',quad,0,4000,count);struct.pack_into('<f',quad,68,value)
                p.write_bytes(struct.pack('<II',1,260)+quad)
                with self.assertRaises(ValueError):parse_records(p)
