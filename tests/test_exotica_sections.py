import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from scenery_c31 import F
from exotica_sections import sections, descriptor, yaw_matrix

TRIG = [4263704963, 4118653474, 3979254875, 4088417758, 4178085694, 4258616668, 4788187]


def fixture():
    m = {0xb7e8: 0x082e0597, 0xb804: 0x08442501, 0xb817: 0x152e0597,
         0xb842: 0x084a2501, 0xb859: 0x082267c4, 0xb86f: 0x14420416,
         0xb878: 0x08402501, 0xb8cb: 0x0840041d, 0xbc36: 0x08400202,
         0xa032: 0x0221e67c, 0xa025: 0x0221e67d, 0x92e8: 0x24e02122,
         0x92f8: 0xc00201c1, 0xb840: 0x1420059b, 0xbbaa: 0x80000, 0xbbb1: 0x4000000,
         0x1fbc: 0xa00000, 0xa00000: 0xa00010,
         0x597: 0xa00017, 0x590: 256, 0x598: 30,
         0x599: 0x80000000, 0x59a: 0x80000000, 0x59b: F.integer(100).store(), 0x59c: 0x80000000,
         0xe67c: 0x100, 0xe67d: 0x110, 0x100: 0xc03000, 0x110: 0xc03100,
         0xc03000: 123, 0xc03100: 456, 0xc02001: 10}
    m.update({0xe991+i: v for i, v in enumerate(TRIG)})
    for i in range(2):
        m[0xa00013+4*i] = 0xc01004
    for i in range(4):
        m[0xa0001b+i] = 0xffffffff
    for i, v in enumerate([0x80000000, 0x80000000, F.integer(100).store(), 0x80000000, 29 << 16,
                           0xc02000, 5, 0, 10, 0x80000000, 0]):
        m[0xc01000+i] = v
    return m


class ExoticaSections(unittest.TestCase):
    def test_future_frontier_material_rebinding_and_no_writes(self):
        m = fixture(); original = copy.deepcopy(m); read = lambda p: m.get(p, 0)
        result = sections(read)
        self.assertEqual(m, original)
        self.assertEqual([r['future'] for r in result['sources']], [False, True])
        self.assertEqual(result['sources'][1]['words'][1:4], [F.integer(5).store(), 0x80000000, F.integer(110).store()])
        self.assertEqual(result['sources'][1]['words'][18:20], [456, 123])
        m[0xc03100] = 789
        self.assertEqual(sections(read)['sources'][1]['words'][18], 789)
        self.assertFalse(any(r['future'] for r in sections(read, partial=True)['sources']))
        m[0x598] = 31
        with self.assertRaisesRegex(ValueError, 'boundary'):
            sections(read)

    def test_revision_and_bad_model_guards(self):
        m = fixture(); read = lambda p: m.get(p, 0)
        m[0xc01005] = 0xff980000
        self.assertFalse(sections(read)['sources'][0]['supported'])
        m[0xc01005] = 0x980000
        with self.assertRaisesRegex(ValueError, 'model'):
            sections(read)
        m[0xb7e8] = 0
        with self.assertRaisesRegex(ValueError, 'revision'):
            sections(read)

    def test_reverse_road_and_billboard_render_fields(self):
        zero = 0x80000000
        context = dict(flags=1|32, header=[zero]*5, position=[zero]*3, heading=zero,
                       section_heading=0x01491000, gap=29, cursor=100, index=2, initial=False)
        matrix = yaw_matrix(F.load(0x01491000), TRIG)
        constants = [0]*11; constants[0]=0x80000; constants[7]=0x4000000; constants[8]=0x8000000
        obj = descriptor([0xc02000, 0, 0, 0, zero, 3*0x4000000|0x8000|0xb05],
                         [0, 10, 0, 0, 0, 0], context, matrix, constants, TRIG, (17, 18))
        self.assertEqual(obj[1:4], [zero]*3)
        self.assertEqual(obj[22], F.integer(254).store())
        self.assertEqual(obj[24], 0x2fa)
        self.assertEqual(obj[29], 126)
        self.assertEqual(obj[15], 0xc080130)
        self.assertEqual(obj[16], 0x78080002)

    def test_end_frontier_and_pretrack(self):
        m = fixture(); read = lambda p: m.get(p, 0)
        m.update({0x597: 0xa0001b, 0x590: 512, 0x598: 60, 0x59b: F.integer(200).store()})
        self.assertFalse(any(r['future'] for r in sections(read)['sources']))
        with self.assertRaisesRegex(ValueError, 'boundary'):
            sections(read, partial=True)
        for p in (0x597, 0x590, 0x598):m[p] = 0
        self.assertTrue(sections(read)['pretrack'])
