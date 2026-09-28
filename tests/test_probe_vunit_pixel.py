import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from probe_vunit_pixel import screen_to_indexed


class ScreenPointMappingTests(unittest.TestCase):
    def test_calibrated_1440p_center_samples(self):
        self.assertEqual(screen_to_indexed(2100, 600), (2309, 892))
        self.assertEqual(screen_to_indexed(170, 575), (116, 924))
        self.assertEqual(screen_to_indexed(120, 545), (58, 962))

    def test_rejects_outside_viewport_or_glass(self):
        for point in ((0, 600), (2543, 600), (120, -1), (120, 1353)):
            with self.subTest(point=point), self.assertRaises(ValueError):
                screen_to_indexed(*point)


if __name__ == '__main__':
    unittest.main()
