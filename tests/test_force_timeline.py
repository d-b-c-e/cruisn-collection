from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from force_timeline import event_frames
import analyze_ffb


class ForceTimelineTests(unittest.TestCase):
    def test_uses_emulated_time_even_when_host_clock_stalls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frames.csv"
            path.write_text("frame,emulated_seconds,host_seconds\n1,0.017,30\n2,0.034,50\n3,0.051,50.017\n")
            events = event_frames([17, 18, 34, 35, 52], path)
            self.assertEqual([e["first_completed_frame"] for e in events], [1, 2, 2, 3, None])
            path.write_text("frame,emulated_seconds\n1,0.017\n3,0.051\n")
            with self.assertRaisesRegex(ValueError, "contiguous"):
                event_frames([17], path)

    def test_host_trace_cannot_be_scored_as_emulated_contacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.csv"
            path.write_text("ms,output,value\n100,wheel,126\n")
            for option in ("--labels", "--frames"):
                with self.subTest(option=option), mock.patch("sys.stderr"), self.assertRaises(SystemExit) as err:
                    analyze_ffb.main([str(path), option, str(Path(tmp) / "unused.json")])
                self.assertEqual(err.exception.code, 2)
