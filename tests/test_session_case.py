import csv
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from session_case import compare_evidence, read_trace, session_evidence


class SessionTests(unittest.TestCase):
    def case(self, directory, wheel=128, color="black", count=3):
        directory.mkdir()
        (directory / "snap").mkdir()
        with open(directory / "frames.csv", "w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["frame", "emulated_seconds", "host_seconds", "speed_percent", ":WHEEL"])
            for n in range(1, count + 1):
                writer.writerow([n, n / 60, n / 50, 1, wheel if n == 2 else 128])
                Image.new("RGB", (3, 2), color).save(directory / "snap" / f"frame_{n:08d}.png")
        (directory / "launch.log").write_text("\n".join(
            [f"session.lua: snapshot at frame {n}" for n in range(1, count + 1)] +
            [f"session.lua: stopped at frame {count}"]))
        return session_evidence(directory, 1, 0)

    def test_input_and_pixel_changes_are_independently_reported(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            ea = self.case(a)
            eb = self.case(b, wheel=140, color="red")
            report = compare_evidence(a, b, ea, eb)
            self.assertFalse(report["passed"])
            self.assertEqual(report["first_input_mismatches"], [2])
            self.assertEqual(report["pixel_mismatches"], 3)
            self.assertEqual(eb["input_coverage"][":WHEEL"]["distinct"], 2)

    def test_truncated_replay_does_not_pass_against_longer_recording(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            ea, eb = self.case(a), self.case(b, count=2)
            with self.assertRaisesRegex(ValueError, "frame count"):
                compare_evidence(a, b, ea, eb)

    def test_stop_receipt_and_extra_images_are_required_checks(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            Image.new("RGB", (3, 2)).save(a / "snap" / "extra.png")
            with self.assertRaisesRegex(ValueError, "manifest"):
                session_evidence(a, 1, 0)
            (a / "launch.log").write_text("")
            with self.assertRaisesRegex(ValueError, "receipt"):
                session_evidence(a, 1, 0)

    def test_repeated_emulated_time_is_not_an_emulated_frame(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            p = a / "frames.csv"
            p.write_text(p.read_text().replace("0.03333333333333333", "0.016666666666666666"))
            with self.assertRaisesRegex(ValueError, "strictly increasing"):
                read_trace(p)

    def test_requested_gl_capture_cannot_pass_without_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            with self.assertRaises(OSError):
                session_evidence(a, 1, 0, require_gl=True)
            (a / "gl-snap").mkdir()
            (a / "gl-snap" / "captures.csv").write_text("file,dropped_messages\n")
            with self.assertRaisesRegex(ValueError, "empty"):
                session_evidence(a, 1, 0, require_gl=True)
