from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from game_patch import read_patch, verify_patch_ram, late_patch_lua


class PatchTests(unittest.TestCase):
    def test_late_patch_cannot_bypass_old_value_guards(self):
        with self.assertRaises(ValueError):
            late_patch_lua({1: (None, 3)}, 60)

    def test_invalid_or_conflicting_patches_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "patch.txt"
            for data in ("# nothing", "1 2", "1 2 3\n1 2 4", "20000 0 1", "1 0 100000000"):
                p.write_text(data)
                with self.assertRaises(ValueError):
                    read_patch(p)

    def test_reverted_patch_cannot_pass_effective_word_check(self):
        with tempfile.TemporaryDirectory() as td:
            p, ram = Path(td) / "patch.txt", Path(td) / "ram.bin"
            p.write_text("55 13880 27100 # farther\n")
            entries = read_patch(p)
            data = bytearray(0x20000 * 4)
            struct.pack_into("<I", data, 0x55 * 4, 0x13880)
            ram.write_bytes(data)
            self.assertFalse(verify_patch_ram(ram, entries)["passed"])
            struct.pack_into("<I", data, 0x55 * 4, 0x27100)
            ram.write_bytes(data)
            self.assertTrue(verify_patch_ram(ram, entries)["passed"])
            ram.write_bytes(data[:-1])
            with self.assertRaises(ValueError):
                verify_patch_ram(ram, entries)
