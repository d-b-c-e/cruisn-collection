from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'harness'))
from verify_exotica_reset_seed import shader_sources


class ResetShaderSourceTests(unittest.TestCase):
    def test_shader_bytes_preserved_without_raw_literals(self):
        source = (ROOT / 'native/exotica_reset.h').read_text(encoding='utf-8')
        self.assertNotIn('R"GLSL', source)
        shaders = shader_sources(source)
        self.assertEqual([len(shader) for shader in shaders], [126, 335])

    def test_missing_or_changed_shader_rejected(self):
        source = (ROOT / 'native/exotica_reset.h').read_text(encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'source extent'):
            shader_sources(source.replace('seed_fragment=', 'other_fragment='))
        with self.assertRaisesRegex(ValueError, 'bytes changed'):
            shader_sources(source.replace('vec2 p=vec2', 'vec2 p=vec3'))


if __name__ == '__main__':
    unittest.main()
