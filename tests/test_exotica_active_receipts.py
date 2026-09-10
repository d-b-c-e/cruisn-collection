import csv
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_active import parse, framebuffer, verify
from page_image import HEADER


class ActiveReceipts(unittest.TestCase):
    def packet(self):
        pim = HEADER.pack(0x314d4950, 16777216, 4096, 0, 1, 2, 9, 9, 0, 0, 0, 0)
        material = (struct.pack('<IIQ4I', 0x31544d48, 5000, 12, len(pim), 1, 0, 0)+pim+
                    struct.pack('<II256I', 0, 0x0084003f, *([0]*256)))
        state = [5000, 8, 0, 0, 32, 0, 0, 256, 0, 24, 0, 0, 0, 0, 0, 511, 399]
        quad = struct.pack('<I17I48f', 0, *state, *([0., 0., 100., 0., 0., 1.]*8))
        return struct.pack('<8I', 0x31444d58, len(material), 1, 86, 0, 1, 0, 0)+material+quad

    def test_packet_owns_fan_and_rejects_bad_state_depth_or_palette(self):
        wire = self.packet()
        result = parse(wire)
        self.assertEqual((result['vertices'], result['margin'], result['draw']), (18, 86, True))
        offset = len(wire)-264
        for position, value in ((offset, 1), (offset+4, 5001), (offset+8, 9),
                                (offset+4+9*4, 24|32), (offset+4+11*4, 400)):
            bad = bytearray(wire);struct.pack_into('<I', bad, position, value)
            with self.assertRaises(ValueError):parse(bad)
        for index, value in ((2, 16777216.), (5, 0.), (0, float('nan'))):
            bad = bytearray(wire);struct.pack_into('<f', bad, offset+72+index*4, value)
            with self.assertRaisesRegex(ValueError, 'D24'):parse(bad)
        with self.assertRaises(ValueError):parse(wire[:-1])

    def test_original_depth_center_other_page_and_observe_are_protected(self):
        w, h, margin, page = 516, 1024, 2, 400
        original = bytes(w*h*4)
        changed = bytearray(original);changed[(page*w)*4] = 255
        self.assertEqual(framebuffer(original, changed, original, original, w, h, page, margin, True)['changed_margin_pixels'], 1)
        with self.assertRaisesRegex(ValueError, 'observe'):
            framebuffer(original, changed, original, original, w, h, page, margin, False)
        with self.assertRaisesRegex(ValueError, 'depth'):
            framebuffer(original, original, original, changed, w, h, page, margin, True)
        for pixel in (page*w+margin, 0, (page+400)*w):
            bad = bytearray(original);bad[pixel*4] = 1
            with self.assertRaisesRegex(ValueError, 'outside'):
                framebuffer(original, bad, original, original, w, h, page, margin, True)

    def test_live_receipts_require_both_consumers_and_fence_identity(self):
        source = dict(scene='12', scene_frame='5000', frame='5000')
        sent = dict(source, ready_frame='5001', objects='1', candidates='1', already_submitted='0',
                    instances='0', quads='0', excluded_raster='1', hash='cbf29ce484222325', guest_cycles='0', assembly_us='1')
        gpu = dict(scene='12', frame='5000', mode='2', quads='0', vertices='0', width='2736', height='4096',
                   page='0', margin='86', snapshot='0', host_us='1')
        fence = dict(scene='12', ready_frame='5001')
        text = ('MIDZ_HOST_ACTIVE=2\nMIDZ_HOST_ACTIVE_RESULT complete=1 scenes=1 quads=0 remaining=0\n'
                'MIDZ_HOST_ACTIVE_GPU_RESULT complete=1 scenes=1 quads=0\n')
        with tempfile.TemporaryDirectory() as temp:
            def write(name, row):
                with (Path(temp)/name).open('w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=list(row));writer.writeheader();writer.writerow(row)
            write('exotica-active-scenes.csv', sent);write('exotica-active-gpu.csv', gpu);write('exotica-host-fences.csv', fence)
            self.assertTrue(verify(temp, [source], text, 2, [])['passed'])
            with self.assertRaisesRegex(ValueError, 'disabled'):verify(temp, [source], text, 0, [])
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                verify(temp, [source], text.replace('complete=1', 'complete=0'), 2, [])
            write('exotica-host-fences.csv', dict(fence, ready_frame='5000'))
            with self.assertRaisesRegex(ValueError, 'ownership'):verify(temp, [source], text, 2, [])
