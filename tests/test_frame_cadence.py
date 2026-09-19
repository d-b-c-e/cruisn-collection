import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from analyze_frame_cadence import analyze


class Cadence(unittest.TestCase):
    def fixture(self, root):
        (root / 'invocation.json').write_text(json.dumps({'environment': {'SNAP_EVERY': '2'}}), encoding='utf-8')
        (root / 'stdout.log').write_text('session.lua: snapshot at frame 2\nsession.lua: snapshot at frame 4\n', encoding='utf-8')
        (root / 'frames.csv').write_text(
            'frame,emulated_seconds,host_seconds\n1,0.02,0.01\n2,0.04,0.03\n3,0.06,0.07\n4,0.08,0.08\n', encoding='utf-8')

    def test_snapshot_cost_belongs_to_next_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            result = analyze(root, 2, 4)
            self.assertEqual(result['all_callbacks']['intervals'], 3)
            self.assertEqual(result['after_snapshot']['intervals'], 1)
            self.assertEqual(result['after_snapshot']['over_threshold'], 1)
            self.assertEqual(result['other_callbacks']['over_threshold'], 0)
            self.assertEqual(result['spikes'][0]['frame'], 3)
            self.assertEqual(len(result['hashes']), 3)

    def test_missing_ack_or_window_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'fully recorded'): analyze(root, 2, 5)
            (root / 'stdout.log').write_text('', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'acknowledgments'): analyze(root, 2, 4)

    def test_corrupt_clock_and_duplicate_frames_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            path = root / 'frames.csv'; original = path.read_text(encoding='utf-8')
            for old, new in [('3,0.06,0.07', '3,0.06,nan'),
                             ('3,0.06,0.07', '3,0.06,0.02'),
                             ('3,0.06,0.07', '3,0.01,0.07'),
                             ('3,0.06,0.07', '2,0.06,0.07')]:
                with self.subTest(new=new):
                    path.write_text(original.replace(old, new), encoding='utf-8')
                    with self.assertRaises(ValueError): analyze(root, 2, 4)


if __name__ == '__main__': unittest.main()
