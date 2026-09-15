from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from vunit_original_mirror import configure, verify, compare_originals


class OriginalMirrorTests(unittest.TestCase):
    def test_candidate_and_ownership_gates(self):
        args = SimpleNamespace(vunit_original_mirror_frame=100, candidate='candidate.exe')
        settings = dict(MIDV_GL='1', MIDV_FFB='0')
        self.assertEqual(configure(args, 'crusnwld', settings.copy(), 200), dict(frame=100, auxiliary=False))
        for rom, changes in [('crusnusa', {}), ('crusnwld', {'MIDV_FFB':'1'}),
                             ('crusnwld', {'MIDV_GL_BATCH_VRAM':'0'}),
                             ('crusnwld', {'MIDV_WORLD_HOST_SCENERY':'2','MIDV_WORLD_HOST_LAYER':'1'})]:
            with self.subTest(rom=rom, changes=changes), self.assertRaises(ValueError):
                configure(args, rom, dict(settings, **changes), 200)
        for changes in [dict(candidate=None), dict(headless=True), dict(native_renderer=True),
                        dict(vunit_original_mirror_frame=199)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args) | changes)), 'crusnwld', settings.copy(), 200)
        host = dict(settings, MIDV_WORLD_HOST_SCENERY='2', MIDV_WORLD_HOST_LAYER='3')
        self.assertTrue(configure(args, 'crusnwld24', host, 200)['auxiliary'])

    def test_explicit_selection_and_missing_receipt(self):
        args = SimpleNamespace(vunit_original_mirror_frame=None)
        self.assertIsNone(configure(args, 'crusnwld', {}, 200))
        with self.assertRaises(ValueError):
            configure(args, 'crusnwld', {'MIDV_GL_ORIGINAL_MIRROR':'1'}, 200)
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(verify(None, root))
            with self.assertRaises(ValueError):
                verify(dict(frame=100, auxiliary=False), root)

    def test_both_pages_exact_and_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            row = dict(frame=100, width=512, height=256, visible_page=1,
                       ordinary_quads=20, auxiliary_quads=0, cpu_blits=3, original_resets=2)
            (root/'vunit-mirror.json').write_text(json.dumps(row))
            for page in range(2):
                for plane in range(4):
                    count = 512*256*(1 if plane & 1 else 2)
                    (root/f'vunit-mirror-100-page{page}-plane{plane}.bin').write_bytes(bytes([page])*count)
            trial = dict(frame=100, auxiliary=False)
            result = verify(trial, root)
            self.assertTrue(result['passed'])
            self.assertTrue(compare_originals(result, result)['passed'])
            with self.assertRaisesRegex(ValueError, 'sequence differs'):
                compare_originals(result, dict(result, original_resets=3))
            changed = dict(result, sha256=dict(result['sha256']))
            changed['sha256']['vunit-mirror-100-page1-plane3.bin'] = 'wrong'
            with self.assertRaisesRegex(ValueError, 'pixels changed'):
                compare_originals(result, changed)
            with self.assertRaises(ValueError):
                verify(None, root)
            path = root/'vunit-mirror-100-page1-plane2.bin'
            with path.open('r+b') as stream:
                stream.write(b'\xff')
            with self.assertRaisesRegex(ValueError, 'differs'):
                verify(trial, root)
            path.write_bytes(b'')
            with self.assertRaisesRegex(ValueError, 'wrong-size'):
                verify(trial, root)


if __name__ == '__main__':
    unittest.main()
