from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from compare_distance_fade import same_invocation


class FadeComparisonTests(unittest.TestCase):
    def test_only_run_relocation_and_fade_toggle_are_allowed(self):
        roots = [Path('left/run').resolve(), Path('right/run').resolve()]
        runs = [dict(returncode=0, error=None, executable_sha256='fixed',
                     command=['candidate.exe', str(root/'session.lua')],
                     environment=dict(MIDV_FFB='0', MIDV_GL='1',
                                      SNAP_SESSION_LOG=str(root/'frames.csv'))) for root in roots]
        runs[1]['environment']['MIDV_WORLD_HOST_DISTANCE_FADE'] = '1'
        self.assertEqual(same_invocation(*runs, *roots), 'fixed')
        for field, value in [('executable_sha256', 'changed'), ('returncode', 1), ('error', 'timeout')]:
            changed = deepcopy(runs)
            changed[1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                same_invocation(*changed, *roots)
        for key, value in [('MIDV_FFB', '1'), ('MIDV_GL', '0'), ('MIDV_WORLD_HOST_DISTANCE_FADE', '0')]:
            changed = deepcopy(runs)
            changed[1]['environment'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                same_invocation(*changed, *roots)


if __name__ == '__main__':
    unittest.main()
