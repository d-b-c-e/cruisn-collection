import csv
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from gl_frames import compare_completed_frames, read_completed_frames, main, requested_frames, IncompleteCaptureError


class CompletedGlTests(unittest.TestCase):
    def test_capture_preflight_counts_global_cadence(self):
        self.assertEqual(list(requested_frames(31, 35, 2, 2)), [32, 34])
        for args in ((31,35,2,1), (31,31,2), (0,10,0), (-1,5,1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                requested_frames(*args)

    def test_incomplete_capture_retains_missing_and_unexpected_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'run'
            self.fixture(path, (30,32,35))
            with self.assertRaises(IncompleteCaptureError) as caught:
                read_completed_frames(path, iter((30,32,34,36)))
            report = caught.exception.capture_diagnostics
            self.assertEqual(report['missing_frames'], [34,36])
            self.assertEqual(report['unexpected_frames'], [35])
            self.assertEqual(report['captured_count'], 3)
            self.assertEqual(report['last_captured'], 35)
            self.assertEqual(report['dimensions'], [(3,2)])

    def fixture(self, path, frames=(30, 31), dropped=0, color="red"):
        path.mkdir()
        with (path / "captures.csv").open("w", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(("file", "last_received_frame", "completed_frame", "width", "height", "dropped_messages"))
            for i, frame in enumerate(frames):
                name = f"{i}.png"
                Image.new("RGB", (3, 2), color).save(path / name)
                writer.writerow((name, frame, frame, 3, 2, dropped))

    def test_pixel_change_is_not_a_passing_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            self.fixture(a)
            self.fixture(b, color="blue")
            self.assertEqual(compare_completed_frames(a, a, range(30, 32))["frames"], 2)
            self.assertEqual(compare_completed_frames(a, b)["different_frames"], [30, 31])

    def test_missing_duplicate_and_dropped_frames_fail(self):
        for frames, dropped in (((30,), 0), ((30, 30), 0), ((30, 31), 1)):
            with self.subTest(frames=frames, dropped=dropped), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "run"
                self.fixture(path, frames, dropped)
                with self.assertRaises(ValueError):
                    read_completed_frames(path, range(30, 32))

    def test_sparse_pixel_evidence_and_reused_file_rejection(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / 'a', root / 'b'
            self.fixture(a, (30, 32, 34))
            self.fixture(b, (30, 32, 34))
            with Image.open(b / '1.png') as im:
                im.putpixel((2, 1), (0, 0, 255))
                im.save(b / '1.png')
            report, sheet = root / 'report.json', root / 'sheet.png'
            self.assertEqual(main([str(a), str(b), '--frames', '30:34', '--every', '2',
                                   '--details', '--contact-sheet', str(sheet), '--report', str(report)]), 1)
            data = json.loads(report.read_text())
            self.assertNotIn('error', data)
            self.assertEqual(data['different_frames'], [32])
            self.assertEqual(data['pixel_changes'][0]['changed_pixels'], 1)
            self.assertEqual(data['pixel_changes'][0]['bounds_xyxy_exclusive'], [2, 1, 3, 2])
            self.assertTrue(sheet.is_file())
            receipts = (b / 'captures.csv').read_text().replace('1.png', '0.png')
            (b / 'captures.csv').write_text(receipts)
            with self.assertRaisesRegex(ValueError, 'filename was reused'):
                read_completed_frames(b)

    def test_sparse_cadence_matches_global_native_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root / 'run', (32, 34))
            self.assertEqual(main([str(root/'run'), str(root/'run'), '--frames', '31:35',
                '--every', '2', '--report', str(root/'report.json')]), 0)
            self.assertTrue(compare_completed_frames(root/'run', root/'run', iter((32, 34)))['passed'])
