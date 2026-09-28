import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from screen_vunit_prior_host_overlap import added_rows


def row(value):
    return dict(words=(value,) * 16, object=value, model=value, depth=value)


class PriorHostOrderTests(unittest.TestCase):
    def test_added_packets_preserve_original_order(self):
        original = [row(1), row(2), row(3)]
        trial = [row(1), row(4), row(2), row(5), row(3)]
        self.assertEqual(added_rows(original, trial), [row(4), row(5)])

    def test_changed_original_packet_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ordered trial subsequence'):
            added_rows([row(1), row(2)], [row(1), row(3)])


if __name__ == '__main__':
    unittest.main()
