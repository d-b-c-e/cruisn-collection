import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_resource_lease import texture_pages, verify, WAVE_BYTES
from exotica_active import sealed_snapshot


class ResourceLease(unittest.TestCase):
    def quad(self, flags=8, kind=0, base=0, width=16, uv=0):
        state = [5000, 3, kind, base, width, 0, 0, 256, 0, flags, 0, 0, 0, 0, 0, 511, 399]
        return struct.pack('<17I48f', *state, *([0., 0., 100., uv, uv, 1.]*8))

    def test_coordinates_wrap_and_all_shader_texture_formats(self):
        for flags in (8, 8|64, 8|128):
            for kind in range(4):
                self.assertEqual(texture_pages(self.quad(flags, kind)), {0})
                self.assertEqual(texture_pages(self.quad(flags, kind, base=0x1fffff, uv=512)), {0, 4095})
        self.assertEqual(texture_pages(self.quad(9)), set())
        self.assertEqual(texture_pages(self.quad(uv=-256)), {0})
        self.assertEqual(len(texture_pages(self.quad(uv=1e10))), 4096)
        for value in (float('nan'), float('inf')):
            with self.assertRaisesRegex(ValueError, 'coordinate'):
                texture_pages(self.quad(uv=value))

    def test_retained_bytes_allow_pointer_advance_but_reject_reuse(self):
        sealed = bytes(WAVE_BYTES);ready = bytearray(sealed)
        # Disjoint model, palette and texture spans exercise each independent guard.
        instance = struct.pack('<11I', 0xbbb5, 0x1000, 0, 1 << 16, 3, 0, 2048, 0, 0, 0, 1)
        mask = bytes([1]+[0]*4095)
        cpu = dict(texture_pages='1', model_checks='1', model_bytes='32', palette_checks='1', camera_advanced='0')
        lease = verify(sealed, ready, instance, self.quad(), mask, cpu)
        ram = bytearray(0x100000);internal = bytes(2048)
        struct.pack_into('<2I', ram, 0x67bf*4, 0x87ff35, 0x87ff3e)
        later = bytearray(ram);struct.pack_into('<I', later, (0x1000+17)*4, 123)
        context = dict(position=[0]*3, view=[0]*9, alternate=[0]*9)
        with self.assertRaisesRegex(ValueError, 'binding'):
            sealed_snapshot(cpu, context, ram, later, internal, instance)
        self.assertEqual(sealed_snapshot(cpu, context, ram, later, internal, instance, lease)['instance_bindings_checked'], 1)
        for address, kind in ((0, 'texture'), (8192, 'model'), (16384, 'palette')):
            ready[address] = 1
            with self.assertRaisesRegex(ValueError, kind):
                verify(sealed, ready, instance, self.quad(), mask, cpu)
            ready[address] = 0
        ready[100000] = 1
        self.assertTrue(verify(sealed, ready, instance, self.quad(), mask, cpu)['passed'])
        with self.assertRaisesRegex(ValueError, 'coverage'):
            verify(sealed, ready, instance, self.quad(), bytes(4096), cpu)


if __name__ == '__main__':
    unittest.main()
