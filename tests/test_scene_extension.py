from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from verify_scene_extension import compare_quads, added_quad_coverage


class ExtensionTests(unittest.TestCase):
    def test_added_coverage_attributes_only_new_primitive_on_correct_page(self):
        q = np.zeros(16, np.uint16)
        q[2:10] = [10, 10, 20, 10, 20, 20, 10, 20]
        edge = q.copy()
        edge[2:10] = np.array([-3, 30, 2, 30, 2, 35, -3, 35], np.int16).view(np.uint16)
        mask = added_quad_coverage(np.array([q]), np.array([q, edge]), 4, 511, 399, 512*512*2)
        self.assertFalse(mask[:512*512].any())
        page = mask[512*512:].reshape(512,512)
        self.assertTrue(page[32, 1])
        self.assertFalse(page[32, 4])
        self.assertFalse(page[15, 15])
        duplicate = added_quad_coverage(np.array([q]), np.array([q, q]), 0, 511, 399, 512*512*2)
        self.assertTrue(duplicate[15*512+15])

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
