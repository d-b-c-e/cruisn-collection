from pathlib import Path
import struct
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from synthesize_input import ANALOG, PORTS, STRIDE, generate


class SyntheticInputTests(unittest.TestCase):
    def seed(self):
        header = bytearray(64)
        header[:8] = b"MAMEINP\0"
        header[16] = 3
        header[20:28] = b"crusnusa"
        payload = bytearray()
        for n in range(3):
            payload.extend(struct.pack("<iqI", 0, n * 17000000000000000, 1 << 20))
            for tag in PORTS:
                payload.extend(struct.pack("<II", 128 if tag == ":WHEEL" else 0, 0))
                if tag in ANALOG:
                    value = 0 if tag == ":WHEEL" else -262144
                    payload.extend(struct.pack("<iiiB", value, value, 25, 0))
        return bytes(header) + zlib.compress(payload)

    def test_analog_current_and_previous_survive_a_direction_change(self):
        data = zlib.decompress(generate(self.seed(), {"frames": 4, "analog": {
            ":WHEEL": [[0, 0], [1, .5], [3, -.5]]}})[64:])
        offset = STRIDE - 13
        self.assertEqual(struct.unpack_from("<ii", data, STRIDE + offset), (131072, 0))
        self.assertEqual(struct.unpack_from("<ii", data, STRIDE * 3 + offset), (-131072, 131072))

    def test_wrong_rom_and_out_of_range_pedals_are_rejected(self):
        bad = bytearray(self.seed()); bad[20] = ord("x")
        with self.assertRaises(ValueError):
            generate(bad, {"frames": 4})
        with self.assertRaises(ValueError):
            generate(self.seed(), {"frames": 4, "analog": {":ACCEL": [[0, -0.5]]}})
