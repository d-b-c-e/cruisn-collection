from pathlib import Path
from types import SimpleNamespace
import json
import csv
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from vunit_original_mirror import configure, verify, compare_originals, verify_metadata
from scenery_c31 import F


class OriginalMirrorTests(unittest.TestCase):
    def test_candidate_and_ownership_gates(self):
        args = SimpleNamespace(vunit_original_mirror_frame=100, candidate='candidate.exe')
        settings = dict(MIDV_GL='1', MIDV_FFB='0')
        self.assertEqual(configure(args, 'crusnwld', settings.copy(), 200), dict(frame=100, auxiliary=False))
        for rom, changes in [('crusnusa', {}), ('crusnwld', {'MIDV_FFB':'1'}),
                             ('crusnwld', {'MIDV_GL_BATCH_VRAM':'0'}),
                             ('crusnwld', {'MIDV_WORLD_HOST_SCENERY':'2','MIDV_WORLD_HOST_LAYER':'1'})]:
            with self.subTest(rom=rom, changes=changes), self.assertRaises(ValueError):
                configure(args, rom, dict(settings, **changes), 200)
        for changes in [dict(candidate=None), dict(headless=True), dict(native_renderer=True),
                        dict(vunit_original_mirror_frame=199)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args) | changes)), 'crusnwld', settings.copy(), 200)
        host = dict(settings, MIDV_WORLD_HOST_SCENERY='2', MIDV_WORLD_HOST_LAYER='3')
        self.assertTrue(configure(args, 'crusnwld24', host, 200)['auxiliary'])

    def test_explicit_selection_and_missing_receipt(self):
        args = SimpleNamespace(vunit_original_mirror_frame=None)
        self.assertIsNone(configure(args, 'crusnwld', {}, 200))
        with self.assertRaises(ValueError):
            configure(args, 'crusnwld', {'MIDV_GL_ORIGINAL_MIRROR':'1'}, 200)
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(verify(None, root))
            with self.assertRaises(ValueError):
                verify(dict(frame=100, auxiliary=False), root)

    def test_metadata_requires_full_owned_capture_and_drain_interval(self):
        args = SimpleNamespace(vunit_original_mirror_frame=100, candidate='candidate.exe',
                               world_host_fade_metadata=True)
        settings = dict(MIDV_GL='1', MIDV_FFB='0', MIDV_WORLD_HOST_SCENERY='2',
                        MIDV_WORLD_HOST_LAYER='3', MIDV_WORLD_HOST_FUTURE='1',
                        MIDV_WORLD_HOST_FAR_COVERAGE='1', MIDV_WORLD_HOST_FIRST='80', MIDV_WORLD_HOST_LAST='150')
        self.assertTrue(configure(args, 'crusnwld', settings.copy(), 200)['fade_metadata'])
        fade_args = SimpleNamespace(**(vars(args) | {'world_host_distance_fade':True}))
        self.assertTrue(configure(fade_args, 'crusnwld', settings.copy(), 200)['distance_fade'])
        with self.assertRaisesRegex(ValueError, 'explicit qualified metadata'):
            configure(SimpleNamespace(**(vars(fade_args) | {'world_host_fade_metadata':False})),
                      'crusnwld', settings.copy(), 200)
        for changes in [dict(MIDV_WORLD_HOST_FIRST='101'), dict(MIDV_WORLD_HOST_LAST='199'),
                        dict(MIDV_WORLD_HOST_FAR_COVERAGE='0'), dict(MIDV_WORLD_HOST_FUTURE='0')]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                configure(args, 'crusnwld', dict(settings, **changes), 200)

    def test_metadata_boundaries_depths_order_and_consumer_coverage(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            words = [F.integer(z).store() for z in (1000, 220000, 239999, 240001)]
            quad = list(range(16))
            packet = struct.pack('<IHH16HI4II', 100, 513, 3, *quad, 240000, *words, 1)
            raw = b'VFD1'+packet
            for name in ('producer', 'consumer'):
                (root/f'vunit-fade-{name}.bin').write_bytes(raw)
            stderr = root/'stderr.log'
            stderr.write_text('MIDV_FADE_METADATA packets=1 roads=1 captured=1\n')
            fingerprint = 14695981039346656037
            for byte in struct.pack('<16H', *quad):
                fingerprint = ((fingerprint ^ byte)*1099511628211) & 0xffffffffffffffff
            row = dict(frame=100, page=513, quads=1, road_quads=1, quads_hash=f'{fingerprint:016x}')
            with (root/'world-host-scenes.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row));writer.writeheader();writer.writerow(row)
            trial = dict(frame=100, first=80, last=150, fade_metadata=True)
            self.assertEqual(verify_metadata(trial, root)['captured_crossings'], 1)
            mirror = dict(frame=100, width=512, height=256, visible_page=0,
                          ordinary_quads=1, auxiliary_quads=1, cpu_blits=1, original_resets=1)
            (root/'vunit-mirror.json').write_text(json.dumps(mirror))
            for page in range(2):
                for plane in range(4):
                    (root/f'vunit-mirror-100-page{page}-plane{plane}.bin').write_bytes(bytes(512*256*(1 if plane & 1 else 2)))
                (root/f'vunit-mirror-100-page{page}-alpha.bin').write_bytes(struct.pack('<f', 1)*512*256)
            fade_trial = dict(trial, distance_fade=True, auxiliary=True)
            self.assertTrue(all(s['opaque']==512*256 for s in verify(fade_trial, root)['opacity']))
            alpha = root/'vunit-mirror-100-page1-alpha.bin'
            with alpha.open('r+b') as stream:
                stream.write(struct.pack('<f', float('nan')))
            with self.assertRaisesRegex(ValueError, 'invalid distance fade opacity'):
                verify(fade_trial, root)
            with alpha.open('r+b') as stream:
                stream.write(struct.pack('<f', 1))
            stderr.write_text('MIDV_FADE_METADATA packets=0 roads=0 captured=1\n')
            with self.assertRaisesRegex(ValueError, 'consumer coverage'):
                verify_metadata(trial, root)
            stderr.write_text('MIDV_FADE_METADATA packets=1 roads=1 captured=1\n')
            corrupted = bytearray(raw)
            struct.pack_into('<I', corrupted, 4+44, 0)  # first depth: invalid zero C31 exponent
            for name in ('producer', 'consumer'):
                (root/f'vunit-fade-{name}.bin').write_bytes(corrupted)
            with self.assertRaisesRegex(ValueError, 'depth'):
                verify_metadata(trial, root)
            (root/'vunit-fade-consumer.bin').write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'FIFO'):
                verify_metadata(trial, root)

    def test_empty_capture_requires_no_matching_scene_quads_and_full_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('producer', 'consumer'):
                (root/f'vunit-fade-{name}.bin').write_bytes(b'VFD1')
            (root/'stderr.log').write_text('MIDV_FADE_METADATA packets=2 roads=1 captured=0\n')
            scene = root/'world-host-scenes.csv'
            scene.write_text('frame,page,quads,road_quads,quads_hash\n99,0,2,1,unused\n')
            trial = dict(frame=100, first=80, last=150, fade_metadata=True)
            self.assertEqual(verify_metadata(trial, root)['captured'], 0)
            scene.write_text('frame,page,quads,road_quads,quads_hash\n100,0,2,1,unused\n')
            with self.assertRaisesRegex(ValueError, 'road/count mismatch'):
                verify_metadata(trial, root)
            scene.write_text('frame,page,quads,road_quads,quads_hash\n99,0,3,1,unused\n')
            with self.assertRaisesRegex(ValueError, 'consumer coverage'):
                verify_metadata(trial, root)

    def test_both_pages_exact_and_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            row = dict(frame=100, width=512, height=256, visible_page=1,
                       ordinary_quads=20, auxiliary_quads=0, cpu_blits=3, original_resets=2)
            (root/'vunit-mirror.json').write_text(json.dumps(row))
            for page in range(2):
                for plane in range(4):
                    count = 512*256*(1 if plane & 1 else 2)
                    (root/f'vunit-mirror-100-page{page}-plane{plane}.bin').write_bytes(bytes([page])*count)
            trial = dict(frame=100, auxiliary=False)
            result = verify(trial, root)
            self.assertTrue(result['passed'])
            self.assertTrue(compare_originals(result, result)['passed'])
            with self.assertRaisesRegex(ValueError, 'sequence differs'):
                compare_originals(result, dict(result, original_resets=3))
            changed = dict(result, sha256=dict(result['sha256']))
            changed['sha256']['vunit-mirror-100-page1-plane3.bin'] = 'wrong'
            with self.assertRaisesRegex(ValueError, 'pixels changed'):
                compare_originals(result, changed)
            with self.assertRaises(ValueError):
                verify(None, root)
            path = root/'vunit-mirror-100-page1-plane2.bin'
            with path.open('r+b') as stream:
                stream.write(b'\xff')
            with self.assertRaisesRegex(ValueError, 'differs'):
                verify(trial, root)
            path.write_bytes(b'')
            with self.assertRaisesRegex(ValueError, 'wrong-size'):
                verify(trial, root)


if __name__ == '__main__':
    unittest.main()
