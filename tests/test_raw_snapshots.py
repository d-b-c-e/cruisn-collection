from pathlib import Path
import struct
import sys
import tempfile
import unittest

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from raw_snapshots import read_raw, convert_raw_snapshots


class RawSnapshotTests(unittest.TestCase):
    def test_rgb_order_and_dimensions_survive_conversion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "raw-snap").mkdir(); (root / "snap").mkdir()
            p = root / "raw-snap" / "frame_00000060.raw"
            p.write_bytes(struct.pack("<8sIIII", b"CRSNRAW1", 2, 1, 0xff123456, 0xffabcdef))
            self.assertEqual(read_raw(p).tobytes(), bytes.fromhex("123456abcdef"))
            self.assertEqual(convert_raw_snapshots(root), 1)
            Image.new("RGB", (2,1), "red").save(root / "snap" / "frame_00000060.png")
            with self.assertRaisesRegex(ValueError, "refusing overwrite"):
                convert_raw_snapshots(root)

    def test_partial_pixels_are_never_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "frame.raw"
            for data in (b"CRSN", struct.pack("<8sII", b"CRSNRAW1", 2, 1) + b"\0" * 7):
                p.write_bytes(data)
                with self.assertRaises(ValueError): read_raw(p)
