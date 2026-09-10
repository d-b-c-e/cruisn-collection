from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from page_image import Image, packet


class PageImages(unittest.TestCase):
    def test_delayed_consumer_does_not_use_later_source_bytes(self):
        sources = [bytes(16), b'first page data!', b'other page data!', bytes(16)]
        queue = [packet(sources[i-1] if i else b'', source, 4, i)
                 for i, source in enumerate(sources)]
        image = Image(16, 4)
        for i, wire in enumerate(queue):
            image.apply(wire)
            self.assertEqual(image.data, sources[i])
        self.assertEqual(image.generation, 4)

    def test_corruption_and_missing_updates_leave_old_image_intact(self):
        first = packet(b'', bytes(16), 4, 0)
        second = packet(bytes(16), b'1234567890abcdef', 4, 1)
        image = Image(16, 4)
        image.apply(first)
        for offset in [0, 4, 8, 12, 16, 24, 32, 40, 48, 52, 56, 60, 64, 95]:
            bad = bytearray(second)
            bad[offset] ^= 1
            with self.assertRaises(ValueError):
                image.apply(bad)
            self.assertEqual((image.data, image.generation), (bytes(16), 1))
        with self.assertRaises(ValueError):
            image.apply(second[:-8])
        image.apply(second)
        with self.assertRaises(ValueError):
            image.apply(second)
        self.assertEqual(image.data, b'1234567890abcdef')

    def test_equal_bytes_still_advance_sequence_and_wrong_baseline_fails(self):
        a, b = Image(16, 4), Image(16, 4)
        a.apply(packet(b'', bytes(16), 4, 0))
        b.apply(packet(b'', b'x' * 16, 4, 0))
        equal = packet(bytes(16), bytes(16), 4, 1)
        self.assertEqual(len(equal), 64)
        self.assertEqual(a.apply(equal), [])
        with self.assertRaises(ValueError):
            b.apply(equal)
        self.assertEqual(b.data, b'x' * 16)

    def test_known_indexed_fnv_and_wire_layout(self):
        from page_image import page_hash
        # Fixed values calculated independently from the FNV byte stream.
        self.assertEqual(page_hash(0, b''), 0x4d25767f9dce13f5)
        wire = packet(b'', b'ABCD', 4, 0)
        self.assertEqual(wire[:4], b'PIM1')
        self.assertEqual(struct.unpack_from('<3I', wire, 4), (4, 4, 1))
        self.assertEqual(wire[64:], bytes(4) + b'ABCD')
