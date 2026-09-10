import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_fence import verify


class ExoticaFence(unittest.TestCase):
    def test_disabled_or_incomplete_fences_cannot_pass(self):
        self.assertIsNone(verify('unused', [], '', False))
        with self.assertRaisesRegex(ValueError, 'disabled'):
            verify('unused', [], 'MIDZ_HOST_FENCE=1\n', False)
        with self.assertRaisesRegex(ValueError, 'acknowledgment'):
            verify('unused', [], '', True)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            verify('unused', [{}], 'MIDZ_HOST_FENCE=1\nMIDZ_HOST_FENCE_RESULT complete=1 requested=1 completed=0 immediate=0\n', True)

    def test_exact_wrapped_boundary_and_immediate_completion(self):
        scene = dict(scene=10, scene_frame=5000, scene_time='1.0', device_time='1.001')
        row = dict(scene=10, scene_frame=5000, end_frame=5000, end_time='1.0015',
                   ready_frame=5001, ready_time='1.002', consumer=0x31fff, target=0x30001,
                   words=2, immediate=0, guest_cycles=0, page=0)
        text = 'MIDZ_HOST_FENCE=1\nMIDZ_HOST_FENCE_RESULT complete=1 requested=1 completed=1 immediate=0\n'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'exotica-host-fences.csv'

            def check(value, message=text):
                with path.open('w', encoding='utf-8', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(row));writer.writeheader();writer.writerow(value)
                return verify(temporary, [scene], message, True)

            self.assertEqual(check(row)['waited_words'], 2)
            for change in (dict(words=1), dict(target=0x32000), dict(ready_time='nan'),
                           dict(ready_frame=5002), dict(guest_cycles=1), dict(scene=11), dict(immediate=1)):
                with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'mismatch'):
                    check(dict(row, **change))
            immediate = dict(row, target=row['consumer'], words=0, immediate=1,
                             ready_frame=5000, ready_time=row['end_time'])
            self.assertEqual(check(immediate, text.replace('immediate=0', 'immediate=1'))['immediate'], 1)


if __name__ == '__main__':
    unittest.main()
