from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from analyze_vunit_margin_gap import projected_box, intersects


class ProjectedBoundsTests(unittest.TestCase):
    def test_signed_projected_coordinates_and_inclusive_bounds(self):
        quad=[0]*16
        quad[2:10]=[65521,156,65520,141,16,141,17,155]
        self.assertEqual(projected_box(quad),(-16,141,17,156))
        self.assertTrue(intersects(projected_box(quad),(15,155,15,155)))
        self.assertFalse(intersects(projected_box(quad),(15,159,15,162)))
        with self.assertRaisesRegex(ValueError,'invalid host quad'):
            projected_box(quad[:-1])


if __name__ == '__main__':
    unittest.main()
