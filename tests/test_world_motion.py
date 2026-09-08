from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from compare_world_motion import compare, read_trace, CAMERA


class MotionTests(unittest.TestCase):
    def test_camera_and_adc_are_independent_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('original', 'candidate')]
            camera = ','.join(CAMERA) + '\n'
            camera += '100,' + ','.join(['0'] * 12) + '\n'
            camera += '101,' + ','.join(['1'] * 12) + '\n'
            adc = 'frame,time,pc,value\n100,1.000000000000,123,80\n101,1.02,123,81\n'
            for path in paths:
                path.mkdir()
                (path / 'world-camera.csv').write_text(camera)
                (path / 'world-adc.csv').write_text(adc)
            self.assertTrue(compare(*paths)['passed'])
            for path in paths:
                (path / 'usa-camera.csv').write_text(camera)
                (path / 'usa-adc.csv').write_text(adc)
            self.assertTrue(compare(*paths, prefix='usa')['passed'])
            self.assertIn('USA',compare(*paths, prefix='usa')['scope'])
            with self.assertRaises(ValueError):compare(*paths, prefix='offroad')
            (paths[1] / 'world-camera.csv').write_text(camera.replace('101,1,', '101,2,'))
            result = compare(*paths)
            self.assertFalse(result['passed'])
            self.assertEqual(result['first_camera_difference_frame'], 101)
            self.assertEqual(result['camera_equal_frame_intervals'], [[100,100]])
            self.assertEqual(result['camera_equal_frames'], 1)
            self.assertTrue(result['adc_frame_value_pc_equal'])
            (paths[1] / 'world-camera.csv').write_text(camera)
            (paths[1] / 'world-adc.csv').write_text(adc.replace('1.000000000000', '1.000000000001'))
            result = compare(*paths)
            self.assertFalse(result['passed'])
            self.assertTrue(result['camera_equal'])
            self.assertTrue(result['adc_frame_value_pc_equal'])
            self.assertFalse(result['adc_times_equal'])
            (paths[1] / 'world-adc.csv').write_text(adc.replace(',81', ',82'))
            result = compare(*paths)
            self.assertEqual(result['first_adc_frame_value_pc_difference'], {
                'index': 1, 'reference': [101,0x123,0x81], 'candidate': [101,0x123,0x82]})

    def test_missing_duplicate_and_truncated_camera_samples_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'camera.csv'
            header = ','.join(CAMERA) + '\n'
            def row(frame): return str(frame) + ',' + ','.join(['0'] * 12) + '\n'
            for data in (header, header + row(10) + row(12), header + row(10) + row(10), header + '10,0\n'):
                path.write_text(data)
                with self.assertRaises(ValueError): read_trace(path, CAMERA)

