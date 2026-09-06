from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from compare_scenery import compare


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
