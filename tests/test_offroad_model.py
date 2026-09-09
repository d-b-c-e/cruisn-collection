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
from offroad_model import project, quads
from verify_offroad_model import check, FIELDS


def sample():
    f = lambda n: F.integer(n).store()
    obj = [0]*22
    obj[18:21] = [0x200, 0x1000, 0xc00000]
    matrix = [f(i in (0, 5, 10)) for i in range(12)]
    matrix[11] = f(1000)
    return dict(schema=1, call=1, frame=2500, object=0x10000, model=0xc00000, lod=0xc00007,
                path=0x1e03, origin_x=f(256), extra_flags=0x400, vertices=4, polygons=1,
                object_words=obj, palette_words=[0x17], matrix=matrix,
                lod_words=[3, 0xc10000, 0, 0, 0xc20000],
                vertex_words=[f(x) for x in (-10, 10, 0, 10, 10, 0, 10, -10, 0, -10, -10, 0)],
                polygon_words=[0x210003, 0x01000200, 0x03000400, 0x30, 0x00030000, 0x00090006],
                projected=[246, 190, 0xdeadbeef, 266, 190, 0, 266, 210, 0xffffffff, 246, 210, 3])


EXPECTED = [0x403, 0x217, 246, 190, 266, 190, 266, 210, 246, 210,
            0x200, 0x100, 0x400, 0x300, 0x1030, 0]


class OffroadModelTests(unittest.TestCase):
    def fixture(self, root):
        r = sample()
        (root/'offroad-model-transform.jsonl').write_text(json.dumps(r)+'\n')
        (root/'offroad-model-reciprocals.bin').write_bytes(struct.pack('<67776I', *[F.integer(1).store()]*67776))
        with (root/'offroad-model-draws.csv').open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(('frame', 'call', 'object', 'model', 'pc', 'page', *FIELDS))
            writer.writerow((2500, 1, r['object'], r['model'], 0x1fb0, 0x201, *EXPECTED))
        (root/'offroad-model-capture.json').write_text(json.dumps(dict(
            complete=True, first=2500, last=2550, started=1, projected=1, draws=1)))
        return r

    def test_ordinary_projection_stride_and_separate_material_words(self):
        r = sample()
        points = project(r, [F.integer(1).store()]*67776)
        self.assertEqual(points, [246, 190, 266, 190, 266, 210, 246, 210])
        self.assertEqual(quads(r, points), [EXPECTED])
        self.assertEqual(quads(r, [256, 200]*4)[0][2:10], [256, 200]*4)
        self.assertEqual(quads(r, [246, 190, 246, 210, 266, 210, 266, 190]), [])

    def test_lod_buffer_and_material_guards(self):
        for field, value in [('vertices', 0), ('palette_words', []), ('matrix', []),
                             ('projected', []), ('lod', 0x980000), ('origin_x', -1)]:
            r = dict(sample(), **{field: value})
            with self.assertRaises(ValueError):
                project(r, [0]*67776)
        for offset in (1, 12):
            r = sample();r['polygon_words'][4] = offset
            with self.assertRaisesRegex(ValueError, 'three-word'):
                project(r, [0]*67776)
        r = sample();r['polygons'] = 2;r['lod_words'][3] = 1
        r['polygon_words'] *= 2;r['palette_words'] += [0x18]
        with self.assertRaisesRegex(ValueError, 'palette binding'):
            project(r, [0]*67776)

    def test_negative_depth_and_branch_specific_reciprocal_limits(self):
        r = sample();recips = [F.integer(1).store()]*67776
        for depth, path in [(-5000, 0x1e3b), (70000, 0x1e60)]:
            r['matrix'][11] = F.integer(depth).store();r['path'] = 0x1e03
            with self.assertRaisesRegex(ValueError, 'outside captured'):
                project(r, recips)
            r['path'] = path
            self.assertEqual(project(r, recips), [246, 190, 266, 190, 266, 210, 246, 210])

    def test_evidence_rejects_incomplete_duplicate_and_unowned_draws(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td);r = self.fixture(root)
            self.assertTrue(check(root)['passed'])
            path = root/'offroad-model-transform.jsonl'
            path.write_text((json.dumps(r)+'\n')*2)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                check(root)
            path.write_text(json.dumps(r)+'\n')
            draws = root/'offroad-model-draws.csv';original = draws.read_text()
            draws.write_text(original.replace('2500,1,', '2500,2,'))
            with self.assertRaisesRegex(ValueError, 'orphan'):
                check(root)
            draws.write_text(original.replace('2500,1,', '2499,1,'))
            with self.assertRaisesRegex(ValueError, 'owner/frame'):
                check(root)
            draws.write_text(original.replace(',266,190,', ',267,190,'))
            self.assertFalse(check(root)['passed'])
            draws.write_text(original)
            receipt = root/'offroad-model-capture.json'
            receipt.write_text(receipt.read_text().replace('true', 'false'))
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                check(root)

    def test_cli_empty_input_produces_failed_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1]/'harness/verify_offroad_model.py'),
                                   str(root), '--report', str(root/'report.json')], capture_output=True)
            self.assertEqual(proc.returncode, 1)
            self.assertFalse(json.loads((root/'report.json').read_text())['passed'])


if __name__ == '__main__':
    unittest.main()
