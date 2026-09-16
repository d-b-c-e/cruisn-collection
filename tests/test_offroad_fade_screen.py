from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from offroad_fade_screen import envelope_counts, FAR, WIDTH
from scenery_c31 import F


class ScreenTests(unittest.TestCase):
    def objects(self, depths):
        return [dict(quads=[[] for _ in depths],
                     depths=[[F.integer(z).store() for z in row] for row in depths])]

    def test_c31_depth_contract_and_envelope_boundaries(self):
        result = envelope_counts(self.objects([[FAR-WIDTH]*4, [FAR-WIDTH, FAR, FAR, FAR-WIDTH], [FAR]*4]))
        self.assertEqual((result['fully_opaque'], result['partial_envelope'], result['fully_zero']), (1, 1, 1))
        self.assertEqual(result['maximum'], FAR)
        self.assertEqual(envelope_counts([])['quads'], 0)
        self.assertIsNone(envelope_counts([])['maximum'])

    def test_bad_extent_and_wrong_numeric_domain_reject(self):
        for values in ([502]*4, [191040]*4, [-1]*4):
            with self.assertRaises(ValueError):
                envelope_counts(self.objects([values]))
        for words in ([True]*4, [0x1_00000000]*4, [0x47c35000]*4, [0]*3):
            with self.assertRaises(ValueError):
                envelope_counts([dict(quads=[[]], depths=[words])])
        with self.assertRaises(ValueError):
            envelope_counts([dict(quads=[], depths=[[1]*4])])


if __name__ == '__main__':
    unittest.main()
