from pathlib import Path
import struct
import sys
import unittest
import zlib
import json
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from synthesize_input import ANALOG, ANALOG_LAYOUTS, STEERING, PORTS, STRIDE, LAYOUTS, generate, capture_schedule, main


class SyntheticInputTests(unittest.TestCase):
    def test_sparse_capture_uses_global_frame_alignment_and_bounds(self):
        self.assertEqual(capture_schedule('3060:5460',400,5500)['SNAP_MAX'],'6')
        for interval,every,stop in [('10:20',100,100),('1:1000',1,2000),
                ('10:99',1,100),('bad',1,100),('10:20',0,100)]:
            with self.subTest(interval=interval,every=every),self.assertRaises(ValueError):
                capture_schedule(interval,every,stop)

    def test_record_only_retains_explicit_unqualified_result_without_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);seed=root/'seed';(seed/'record/input').mkdir(parents=True)
            (seed/'record/input/session.inp').write_bytes(self.seed())
            (seed/'case.json').write_text(json.dumps(dict(rom='crusnusa',
                evidence=dict(columns=['frame','time','x','y',*PORTS]),
                command=['exe','crusnusa'],settings={})),encoding='utf-8')
            scenario=root/'scenario.json';scenario.write_text('{"frames": 2}',encoding='utf-8')
            work=root/'out';recording=MagicMock();recording.path=work/'case'
            recording.manifest={'status':'recorded'}
            recording.prepare.return_value=(['exe','crusnusa'],{},work/'runtime')
            with patch('synthesize_input.Recording',return_value=recording), \
                 patch('synthesize_input.execute',return_value={'returncode':0}), \
                 patch('synthesize_input.replay.main') as replay_main:
                self.assertEqual(main([str(seed),str(scenario),'--output',str(work),'--record-only']),0)
                replay_main.assert_not_called()
            report=json.loads((work/'report.json').read_text(encoding='utf-8'))
            self.assertTrue(report['recorded'])
            self.assertFalse(report['passed'])
            self.assertFalse(report['identity_replayed'])

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
