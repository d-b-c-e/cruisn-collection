import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from screen_vunit_panorama_strips import candidate, strips


def quad(left, bottom, *, rotated=False):
    right, top = left + 256, bottom - 216
    points = ([(left, bottom), (left, top), (right, top), (right, bottom)]
              if rotated else
              [(left, top), (right, top), (right, bottom), (left, bottom)])
    words = [0x100, 0x4600] + [v & 0xffff for point in points for v in point]
    return words + [0, 0, 0, 0, 0x25f9, 0]


class PanoramaStripTests(unittest.TestCase):
    def test_two_valid_vertex_orders_form_same_strip(self):
        for rotated in (False, True):
            with self.subTest(rotated=rotated):
                group = strips([quad(-280 + 256 * i, 400, rotated=rotated)
                                for i in range(3)])
                self.assertEqual(len(group), 1)
                self.assertEqual(group[0]['ordinals'], [0, 1, 2])
                self.assertEqual(group[0]['extent'], [-280, 184, 488, 400])

    def test_diagonal_crossing_is_not_a_backdrop_rectangle(self):
        malformed = quad(-280, 400, rotated=True)
        # Exchange top-left and top-right: one vertex order now crosses.
        malformed[4:6], malformed[6:8] = malformed[6:8], malformed[4:6]
        self.assertIsNone(candidate(0, malformed))


if __name__ == '__main__':
    unittest.main()
