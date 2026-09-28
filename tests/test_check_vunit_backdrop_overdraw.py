import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from check_vunit_backdrop_overdraw import check_attribution


class BackdropOverdrawTests(unittest.TestCase):
    def setUp(self):
        self.report = {'passed': True, 'changed_prior_game_pixels': 7,
                       'changed_prior_game_dma_attribution': [
                           {'original_dma_ordinal': 3, 'changed_pixels': 5},
                           {'original_dma_ordinal': 6, 'changed_pixels': 2}]}
        self.groups = [{'ordinals': [0, 1, 2, 3, 4]},
                       {'ordinals': [5, 6, 7, 8, 9]}]

    def test_two_distinct_backdrop_bands_are_admitted(self):
        result = check_attribution(self.report, self.groups)
        self.assertEqual(result['structurally_backdrop_pixels'], 7)
        self.assertEqual(result['unclassified_game_pixels'], 0)

    def test_foreground_ordinal_is_flagged(self):
        self.report['changed_prior_game_dma_attribution'][1]['original_dma_ordinal'] = 12
        result = check_attribution(self.report, self.groups)
        self.assertEqual(result['unclassified_game_pixels'], 2)
        self.assertEqual(result['unclassified_dma'][0]['original_dma_ordinal'], 12)

    def test_incomplete_attribution_is_rejected(self):
        self.report['changed_prior_game_pixels'] = 8
        with self.assertRaisesRegex(ValueError, 'incomplete original DMA'):
            check_attribution(self.report, self.groups)

    def test_failed_source_report_is_rejected(self):
        self.report['passed'] = False
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            check_attribution(self.report, self.groups)


if __name__ == '__main__':
    unittest.main()
