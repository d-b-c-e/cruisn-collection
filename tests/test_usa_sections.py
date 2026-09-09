import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from scenery_c31 import F
from usa_sections import check_record, future, material_operands, placement, section_definitions, palette_ownership
from verify_usa_materials import compare_samples
from usa_future_scene import collect, uploads
from verify_usa_sections import check
from verify_world_sections import yaw_matrix

CONSTANTS = [4263704963, 4118653474, 3979254875, 4088417758, 4178085694, 4258616668, 4788187]
ZERO = 0x80000000


class UsaSectionTests(unittest.TestCase):
    def test_pending_uploads_hold_only_the_affected_future_material(self):
        m, p, _ = self.memory(0)
        m.update({0x9ea9: 0x1000, 0x9ea8: 0x2000, 0x62: 0x1000, 0xcc3f: 0,
                  0xc00001: 0x2003, 0x1003: 0x50001, 0x2005: 0x8003})
        m.update(dict(enumerate(CONSTANTS, 0xc8ed)))
        self.assertEqual(collect(m.__getitem__)[1]['ready'], 1)
        m.update({0xcc3f: 0xcc42, 0xcc42: 0, 0xcc44: 0x9e0500, 0xcc45: 0x80000100})
        self.assertEqual(uploads(m.__getitem__), (1, {5}, False))
        self.assertEqual(collect(m.__getitem__)[1]['deferred'], 1)
        m[0xcc44] = 0x9e0600
        self.assertEqual(collect(m.__getitem__)[1]['ready'], 1)
        m[0xcc44] = 0xa00000
        self.assertEqual(collect(m.__getitem__)[1]['deferred'], 1)
        m[0xcc42] = 0xcc42
        with self.assertRaises(ValueError): uploads(m.__getitem__)
        m[0xcc42] = 0; m[0xcc44] = 0x980040
        with self.assertRaises(ValueError): uploads(m.__getitem__)
        m[0xcc3f] = 0; m[0x2005] = 0x8004
        self.assertEqual(collect(m.__getitem__)[1]['unbound'], 1)

    def test_live_palette_colors_can_change_but_wrong_slot_ownership_fails(self):
        m = {0x9ea9: 0x1000, 0x9ea8: 0x2000, 0x1003: 0x50001, 0x2005: 0x8003}
        self.assertEqual(palette_ownership(m.__getitem__, 3), 5)
        m[0x2005] = 0x8004
        with self.assertRaises(ValueError): palette_ownership(m.__getitem__, 3)
        m[0x1003] = 0
        self.assertIsNone(palette_ownership(m.__getitem__, 3))
        a = dict(frame=1, texture=b'atlas', palette=bytes(1024), refs=dict(palette_banks=[0], owners={3: 0}))
        b = copy.deepcopy(a); b['frame'] = 2; b['palette'] = b'X'+bytes(1023)
        self.assertTrue(compare_samples(a, b)['passed'])
        self.assertFalse(compare_samples(a, b, require_static=True)['passed'])
        b['refs']['owners'][3] = 1
        self.assertFalse(compare_samples(a, b)['passed'])

    def memory(self, flags):
        p = 0xc10000
        size = 6+bool(flags & 1)+(4 if flags & 8 else 0)+bool(flags & 0x1000)
        data = [flags, ZERO, ZERO, ZERO, ZERO, 0xc20000]
        if flags & 1: data.append(0xc20020)
        if flags & 8: data += [F.integer(v).store() for v in (20, 30, 40, 1)]
        if flags & 0x1000: data.append(0xc20040)
        data += [0xffffffff, 0, 0, 0, 0, 0]
        memory = dict(enumerate(data, p))
        for block in (0xc20000, 0xc20020, 0xc20040):
            memory.update(dict(enumerate([0, 1, 0xc00002, 5, 6, 7, ZERO, 0], block)))
        memory.update({0xa12e: p, 0xe4a5: p, 0xe49d: p, 0xe4a4: 0})
        return memory, p, size

    def test_variable_header_and_third_list_offset_heading(self):
        for flags in (0, 1, 8, 9, 0x1000, 0x1001, 0x1008, 0x1009):
            memory, p, size = self.memory(flags)
            rows, end = section_definitions(memory.__getitem__, p)
            self.assertEqual(end, p+size)
            self.assertEqual(len(rows), 1+bool(flags & 1)+bool(flags & 0x1000))
            for row in rows:
                self.assertEqual(row['section_flags'], flags & ~8 if row['stage'] == 2 else flags)
                self.assertEqual(row['heading'], F.integer(1).store() if row['stage'] == 2 and flags & 8 else ZERO)
        # The sole primary list still receives offsets when no third list exists.
        m, p, _ = self.memory(8)
        row = dict(section_definitions(m.__getitem__, p)[0][0], trig_constants=CONSTANTS)
        baseline = copy.deepcopy(row)
        baseline['section_flags'] = 0
        baseline['definition'][1:4] = [25, 36, 47]
        self.assertEqual(placement(row), placement(baseline))

    def test_completed_and_partial_frontiers_do_not_reemit_current_objects(self):
        m, p, size = self.memory(0x1009)
        before = dict(m)
        self.assertEqual(len(future(m.__getitem__)['definitions']), 3)
        self.assertEqual(m, before)
        m[0xe4a5] = p+size; m[0xe4a4] = 1
        r = future(m.__getitem__)
        self.assertTrue(r['partial']); self.assertEqual(r['definitions'], [])
        m[0xe49d] = p+size
        self.assertFalse(future(m.__getitem__)['partial'])
        m[0xe4a4] = 0
        with self.assertRaisesRegex(ValueError, 'cursor mismatch'): future(m.__getitem__)
        m[0xe4a5] = m[0xe49d] = 0
        self.assertEqual(future(m.__getitem__)['stop'], 'track not initialized')

    def test_unsafe_pointers_counts_and_missing_bindings_fail_closed(self):
        m, p, _ = self.memory(0)
        m[p+5] = 0x980040
        with self.assertRaises(ValueError): section_definitions(m.__getitem__, p)
        m[p+5] = 0xc20000; m[0xc20001] = 4097
        with self.assertRaises(ValueError): section_definitions(m.__getitem__, p)
        m.update({0xc00001: 0x2003, 0x9ea9: 0x1ffff})
        with self.assertRaises(ValueError): material_operands(m.__getitem__, 0xc00002)
        m[0x9ea9] = 0x1000; m[0x1003] = 0
        self.assertEqual(material_operands(m.__getitem__, 0xc00002)['palette_binding'], 0)
        with self.assertRaises(ValueError): future(m.__getitem__, sections=129)

    def record(self):
        identity = [0, ZERO, ZERO, ZERO, 0, ZERO, ZERO, ZERO, 0]
        row = dict(definition=[0xc00002, 0, 0, 0, ZERO, 0xb07], section_words=[8, ZERO, ZERO, ZERO, ZERO, 0, ZERO, ZERO, ZERO, ZERO, 0, 0],
                   section_flags=8, heading=ZERO, trig_constants=CONSTANTS,
                   camera=[ZERO, ZERO, F.integer(6000).store()], view=identity,
                   model_prefix=0x2000, palette_binding=5 << 16, final_pc=0x414f,
                   frame=2000, serial=1, section_pointer=0xc10000)
        row['matrix'] = yaw_matrix(F.load(ZERO), CONSTANTS)
        ready = [0]*34
        ready[1:4] = [ZERO]*3; ready[4:13] = row['matrix']; ready[13] = 0xc00002
        ready[14] = 0x2400; ready[15] = 0xb07; ready[16] = 0x500
        ready[21] = ZERO; ready[28] = (-6000) & 0xffffffff; ready[31] = 0x21aa
        row['ready'] = ready
        row['actual'] = list(ready)
        row['actual'][14] |= 1 << 28; row['actual'][15] = 0x300; row['actual'][30] = 0x21f8
        return row

    def test_final_class_road_tag_negative_depth_and_palette_corruption(self):
        row = self.record()
        self.assertTrue(all(check_record(row).values()))
        for field in (14, 15, 16, 28, 30, 31):
            wrong = copy.deepcopy(row); wrong['actual'][field] ^= 1
            self.assertFalse(all(check_record(wrong).values()), field)
        row['definition'][5] |= 0x2000
        self.assertIsNone(check_record(row))

    def test_capture_completion_and_contiguous_allocation_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            row = self.record()
            (run/'usa-sections.jsonl').write_text(json.dumps(row)+'\n')
            receipt = dict(schema=1, first=1800, last=5010, complete=True, objects=1)
            (run/'usa-section-capture.json').write_text(json.dumps(receipt))
            self.assertTrue(check(run)['passed'])
            for change in (dict(complete=False), dict(objects=2), dict(last=1999)):
                (run/'usa-section-capture.json').write_text(json.dumps(dict(receipt, **change)))
                with self.assertRaises(ValueError): check(run)


if __name__ == '__main__': unittest.main()
