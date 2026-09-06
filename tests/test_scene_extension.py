from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from verify_scene_extension import compare_quads


class ExtensionTests(unittest.TestCase):
    def test_multiplicity_and_center_intrusions_are_not_hidden(self):
        q = np.zeros(16, np.uint16)
        q[2:10:2] = [10, 20, 20, 10]
        left = q.copy(); left[2:10:2] = np.array([-30, -5, -5, -30], np.int16).view(np.uint16)
        r = compare_quads(np.array([q, q]), np.array([q, left]))
        self.assertEqual(r["removed_or_changed_quads"], 1)
        self.assertEqual(r["added_quads_intersecting_native_x"], 0)
        cross = left.copy(); cross[4] = 1
        r = compare_quads(np.array([q]), np.array([q, cross]))
        self.assertEqual(r["removed_or_changed_quads"], 0)
        self.assertEqual(r["added_quads_intersecting_native_x"], 1)
        r = compare_quads(np.array([q, left]), np.array([left, q]))
        self.assertEqual(r["removed_or_changed_quads"], 0)
        self.assertFalse(r["original_draw_order_preserved"])
