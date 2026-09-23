import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from analyze_lifetime_stutter import analyze


class LifetimeAdjacency(unittest.TestCase):
    def test_next_callback_is_distinct_from_native_event_frame(self):
        frames = {f: t for f, t in enumerate((0, .01, .02, .03, .063, .078, .09), start=1)}
        phases = {"lifetime_install": {4: dict(scene=2, callbacks=3, microseconds=100)},
                  "lifetime_complete": {4: dict(scene=2, callbacks=3, microseconds=16000)}}
        result = analyze(frames, phases, 3, 6, control_frames=frames)
        self.assertEqual(result["event_buckets"], 1)
        self.assertEqual(result["next_callback_over_threshold"], 1)
        self.assertEqual(result["other_callback_over_threshold"], 0)
        self.assertEqual(result["details"][0]["native_frame"], 4)
        self.assertAlmostEqual(result["details"][0]["next_callback_interval_ms"], 33)
        self.assertEqual(result["control_same_ordinal"]["next_callback_over_threshold"], 1)

    def test_missing_bounded_next_interval_rejected(self):
        frames = {1: 0, 2: .01, 3: .02, 4: .03}
        phases = {"lifetime_install": {4: dict(scene=2, callbacks=1, microseconds=1)},
                  "lifetime_complete": {4: dict(scene=2, callbacks=1, microseconds=2)}}
        with self.assertRaisesRegex(ValueError, "no complete lifetime"):
            analyze(frames, phases, 2, 3)


if __name__ == "__main__":
    unittest.main()
