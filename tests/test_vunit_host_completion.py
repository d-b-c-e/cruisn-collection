from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from vunit_host_completion import select, require_preparation_frame


class HostCompletionTests(unittest.TestCase):
    def fixture(self):
        rows = [dict(frame=f, page=p, quads=n, quads_hash=f'{f:016x}')
                for f, p, n in [(10, 516, 3), (12, 513, 4), (14, 516, 5), (16, 513, 6)]]
        return rows, dict(frame=16, visible_page=1, auxiliary_quads=7)

    def test_frame_number_and_latest_preparation_are_not_displayed_scene(self):
        rows, receipt = self.fixture()
        result = select(rows, receipt)
        self.assertEqual(result['visible']['frame'], 10)
        self.assertEqual(result['pages'][0]['frame'], 12)
        self.assertEqual(result['excluded_unconsumed_quads'], 11)
        self.assertEqual(require_preparation_frame(result, 10)['consumed_quads'], 3)
        with self.assertRaisesRegex(ValueError, 'does not match'):
            require_preparation_frame(result, 16)

    def test_partial_scene_cannot_qualify_whole_saved_preparation(self):
        rows, receipt = self.fixture()
        result = select(rows, dict(receipt, auxiliary_quads=9))
        self.assertEqual(result['visible']['consumed_quads'], 2)
        self.assertFalse(result['visible']['complete'])
        with self.assertRaises(ValueError):
            require_preparation_frame(result, 14)

    def test_zero_submission_has_no_visible_host_scene(self):
        rows, receipt = self.fixture()
        rows.insert(2, dict(frame=13, page=516, quads=0, quads_hash='0'*16))
        self.assertEqual(select(rows, receipt)['visible']['frame'], 10)
        result = select(rows, dict(receipt, auxiliary_quads=0))
        self.assertIsNone(result['visible'])
        with self.assertRaises(ValueError):
            require_preparation_frame(result, 10)

    def test_incomplete_journal_future_consumption_and_bad_order_reject(self):
        rows, receipt = self.fixture()
        for change in (dict(auxiliary_quads=19), dict(frame=11),
                       dict(auxiliary_quads=True), dict(visible_page=2)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                select(rows, dict(receipt, **change))
        rows[-1]['frame'] = 9
        with self.assertRaises(ValueError):
            select(rows, receipt)


if __name__ == '__main__':
    unittest.main()
