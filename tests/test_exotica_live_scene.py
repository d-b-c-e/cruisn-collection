from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from verify_exotica_live_scene import decode_context, fnv_bytes, check_boundary
from verify_exotica_scene import context_bytes


class ExoticaLiveScene(unittest.TestCase):
    def payload(self):
        call = dict(scale=0xfa000000, palette_setup=0x0084003f, state_constants=[0]*12,
                    state_commands=[0]*46, programs=[10, 11, 12, 13], default_state=[0x12000000])
        for i in range(4):call['program'+str(i)] = [0]*4
        context = dict(quad_size=10, ucode=0xc0, palette=1, texture=2, yscale=0, zoffset=0,
                       matrix=[float(i % 4 == 0) for i in range(9)], translation=[1.5, -2.125, 0., 0.],
                       light=[0.]*3, regs=[0]*128, render=[0]*80, render_policy=0)
        raw = context_bytes(5000, 3, 86., 0, dict(bank=2, loading=1), call, context, [1, 2, 3], [0]*9, [1]*9)
        return raw, call, context

    def test_complete_context_roundtrip_and_strict_boundaries(self):
        raw, call, context = self.payload();parsed = decode_context(raw)
        self.assertEqual(parsed['call'], call);self.assertEqual(parsed['context'], context)
        self.assertEqual((parsed['frame'], parsed['bank'], parsed['partial']), (5000, 2, True))
        for corrupted in (raw[:-4], raw+b'\0'*4, b'\0'*4+raw[4:], raw+b'\0'):
            with self.assertRaises(ValueError):decode_context(corrupted)
        bad = bytearray(raw);struct.pack_into('<I', bad, 5*4, 3)
        with self.assertRaisesRegex(ValueError, 'context bounds'):decode_context(bad)
        bad = bytearray(raw);struct.pack_into('<f', bad, 3*4, float('nan'))
        with self.assertRaisesRegex(ValueError, 'context bounds'):decode_context(bad)

    def test_fingerprint_known_vector_and_byte_order(self):
        self.assertEqual(fnv_bytes(b'hello'), 'a430d84680aabd0b')
        self.assertEqual(fnv_bytes(b''), 'cbf29ce484222325')
        self.assertNotEqual(fnv_bytes(b'\1\2\3\4'), fnv_bytes(b'\4\3\2\1'))

    def test_bounds_requires_versioned_context_without_changing_original_fields(self):
        old, call, context = self.payload()
        new = context_bytes(5000, 3, 86., 0, dict(bank=2, loading=1), call, context,
                            [1, 2, 3], [0]*9, [1]*9, frustum_bounds=True)
        self.assertEqual(new[4:-4], old[4:])
        self.assertFalse(decode_context(old)['frustum_bounds'])
        self.assertTrue(decode_context(new)['frustum_bounds'])
        self.assertEqual(decode_context(new)['context'], context)
        for bad in (new[:-4], new[:-4]+struct.pack('<I', 0), new+b'\0'*4, old+struct.pack('<I', 1)):
            with self.assertRaises(ValueError):decode_context(bad)

    def test_scene_can_cross_refresh_but_must_own_first_supported_model(self):
        events = [dict(kind=kind, pc=pc, time=time, frame=frame, flags=flags, camera=[1, 2, 3])
                  for kind, pc, time, frame, flags in (
                      ('begin', 0x67f6, 1., 5000, 0), ('special', 0x6c92, 1.0001, 5000, 0),
                      ('static', 0x6820, 1.0002, 5000, 0), ('model', 0x6964, 1.0003, 5000, 0x80),
                      ('model', 0x6964, 1.0004, 5001, 0), ('model', 0x6964, 1.0005, 5001, 0),
                      ('end', 0x6836, 1.0006, 5001, 0))]
        row = dict(scene=7, scene_time='1.0', scene_frame='5000', cpu_time='1.0004', cpu_frame='5001')
        self.assertTrue(check_boundary(events, row, [1, 2, 3])['passed'])
        with self.assertRaisesRegex(ValueError, 'first supported'):
            check_boundary(events, dict(row, cpu_time='1.0005'), [1, 2, 3])
        with self.assertRaisesRegex(ValueError, 'first supported'):
            check_boundary(events, row, [4, 5, 6])
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            check_boundary(events[:-1], row, [1, 2, 3])
