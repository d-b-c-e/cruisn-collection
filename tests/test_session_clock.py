import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from session_clock import FrameTail, clock_text


class SessionClockTests(unittest.TestCase):
    def test_partial_rows_pause_and_late_file_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frames.csv"
            tail = FrameTail(path)
            self.assertIsNone(tail.poll())
            path.write_bytes(b"frame,emulated_seconds,host_seconds\n1,0.02,0.5\n2,0.0")
            self.assertEqual(tail.poll(), (1, .02))
            self.assertEqual(tail.poll(), (1, .02))  # paused: no wall-clock interpolation
            with path.open("ab") as stream:
                stream.write(b"4,0.6\n3,nan,0.7\n3,0.06,0.8\n")
            self.assertEqual(tail.poll(), (3, .06))
            self.assertEqual(clock_text(tail.latest), ("000.06 s", "Frame 3  |  emulated time"))
            # A restarted stream must not retain an old time or partial row.
            path.write_bytes(b"1,0.01,0.1\n")
            self.assertEqual(tail.poll(), (1, .01))

    def test_record_and_replay_use_emulated_time_despite_different_host_times(self):
        with tempfile.TemporaryDirectory() as tmp:
            observed = []
            for name, host in (("record", 103.0), ("replay", 80.0)):
                path = Path(tmp) / name
                path.write_text(f"frame,emulated_seconds,host_seconds\n6000,103.5796,{host}\n")
                observed.append(clock_text(FrameTail(path).poll()))
            self.assertEqual(observed[0], observed[1])
            self.assertEqual(observed[0][0], "103.58 s")
