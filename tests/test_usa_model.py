import copy
import csv
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from scenery_c31 import F
from usa_model import project, quads
from verify_usa_model import check, FIELDS


def sample():
    f = lambda n: F.integer(n).store()
    obj = [0]*32
    obj[14], obj[16] = 0x1400, 0x200
    return dict(call=1, frame=3500, end_frame=3500, object=0x10000, model=0xc00000,
                compact=0, fast=1, palette_kind=1, vertices=4, polygons=1,
                object_words=obj, palette_words=[0x200],
                matrix=[f(i % 4 == 0) for i in range(9)], camera_space=[f(0), f(0), f(1024)],
                model_words=[20, 3, 0xfff6fff6, 0, 0xfff6000a, 0, 0x000a000a, 0, 0x000afff6, 0,
                             0x200100, 0x03020100, 0x00100000, 0x10001010, 0x20],
                projected=[f(v) for v in (246, 189, 1024, 266, 189, 1024, 266, 210, 1024, 246, 210, 1024)])


class UsaModelTests(unittest.TestCase):
    def fixture(self, root):
        r = sample()
        recips = [F.integer(1).store()]*5080
        # Keep full C31 fractional screen words as captured data.
        r['projected'] = project(r, recips)
        (root/'usa-model-transform.jsonl').write_text(json.dumps(r)+'\n')
        (root/'usa-model-reciprocals.bin').write_bytes(struct.pack('<5080I', *recips))
        with (root/'usa-model-draws.csv').open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(('frame', 'call', 'object', 'model', *FIELDS))
            writer.writerow((3500, 1, r['object'], r['model'],
                             0x100, 0x200, 246, 189, 266, 189, 266, 210, 246, 210, 0, 16, 4112, 4096, 0x20, 0))
        return r

    def test_interleaved_texture_and_both_palette_paths(self):
        r = sample()
        buffer = project(r, [F.integer(1).store()]*5080)
        expected = [[0x100, 0x200, 246, 189, 266, 189, 266, 210, 246, 210, 0, 16, 4112, 4096, 0x20, 0]]
        self.assertEqual(quads(r, buffer), expected)
        r['palette_kind'] = 0
        r['object_words'][14] &= ~0x400
        r['palette_words'] = [0x21234]
        self.assertEqual(quads(r, buffer), expected)
        r['compact'] = 1
        r['matrix'] = [F.integer(n).store() for n in (1, 0, 0, 1)]
        self.assertEqual(project(r, [F.integer(1).store()]*5080), buffer)

    def test_invalid_counts_indices_materials_and_origin_fail(self):
        original = sample()
        for field, value in [('vertices', 3), ('palette_words', []), ('matrix', []), ('projected', [])]:
            r = dict(original, **{field: value})
            with self.assertRaises(ValueError):
                project(r, [0]*5080)
        r = copy.deepcopy(original)
        r['model_words'][11] = 0x04020100
        with self.assertRaisesRegex(ValueError, 'outside'):
            project(r, [0]*5080)
        r = dict(original, schema=1)
        with self.assertRaisesRegex(ValueError, 'origin'):
            project(r, [0]*5080)

    def test_evidence_requires_nonempty_owned_ordered_dma(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            self.assertTrue(check(root)['passed'])
            path = root/'usa-model-draws.csv'
            original = path.read_text()
            path.write_text(original.replace('3500,1,', '3500,2,'))
            with self.assertRaisesRegex(ValueError, 'orphan'):
                check(root)
            path.write_text(original.replace(',266,189,', ',267,189,'))
            self.assertFalse(check(root)['passed'])
            (root/'usa-model-transform.jsonl').write_text('')
            with self.assertRaisesRegex(ValueError, 'empty'):
                check(root)

    def test_incomplete_receipt_and_duplicate_records_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            r = self.fixture(root)
            path = root/'usa-model-transform.jsonl'
            path.write_text((json.dumps(r)+'\n')*2)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                check(root)
            path.write_text(json.dumps(dict(r, schema=1, origin_y=F.integer(200).store()))+'\n')
            with self.assertRaisesRegex(ValueError, 'receipt'):
                check(root)
            (root/'usa-model-capture.json').write_text(json.dumps(dict(complete=False)))
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                check(root)

    def test_cli_failure_returns_nonzero_and_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1]/'harness/verify_usa_model.py'),
                                   str(root), '--report', str(root/'report.json')], capture_output=True)
            self.assertEqual(proc.returncode, 1)
            self.assertFalse(json.loads((root/'report.json').read_text())['passed'])

    def test_negative_cached_depth_is_a_signed_guest_word(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            r = self.fixture(root)
            f = lambda n: F.integer(n).store()
            r.update(schema=2, origin_y=f(200), camera=[f(0)]*3, view=r['matrix'],
                     billboard_full=r['matrix'], billboard_compact=[f(n) for n in (1, 0, 0, 1)],
                     dispatch_mode=0x3c4, dispatch_enable=0)
            r['camera_space'][2] = f(-16)
            r['object_words'][1:4] = [f(0), f(0), f(-16)]
            r['object_words'][4:13] = r['matrix']
            r['object_words'][13], r['object_words'][28] = r['model'], (-16) & 0xffffffff
            r['projected'] = project(r, [f(1)]*5080)
            (root/'usa-model-transform.jsonl').write_text(json.dumps(r)+'\n')
            (root/'usa-model-capture.json').write_text(json.dumps(dict(complete=True, projected=1, draws=1, first=3500, last=3500)))
            self.assertTrue(check(root)['passed'])


if __name__ == '__main__':
    unittest.main()
