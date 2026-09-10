import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from capture_writer import verify

RECEIPT = ('MIDZ_CAPTURE_WRITER_BEGIN\n'
           'MIDZ_CAPTURE_WRITER submitted=2 written=2 failed=0 rejected=0 peak_bytes=4096 '
           'write_total_us=1000 write_max_us=750 drain_us=100\n')


class CaptureWriterTests(unittest.TestCase):
    def test_old_builds_and_both_new_renderers(self):
        self.assertIsNone(verify('old emulator log'))
        for prefix in ('MIDZ', 'MIDV'):
            result = verify(RECEIPT.replace('MIDZ', prefix))
            self.assertEqual(result['renderer'], prefix)
            self.assertEqual(result['written'], 2)

    def test_started_writer_must_finish_all_requests(self):
        for text in (RECEIPT.splitlines()[0], RECEIPT.splitlines()[1], RECEIPT + RECEIPT,
                     RECEIPT.replace('written=2', 'written=1'),
                     RECEIPT.replace('rejected=0', 'rejected=1'),
                     RECEIPT.replace('peak_bytes=4096', 'peak_bytes=536870913'),
                     RECEIPT.replace('write_total_us=1000', 'write_total_us=2000')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                verify(text)

    def test_write_failure_cannot_be_hidden_by_success_counters(self):
        for prefix in ('MIDZ', 'MIDV'):
            for failure in ('writer failed: index close', 'writer rejected: capture.bmp', 'write failed: capture.bmp'):
                with self.subTest(prefix=prefix, failure=failure), self.assertRaises(ValueError):
                    verify(RECEIPT + prefix + ' screenshot ' + failure)

    def test_pacing_requires_its_own_acknowledgment(self):
        for text in ('', RECEIPT, RECEIPT.rstrip() + ' paced=0 waits=0 wait_us=0\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                verify(text, require_pacing=True)
        result = verify(RECEIPT.rstrip() + ' paced=1 waits=2 wait_us=1000\n', require_pacing=True)
        self.assertEqual(result['waits'], 2)
