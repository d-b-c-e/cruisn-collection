from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from analyze_vunit_margin_gap import projected_box, intersects, gap_distance, native_box, original_evidence


class ProjectedBoundsTests(unittest.TestCase):
    def test_signed_projected_coordinates_and_inclusive_bounds(self):
        quad=[0]*16
        quad[2:10]=[65521,156,65520,141,16,141,17,155]
        self.assertEqual(projected_box(quad),(-16,141,17,156))
        self.assertTrue(intersects(projected_box(quad),(15,155,15,155)))
        self.assertFalse(intersects(projected_box(quad),(15,159,15,162)))
        with self.assertRaisesRegex(ValueError,'invalid host quad'):
            projected_box(quad[:-1])

    def test_fine_sample_uses_widescreen_margin_and_bottom_up_y(self):
        self.assertEqual(native_box((60,956,60,964),2736,1600,4,86,400),(-71,158,-71,161))
        self.assertFalse(intersects((-109,122,-69,156),(-71,158,-71,161)))
        self.assertEqual(gap_distance((-109,122,-69,156),(-71,158,-71,161)), 2)
        self.assertEqual(gap_distance((-117,163,-3,176),(-71,158,-71,161)), 2)
        self.assertEqual(gap_distance((-71,158,-71,161),(-71,158,-71,161)), 0)
        with self.assertRaisesRegex(ValueError, 'invalid projected rectangle'):
            gap_distance((0, 0, -1, 0), (0, 0, 1, 1))
        with self.assertRaisesRegex(ValueError,'unqualified fine/native'):
            native_box((60,956,60,964),2736,1600,4,0,400)

    def test_original_command_join_rejects_failed_or_unrelated_run(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            (case/'report.json').write_text(json.dumps({'passed': False, 'case': 'same'}),
                                            encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'does not match'):
                original_evidence(case, case, {'case': 'same'}, {}, {}, (0,0,0,0))
            (case/'report.json').write_text(json.dumps({'passed': True, 'case': 'other'}),
                                            encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'does not match'):
                original_evidence(case, case, {'case': 'same'}, {}, {}, (0,0,0,0))


if __name__ == '__main__':
    unittest.main()
