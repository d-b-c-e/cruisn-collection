from pathlib import Path
import struct
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from synthesize_input import ANALOG, ANALOG_LAYOUTS, STEERING, PORTS, STRIDE, LAYOUTS, generate


class SyntheticInputTests(unittest.TestCase):
    def seed(self, rom="crusnusa"):
        header = bytearray(64)
        header[:8] = b"MAMEINP\0"
        header[16] = 3
        header[20:20 + len(rom)] = rom.encode("ascii")
        payload = bytearray()
        for n in range(3):
            payload.extend(struct.pack("<iqI", 0, n * 17000000000000000, 1 << 20))
            for tag in LAYOUTS[rom]:
                payload.extend(struct.pack("<II", 128 if tag == ":WHEEL" else 0, 0))
                if tag in ANALOG_LAYOUTS[rom]:
                    value = 0 if tag == STEERING[rom] else -262144
                    payload.extend(struct.pack("<iiiB", value, value, 25, 0))
        return bytes(header) + zlib.compress(payload)

    def test_world_and_offroad_keep_serial_port_separate_from_wheel(self):
        for rom in ("crusnwld", "crusnwld24", "offroadc"):
            with self.subTest(rom=rom):
                data = zlib.decompress(generate(self.seed(rom), {"frames": 2,
                    "analog": {":WHEEL": [[0, .5]]}})[64:])
                # Their final eight bytes are the separate serial-PIC port.
                self.assertEqual(data[STRIDE - 8:STRIDE], bytes(8))
                self.assertEqual(struct.unpack_from("<i", data, STRIDE - 21)[0], 131072)

    def test_analog_current_and_previous_survive_a_direction_change(self):
        data = zlib.decompress(generate(self.seed(), {"frames": 4, "analog": {
            ":WHEEL": [[0, 0], [1, .5], [3, -.5]]}})[64:])
        offset = STRIDE - 13
        self.assertEqual(struct.unpack_from("<ii", data, STRIDE + offset), (131072, 0))
        self.assertEqual(struct.unpack_from("<ii", data, STRIDE * 3 + offset), (-131072, 131072))

    def test_exotica_keeps_pedals_steering_and_serial_distinct(self):
        data = zlib.decompress(generate(self.seed('crusnexo'), {'frames':2,'analog':{
            ':ANALOG1':[[0,0]], ':ANALOG2':[[0,1]], ':ANALOG3':[[0,-.5]]}})[64:])
        self.assertEqual(len(data),151*3)
        self.assertEqual(struct.unpack_from('<i',data,32)[0],-262144) # brake
        self.assertEqual(struct.unpack_from('<i',data,53)[0],262144)  # accelerator
        self.assertEqual(struct.unpack_from('<i',data,74)[0],-131072) # steering
        self.assertEqual(data[143:151],bytes(8)) # serial IOASIC

    def test_exotica_preserves_first_refresh_rounding(self):
        seed=self.seed('crusnexo');payload=bytearray(zlib.decompress(seed[64:]))
        first=17502471248760000;step=17502471248764376
        struct.pack_into('<q',payload,151+4,first)
        struct.pack_into('<q',payload,302+4,first+step)
        data=zlib.decompress(generate(seed[:64]+zlib.compress(payload),{'frames':4})[64:])
        self.assertEqual(struct.unpack_from('<q',data,151+4)[0],first)
        self.assertEqual(struct.unpack_from('<q',data,604+4)[0],first+3*step)

    def test_wrong_rom_and_out_of_range_pedals_are_rejected(self):
        bad = bytearray(self.seed()); bad[20] = ord("x")
        with self.assertRaises(ValueError):
            generate(bad, {"frames": 4})
        with self.assertRaises(ValueError):
            generate(self.seed(), {"frames": 4, "analog": {":ACCEL": [[0, -0.5]]}})
