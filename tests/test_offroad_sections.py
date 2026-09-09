from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from offroad_sections import sections, descriptor
from verify_offroad_future import allocated_pool, differences


def fixture():
    base, data = 0xc00000, 0xc01000
    m = {0x1b4b4: base, 0x1b4cc: 3, 0x1b4bd: 1, 0x1b4b5: base,
         0x1b4b7: base, 0x1b4ba: base, 0x1b4cd: 0xc03000,
         0x1b4cf: 0x1200, 0x1b4ce: 0x3210}
    for i in range(3):
        m.update({base+4*i: 1 if i == 0 else 0x80000000 if i == 2 else 0,
                  base+4*i+1: i, base+4*i+3: data+64*i,
                  data+64*i+16: 1, data+64*i+17: 0x20, data+64*i+18: 0xc02000})
    return m


class OffroadSectionsTests(unittest.TestCase):
    def test_future_excludes_loaded_and_refreshes_binding(self):
        m = fixture(); read = lambda p: m.get(p, 0)
        a = sections(read); self.assertEqual([s['number'] for s in a['sources']], [1, 2])
        self.assertEqual(a['sources'][0]['words'][6], 0x18000)
        m[0x1b4cf] = 0x2300
        self.assertEqual(sections(read)['sources'][0]['words'][18], 0x2300)
        self.assertEqual(a['sources'][0]['words'][18], 0x1200)
        m[0x1b4b9] = 1
        partial = sections(read)
        self.assertTrue(partial['frontier']['partial'])
        self.assertEqual([s['number'] for s in partial['sources']], [2])
        m.update({0x1b4b7: 0xc00004, 0x1b4b8: 1, 0x1b4b9: 1})
        self.assertEqual([s['number'] for s in sections(read)['sources']], [2])
        self.assertEqual([s['number'] for s in sections(read, True)['sources']], [0, 1])

    def test_partial_boundary_bad_order_end_markers_and_budgets_fail(self):
        for address, value in [(0x1b4b9, 2), (0x1b4b7, 0xc00001), (0xc00005, 17),
                               (0xc00008, 0), (0xc00004, 1), (0x1b4cc, 129),
                               (0xc01050, 257), (0xc00007, 0xfffff8), (0x1b4bd, 2)]:
            m = fixture(); m[address] = value
            with self.subTest(address=address), self.assertRaises(ValueError):
                sections(lambda p: m.get(p, 0))
        self.assertTrue(sections(lambda p: 0)['frontier']['pretrack'])

    def test_custom_non_model_operand_and_stable_tag_bounds(self):
        binding = [0xc03000, 0x100, 0x200]
        words = [0, 0xc02000, *range(9)]
        self.assertEqual(descriptor(words, 255, 0, 256, binding)[6], 0xffff8000)
        for flag in (0x10000000, 0x04000000, 0x00800000, 0x08000000, 0x20000000):
            words[:2] = [flag, 0x980000]
            self.assertIsNone(descriptor(words, 0, 0, 1, binding))
        words[0] = 0
        with self.assertRaises(ValueError):
            descriptor(words, 0, 0, 1, binding)
        words[1] = 0xc02000
        for number, ordinal, count in [(256, 0, 1), (0, 1, 1), (0, 0, 257)]:
            with self.assertRaises(ValueError):
                descriptor(words, number, ordinal, count, binding)

    def test_pool_cycle_guard_and_only_active_flag_is_ignored(self):
        m = {0x111ee: 0x10000, 0x111f6: 0x10, 0x10: 0x10000, 0x10000: 0x10000}
        with self.assertRaisesRegex(ValueError, 'cycle'):
            allocated_pool(lambda p: m.get(p, 0))
        a, b = [0]*22, [0]*22
        b[5] = 0x80000000
        self.assertEqual(differences(a, b), [])
        b[5] |= 4; b[20] = 1
        self.assertEqual(differences(a, b), [5, 20])


if __name__ == '__main__':
    unittest.main()
