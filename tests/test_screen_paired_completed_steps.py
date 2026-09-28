import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from screen_paired_completed_steps import step_counts


class CompletedStepTests(unittest.TestCase):
    def test_separates_shared_and_candidate_only_motion(self):
        base = np.zeros((1, 3, 3), dtype='u1')
        control_after = base.copy()
        control_after[0, 0, 0] = 1
        trial_after = control_after.copy()
        trial_after[0, 1, 0] = 1
        result = step_counts(base, control_after, base, trial_after)
        self.assertEqual(result['control_changed_pixels'], 1)
        self.assertEqual(result['trial_changed_pixels'], 2)
        self.assertEqual(result['both_changed_locations'], 1)
        self.assertEqual(result['trial_only_changed_locations'], 1)
        self.assertEqual(result['paired_difference_gained_locations'], 1)
        self.assertEqual(result['paired_difference_lost_locations'], 0)

    def test_paired_footprint_can_handover_and_move(self):
        base = np.zeros((1, 2, 3), dtype='u1')
        trial_before = base.copy()
        trial_before[0, 0, 0] = 1
        trial_after = base.copy()
        trial_after[0, 1, 0] = 1
        result = step_counts(base, base, trial_before, trial_after)
        self.assertEqual(result['paired_difference_gained_locations'], 1)
        self.assertEqual(result['paired_difference_lost_locations'], 1)
        self.assertEqual(result['paired_difference_shared_locations'], 0)

    def test_rejects_mismatched_dimensions(self):
        image = np.zeros((1, 2, 3), dtype='u1')
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            step_counts(image, image, image, image[:, :1])


if __name__ == '__main__':
    unittest.main()
