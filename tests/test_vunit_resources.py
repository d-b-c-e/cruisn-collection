from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from compare_vunit_resources import SIZES, RECORD, compare, validate


class VunitResourceTests(unittest.TestCase):
    def fixture(self, root, frames=(8, 10, 12)):
        root.mkdir()
        for name, size in SIZES.items():
            with (root/name).open('wb') as f:
                f.truncate(size)
        (root/'meta.txt').write_text('frame 10\npage_control 513\nvisible_page_offset 0x40000\nvisarea 510 400\n')
        (root/'quads.bin').write_bytes(b'MVQ1'+b''.join(RECORD.pack(n, 513, *([0]*16)) for n in frames))

    def test_complete_original_data_and_single_byte_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a', Path(tmp)/'b'
            self.fixture(a); self.fixture(b)
            result = compare(a, b, 10)
            self.assertTrue(result['passed'])
            self.assertEqual(result['reference']['dma_records'], 3)
            with (b/'textureram.bin').open('r+b') as f:
                f.seek(123); f.write(b'\x01')
            self.assertEqual(compare(a, b, 10)['differing_files'], ['textureram.bin'])

    def test_identical_truncated_resources_are_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'capture'; self.fixture(root)
            (root/'paletteram.bin').write_bytes(b'')
            with self.assertRaisesRegex(ValueError, 'resource'):
                compare(root, root, 10)

    def test_metadata_identity_and_shape_fail(self):
        for replacement in ['frame 11', 'page_control 512', 'visarea 512 400', 'frame 10\nframe 10']:
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)/'capture'; self.fixture(root)
                p = root/'meta.txt'; text = p.read_text()
                target = 'page_control 513' if replacement.startswith('page_control') else 'visarea 510 400' if replacement.startswith('visarea') else 'frame 10'
                p.write_text(text.replace(target, replacement))
                with self.assertRaises(ValueError): validate(root, 10)

    def test_dma_header_truncation_order_and_missing_frame_span_fail(self):
        for kind in ['header', 'truncated', 'backwards', 'before', 'after']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)/'capture'
                frames = {'backwards': (8, 12, 10), 'before': (8, 9), 'after': (11, 12)}.get(kind, (8, 10, 12))
                self.fixture(root, frames); p = root/'quads.bin'
                if kind == 'header': p.write_bytes(b'NOPE'+p.read_bytes()[4:])
                if kind == 'truncated': p.write_bytes(p.read_bytes()[:-1])
                with self.assertRaises(ValueError): validate(root, 10)
