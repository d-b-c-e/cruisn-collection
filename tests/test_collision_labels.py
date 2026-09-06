import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from collision_labels import evaluate


class CollisionLabelsTests(unittest.TestCase):
    def test_unreviewed_is_not_a_false_positive_and_duplicates_do_not_inflate_recall(self):
        labels = dict(schema=1, clock="emulated_ms", coverage=[[100, 1000]],
                      events=[dict(kind="car", start_ms=200, end_ms=250),
                              dict(kind="wall", start_ms=600, end_ms=650)])
        r = evaluate([10, 210, 220, 800, 2000], labels)
        self.assertEqual((r["matched_contacts"], r["missed_contacts"], r["unmatched_candidates"], r["unreviewed_candidates"]), (1, 1, 2, 2))
        self.assertEqual(r["recall"], .5)
        labels["events"][1]["end_ms"] = 1100
        with self.assertRaises(ValueError):
            evaluate([], labels)
