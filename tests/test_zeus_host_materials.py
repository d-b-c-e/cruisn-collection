import csv
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from page_image import HEADER
from zeus_host_materials import parse, verify_live, palette_bytes


class PrivateMaterials(unittest.TestCase):
    def test_late_materials_require_one_ordered_pair_per_scene(self):
        columns = ('scene', 'frame', 'generation', 'pages', 'palettes', 'bytes', 'hash')
        scenes = [dict(scene='12', frame='5000'), dict(scene='13', frame='5001')]
        rows = [dict(zip(columns, (str(12+i//2), str(5000+i//2), str(i+1), '0', '0', '96', '0000000000000009'))) for i in range(4)]
        text = ('MIDZ_HOST_MATERIALS_RESULT queued=4 hash=0000000000000009\n'
                'MIDZ_HOST_MATERIALS_GPU_RESULT complete=1 received=4 snapshots=0 hash=0000000000000009\n')
        with tempfile.TemporaryDirectory() as temp:
            def write(values):
                for name in ('exotica-host-materials.csv', 'exotica-host-materials-gpu.csv'):
                    with (Path(temp)/name).open('w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader();writer.writerows(values)
            write(rows)
            self.assertTrue(verify_live(temp, scenes, [], text, active=True)['passed'])
            with self.assertRaisesRegex(ValueError, 'drain'):
                verify_live(temp, scenes, [], text)
            write([rows[0], rows[2], rows[1], rows[3]])
            with self.assertRaisesRegex(ValueError, 'contract'):
                verify_live(temp, scenes, [], text, active=True)
            write(rows[:-1])
            with self.assertRaisesRegex(ValueError, 'drain'):
                verify_live(temp, scenes, [], text, active=True)

    def test_typed_packet_lengths_and_modes(self):
        pim = HEADER.pack(0x314d4950, 16777216, 4096, 0, 1, 2, 9, 9, 0, 0, 0, 0)
        wire = struct.pack('<IIQ4I', 0x31544d48, 5000, 12, len(pim), 0, 0, 0) + pim
        p = parse(wire)
        self.assertEqual((p['scene'], p['generation'], p['hash'], p['palettes']), (12, 2, 9, []))
        for offset in (0, 16, 20, 24, 28, 32, 36, 40, 44, 56, 80, 84):
            bad = bytearray(wire)
            bad[offset] ^= 2
            with self.assertRaises(ValueError):
                parse(bad)
        for bad in (wire[:-1], wire + b'\0'):
            with self.assertRaises(ValueError):
                parse(bad)

    def test_palette_uses_all_channels_and_ignores_high_bit(self):
        wave = struct.pack('<256H', *(list(range(256))))
        self.assertEqual(struct.unpack_from('<I', palette_bytes(wave, 0), 31*4)[0], 248)
        white = struct.pack('<256H', *([65535]*256))
        self.assertEqual(palette_bytes(white, 0), struct.pack('<I', 0xf8f8f8)*256)

    def test_missing_gpu_update_and_wrong_final_hash_reject(self):
        columns = ('scene','frame','generation','pages','palettes','bytes','hash','stage_us')
        row = dict(zip(columns, ('12','5000','1','4096','0',str(32+64+4096*4100),'0000000000000009','1.0')))
        scenes = [dict(scene='12', frame='5000')]
        text = ('MIDZ_HOST_MATERIALS_RESULT queued=1 hash=0000000000000009\n'
                'MIDZ_HOST_MATERIALS_GPU_RESULT complete=1 received=1 snapshots=0 hash=0000000000000009\n')
        with tempfile.TemporaryDirectory() as temp:
            def write(name, rows):
                with (Path(temp)/name).open('w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader();writer.writerows(rows)
            write('exotica-host-materials.csv', [row])
            write('exotica-host-materials-gpu.csv', [row])
            self.assertTrue(verify_live(temp, scenes, [], text)['passed'])
            with self.assertRaisesRegex(ValueError, 'final'):
                verify_live(temp, scenes, [], text.replace('hash=0000000000000009', 'hash=000000000000000a', 1))
            write('exotica-host-materials-gpu.csv', [])
            with self.assertRaisesRegex(ValueError, 'drain'):
                verify_live(temp, scenes, [], text)
