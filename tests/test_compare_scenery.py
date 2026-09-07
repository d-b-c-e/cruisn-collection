from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from compare_scenery import compare, compare_scenes


class SceneryComparisonTests(unittest.TestCase):
    def test_duplicates_order_and_unknown_draws_are_not_silently_lost(self):
        def row(model, x):
            return (0x289, 4, 123, model, int(bool(model)), 0, 0,
                    x, 0, x+1, 0, x+1, 1, x, 1, 0, 0, 0, 0, 0, 0)
        a, b, new, unknown = row(1, 1), row(2, 3), row(3, 5), row(0, 7)
        control = {1: [a, b, a]}
        self.assertTrue(compare(control, {1: [new, a, b, a]}, {3})['passed'])
        giant=list(new); giant[9]=30000
        self.assertFalse(compare(control,{1:[tuple(giant),a,b,a]},{3},32)['passed'])
        for bad in ([a, b], [a, a, b], [a, b, a, unknown], [a, b, a, new]):
            self.assertFalse(compare(control, {1: bad}, set())['passed'])
        with self.assertRaisesRegex(ValueError, 'frame sets'):
            compare(control, {2: [a, b, a]}, set())

    def test_scene_comparison_retains_frame_spill_without_discarding_geometry(self):
        def row(page, model):
            return (0x289, page, 123, model, int(bool(model)), 0, 0,
                    1, 0, 2, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0)
        edge, a, hud, end = row(1, 1), row(4, 2), row(4, 0), row(1, 3)
        control = {1: [edge], 2: [a, hud], 3: [end]}
        delayed = {1: [edge], 2: [a], 3: [hud, end]}
        self.assertFalse(compare(control, delayed, set())['passed'])
        result = compare_scenes(control, delayed, set())
        self.assertTrue(result['passed'])
        self.assertEqual(result['scenes'][0]['control_frames'], [2, 2])
        self.assertEqual(result['scenes'][0]['candidate_frames'], [2, 3])
        self.assertFalse(compare_scenes(control, {1: [edge], 2: [a], 3: [end]}, set())['passed'])
        self.assertFalse(compare_scenes(control, {1: [edge], 2: [hud, a], 3: [end]}, set())['passed'])
        with self.assertRaisesRegex(ValueError, 'sequences differ'):
            compare_scenes(control, {1: [edge], 2: [a, hud, end, a, end]}, set())
        with self.assertRaisesRegex(ValueError, 'completed page-control'):
            compare_scenes({1: [a]}, {1: [a]}, set())

    def test_disjoint_reordering_is_explained_but_still_fails_order_gate(self):
        def row(x):
            return (0x289, 4, 123, 1, 1, 0, 0,
                    x, 0, x+1, 0, x+1, 1, x, 1, 0, 0, 0, 0, 0, 0)
        a, b = row(1), row(40)
        for nearby, overlaps in [(b, 0), (row(3), 1)]:
            result = compare({1: [a, nearby]}, {1: [nearby, a]}, set(), order_details=True)
            self.assertFalse(result['passed'])
            detail = result['frames'][0]['reordering_bounds']
            self.assertEqual(detail['inverted_pairs'], 1)
            self.assertEqual(detail['possibly_overlapping_pairs'], overlaps)
