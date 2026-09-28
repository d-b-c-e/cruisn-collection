import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from screen_vunit_margin_overdraw import source_lifecycle


class SourceLifecycleTests(unittest.TestCase):
    def test_owned_worker_receipt(self):
        basis, capture_only = source_lifecycle(
            {'vunit_runtime': {'result': {'completion': 'owned-worker-stop'}}}, {})
        self.assertEqual(basis, 'owned-worker-stop receipt')
        self.assertFalse(capture_only)

    def test_capture_mode_requires_zero_exit_and_hashed_dma(self):
        report = {'capture': {'sha256': {'quads.bin': 'a' * 64}}}
        basis, capture_only = source_lifecycle(report, {'returncode': 0})
        self.assertIn('no vunit_runtime', basis)
        self.assertTrue(capture_only)
        for invalid_report, invocation in (
                ({}, {'returncode': 0}),
                (report, {'returncode': 1}),
                ({'capture': {'sha256': {}}}, {'returncode': 0})):
            with self.subTest(invalid_report=invalid_report, invocation=invocation):
                with self.assertRaisesRegex(ValueError, 'source lacks'):
                    source_lifecycle(invalid_report, invocation)


if __name__ == '__main__':
    unittest.main()
