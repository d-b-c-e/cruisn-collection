from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import steering_reconstruction as s


def inp(states=None, rom='crusnexo', sensitivity=100, reverse=0):
    if states is None:
        states = [(0, 0), (65536, 0), (65536, 65536)]
    header = bytearray(64)
    header[:8] = b'MAMEINP\0'; header[16:18] = b'\x03\x00'
    header[20:20 + len(rom)] = rom.encode()
    payload = bytearray()
    for n, (accum, previous) in enumerate(states):
        payload.extend(struct.pack('<iqI', 0, n * 20_000_000_000_000_000, 100))
        for tag in s.LAYOUTS[rom]:
            steering = tag == s.STEERING[rom]
            payload.extend(struct.pack('<II', 128 if steering else 0, 0))
            if tag in s.ANALOG_LAYOUTS[rom]:
                payload.extend(struct.pack('<iiiB', accum if steering else 0,
                                           previous if steering else 0, sensitivity, reverse))
    return bytes(header) + zlib.compress(payload)


class SteeringReconstructionTests(unittest.TestCase):
    def test_all_game_layouts_preserve_interpolation_in_both_directions(self):
        for rom in s.LAYOUTS:
            with self.subTest(rom=rom):
                rec = s.SteeringRecording(inp(rom=rom), rom)
                self.assertEqual(rec.sample(20_000_000_000_000_000), 128)
                self.assertEqual(rec.sample(30_000_000_000_000_000), 184)
                self.assertEqual(rec.sample(40_000_000_000_000_000), 240)
                rec = s.SteeringRecording(inp([(0, 0), (-65536, 0), (-65536, -65536)], rom), rom)
                self.assertEqual(rec.sample_csv('0.030000000000'), 72)

    def test_recorded_sensitivity_reversal_clamp_and_signed_truncation(self):
        rec = s.SteeringRecording(inp([(0, 0), (262144, 0), (262144, 262144)],
                                    sensitivity=25, reverse=1), 'crusnexo')
        self.assertEqual(rec.sample_csv('0.030000000000'), 72)
        self.assertEqual(s.port_value(2**30, 25, 0), 240)
        self.assertEqual(s.port_value(-2**30, 25, 0), 16)
        self.assertEqual(s.trunc(-5, 2), -2)
        self.assertEqual(s.port_value(-293, 100, 0), 127)
        self.assertEqual(s.port_value(293, 100, 0), 129)

    def test_sampling_does_not_reapply_live_gain_or_curve(self):
        rec = s.SteeringRecording(inp(), 'crusnexo')
        with patch.dict('os.environ', {'MIDV_STEER_GAIN': '400', 'MIDV_STEER_CURVE': '25'}):
            self.assertEqual(rec.sample_csv('0.030000000000'), 184)

    def test_rounded_clocks_fail_on_ambiguous_input_and_unknown_ends(self):
        # A digital change may leave a discontinuity in effective analog state.
        rec = s.SteeringRecording(inp([(0, 0), (65536, 65536), (0, 65536)]), 'crusnexo')
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            rec.sample_csv('0.020000000000')
        for time in (-1, rec.times[-1] + 1):
            with self.assertRaises(ValueError): rec.sample(time)
        for time in ('nan', 'Infinity', '-0.000000000001', '86401.000000000000', '0.03'):
            with self.assertRaises(ValueError): s.clock_interval(time)
        with self.assertRaises(ValueError): rec.sample_csv('0.000000000000')

    def test_bad_identity_compression_settings_and_payloads_fail(self):
        original = inp()
        for data in (b'', original[:-1], original + b'junk', b'NO'+original[2:],
                     inp(sensitivity=0), inp(reverse=2), inp(states=[(0, 0)])):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                s.SteeringRecording(data, 'crusnexo')
        with self.assertRaises(ValueError): s.SteeringRecording(original, 'crusnusa')
        with patch.object(s, 'MAX_BYTES', 128), self.assertRaises(ValueError):
            s.SteeringRecording(original, 'crusnexo')
        payload = bytearray(zlib.decompress(original[64:]))
        struct.pack_into('<q', payload, 4, 1)  # Initial input must start at zero.
        with self.assertRaises(ValueError):
            s.SteeringRecording(original[:64]+zlib.compress(payload), 'crusnexo')

    def fixture(self, root):
        run = root/'run'; (run/'input').mkdir(parents=True)
        (root/'report.json').write_text(json.dumps({'passed': True}))
        (run/'invocation.json').write_text(json.dumps(dict(command=['mame', 'crusnexo'],
            executable_sha256='a'*64, environment={'MIDV_FFB': '0'})))
        (run/'input/session.inp').write_bytes(inp())
        (run/'frames.csv').write_text('frame,emulated_seconds,:ANALOG3\n'
                                     '1,0.020000000000,128\n2,0.040000000000,240\n')
        (run/'exotica-adc.csv').write_text('frame,time,pc,address,value\n1,0.030000000000,856c,9c000b,b8\n')
        return run

    def test_independent_frames_and_actual_adc_join_with_explicit_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.fixture(Path(tmp)); report = s.verify(run, 'crusnexo', True)
            self.assertTrue(report['passed'])
            self.assertFalse(report['physical_angle_verified'])
            self.assertFalse(report['normalization_accepted'])
            self.assertEqual(report['actual_adc']['steering_reads'], 1)
            self.assertEqual(report['actual_adc']['max_frame_snapshot_difference'], 56)
            self.assertIn('input/session.inp', report['inputs'])

    def test_mismatched_evidence_adc_consumer_timing_and_polarity_fail(self):
        mutations = [('frames.csv', ',128\n', ',129\n'),
                     ('frames.csv', '0.020000000000', '0.020010000000'),
                     ('exotica-adc.csv', ',b8\n', ',b9\n'),
                     ('exotica-adc.csv', ',856c,', ',856d,'),
                     ('exotica-adc.csv', '0.030000000000', '0.010000000000'),
                     ('invocation.json', '"MIDV_FFB": "0"', '"MIDV_FFB": "1"'),
                     ('invocation.json', '"MIDV_FFB": "0"', '"MIDV_FFB": "0", "MIDZ_WHEEL_INVERT": "1"')]
        for name, old, new in mutations:
            with self.subTest(name=name,old=old), tempfile.TemporaryDirectory() as tmp:
                run=self.fixture(Path(tmp)); path=run/name
                text=path.read_text(); self.assertIn(old,text); path.write_text(text.replace(old,new))
                with self.assertRaises(ValueError): s.verify(run, 'crusnexo', True)


if __name__ == '__main__':
    unittest.main()
