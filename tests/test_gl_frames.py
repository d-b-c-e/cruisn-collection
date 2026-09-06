import csv
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from gl_frames import compare_completed_frames, read_completed_frames


class CompletedGlTests(unittest.TestCase):
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
