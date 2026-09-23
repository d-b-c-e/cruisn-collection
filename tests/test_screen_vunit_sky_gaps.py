import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from screen_vunit_sky_gaps import candidates, components


class SkyGapScreenTests(unittest.TestCase):
    def test_only_bracketed_short_sky_run_is_candidate(self):
        sky = np.zeros((12, 4), dtype=bool)
        tags = np.ones((12, 4), dtype='u1')
        sky[3:7, 0] = True
        tags[7, 0] = 5
        sky[2:8, 1] = True
        tags[8, 1] = 5
        sky[3:7, 3] = True  # no auxiliary above
        tags[7, 3] = 1
        found = candidates(sky, tags, 2, 3, 4)
        self.assertEqual(int(found.sum()), 4)
        self.assertEqual(components(found), [dict(pixels=4, box=[0, 3, 0, 6])])
        with self.assertRaisesRegex(ValueError, 'geometry'):
            candidates(sky, tags, 3, 2, 4)

    def test_right_margin_and_missing_ground_are_distinct(self):
        sky = np.zeros((10, 5), dtype=bool)
        tags = np.ones((10, 5), dtype='u1')
        sky[2:5, 4] = True
        tags[5, 4] = 5
        sky[2:5, 0] = True
        tags[1, 0] = 0  # no original ground below
        tags[5, 0] = 5
        found = candidates(sky, tags, 1, 4, 4)
        self.assertEqual(components(found), [dict(pixels=3, box=[4, 2, 4, 4])])


if __name__ == '__main__':
    unittest.main()
