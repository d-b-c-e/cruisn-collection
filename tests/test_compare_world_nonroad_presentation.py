import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from compare_world_nonroad_course import require_presentation


class WorldNonroadPresentationTests(unittest.TestCase):
    def test_rejects_matched_omission_of_release_crt(self):
        pair = [{'environment': {'MIDV_GL_SCALE': '4'}}] * 2
        with self.assertRaisesRegex(ValueError, 'MIDV_GL_CRT'):
            require_presentation(pair, {'MIDV_GL_CRT': '1'})

    def test_rejects_one_arm_with_different_height(self):
        pair = [{'environment': {'MIDV_GL_HEIGHT': '400'}},
                {'environment': {'MIDV_GL_HEIGHT': '401'}}]
        with self.assertRaisesRegex(ValueError, 'MIDV_GL_HEIGHT'):
            require_presentation(pair, {'MIDV_GL_HEIGHT': '400'})

    def test_accepts_explicit_matched_default_view(self):
        expected = {'MIDV_GL_CRT': '1', 'MIDV_GL_SCALE': '4',
                    'MIDV_GL_HEIGHT': '400'}
        pair = [{'environment': dict(expected)} for _ in range(2)]
        self.assertEqual(require_presentation(pair, expected), expected)


if __name__ == '__main__':
    unittest.main()
