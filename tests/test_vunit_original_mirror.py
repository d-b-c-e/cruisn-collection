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
    def test_metadata_capture_can_precede_completed_presentation(self):
        args = SimpleNamespace(vunit_original_mirror_frame=104, vunit_host_metadata_frame=100,
                               candidate='candidate.exe', offroad_host_fade_metadata=True)
        settings = dict(MIDV_GL='1', MIDV_FFB='0', MIDV_OFFROAD_HOST_SCENERY='2',
                        MIDV_OFFROAD_HOST_LAYER='3', MIDV_OFFROAD_HOST_FUTURE='1',
                        MIDV_OFFROAD_HOST_FIRST='80', MIDV_OFFROAD_HOST_LAST='150',
                        MIDV_OFFROAD_HOST_DISTANCE='3')
        configured = settings.copy()
        result = configure(args, 'offroadc', configured, 200)
        self.assertEqual(result['metadata_frame'], 100)
        self.assertEqual(result['frame'], 104)
        self.assertEqual(configured['MIDV_GL_HOST_METADATA_FRAME'], '100')
        for frame in (0, 79, 105):
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args) | {'vunit_host_metadata_frame':frame})),
                          'offroadc', settings.copy(), 200)
        with self.assertRaises(ValueError):
            configure(SimpleNamespace(**(vars(args) | {'vunit_host_metadata_frame':None})),
                      'offroadc', configured, 200)

    def test_candidate_and_ownership_gates(self):
        args = SimpleNamespace(vunit_original_mirror_frame=100, candidate='candidate.exe')
        settings = dict(MIDV_GL='1', MIDV_FFB='0')
        self.assertEqual(configure(args, 'crusnwld', settings.copy(), 200), dict(frame=100, auxiliary=False))
        for rom, changes in [('crusnexo', {}), ('crusnwld', {'MIDV_FFB':'1'}),
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
        with self.assertRaisesRegex(ValueError, 'capture journals'):
            configure(args, 'crusnwld24', dict(host, MIDV_HOST_JOURNALS='quiet'), 200)

    def test_other_vunit_ownership_without_world_fade(self):
        args = SimpleNamespace(vunit_original_mirror_frame=100, candidate='candidate.exe')
        for rom, game in [('crusnusa', 'USA'), ('offroadc', 'OFFROAD')]:
            settings = {'MIDV_GL':'1', 'MIDV_FFB':'0', f'MIDV_{game}_HOST_SCENERY':'2',
                        f'MIDV_{game}_HOST_LAYER':'3'}
            self.assertTrue(configure(args, rom, settings.copy(), 200)['auxiliary'])
            for layer in ('0','1','2'):
                with self.assertRaises(ValueError):
                    configure(args, rom, settings | {f'MIDV_{game}_HOST_LAYER':layer}, 200)
            with self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args) | {'world_host_fade_metadata':True})), rom, settings, 200)

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

    def test_usa_metadata_is_explicit_and_does_not_enable_fade(self):
        args = SimpleNamespace(vunit_original_mirror_frame=100, candidate='candidate.exe',
                               usa_host_fade_metadata=True)
        settings = dict(MIDV_GL='1', MIDV_FFB='0', MIDV_USA_HOST_SCENERY='2',
                        MIDV_USA_HOST_LAYER='3', MIDV_USA_HOST_FUTURE='1',
                        MIDV_USA_HOST_FAR_COVERAGE='1', MIDV_USA_HOST_FIRST='80', MIDV_USA_HOST_LAST='150')
        actual = settings.copy()
        result = configure(args, 'crusnusa', actual, 200)
        self.assertEqual(result['metadata_game'], 'usa')
        self.assertEqual(actual['MIDV_USA_HOST_FADE_METADATA'], '1')
        self.assertNotIn('MIDV_WORLD_HOST_DISTANCE_FADE', actual)
        observed = settings.copy()
        observed_result = configure(SimpleNamespace(**(vars(args) | {'usa_host_opacity_observer':True})),
                                    'crusnusa', observed, 200)
        self.assertTrue(observed_result['opacity_observer'])
        self.assertEqual(observed['MIDV_USA_HOST_OPACITY_OBSERVER'], '1')
        self.assertNotIn('MIDV_WORLD_HOST_DISTANCE_FADE', observed)
        for rom, changes, options in [
                ('offroadc', {}, {}), ('crusnwld', {}, {}),
                ('crusnusa', {'MIDV_USA_HOST_FAR_COVERAGE':'0'}, {}),
                ('crusnusa', {'MIDV_USA_HOST_LAST':'199'}, {}),
                ('crusnusa', {}, {'world_host_distance_fade':True}),
                ('crusnusa', {}, {'usa_host_fade_metadata':False, 'usa_host_opacity_observer':True}),
                ('crusnusa', {'MIDV_USA_HOST_OPACITY_OBSERVER':'1'}, {}),
                ('crusnusa', {}, {'vunit_original_mirror_frame':None}),
                ('crusnusa', {'MIDV_USA_HOST_FADE_METADATA':'1'}, {'usa_host_fade_metadata':False})]:
            with self.subTest(rom=rom, changes=changes, options=options), self.assertRaises(ValueError):
                configure(SimpleNamespace(**(vars(args) | options)), rom, settings | changes, 200)

    def test_usa_metadata_receipts_reject_invented_road_permission(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            words = [F.integer(z).store() for z in (1000, 220000, 239999, 240001)]
            quad = list(range(16))
            fingerprint = 14695981039346656037
            for byte in struct.pack('<16H', *quad):
                fingerprint = ((fingerprint ^ byte)*1099511628211) & 0xffffffffffffffff
            (root/'usa-host-scenes.csv').write_text(
                f'frame,page,quads,quads_hash\n100,513,1,{fingerprint:016x}\n', encoding='utf-8')
            (root/'stderr.log').write_text('MIDV_FADE_METADATA packets=1 roads=0 captured=1\n', encoding='utf-8')
            trial = dict(frame=100, first=80, last=150, fade_metadata=True, metadata_game='usa')
            for policy in (0, 1):
                raw = b'VFD1'+struct.pack('<IHH16HI4II',100,513,3,*quad,240000,*words,policy)
                for name in ('producer', 'consumer'):
                    (root/f'vunit-fade-{name}.bin').write_bytes(raw)
                if policy:
                    with self.assertRaisesRegex(ValueError, 'no authored-road'):
                        verify_metadata(trial, root)
                else:
                    result = verify_metadata(trial, root)
                    self.assertEqual(result['captured_crossings'], 1)
                    self.assertEqual(result['captured_roads'], 0)

    def test_offroad_metadata_uses_projection_bound_without_far_clipping(self):
        args = SimpleNamespace(vunit_original_mirror_frame=100, candidate='candidate.exe',
                               offroad_host_fade_metadata=True, offroad_host_opacity_observer=True)
        settings = dict(MIDV_GL='1', MIDV_FFB='0', MIDV_OFFROAD_HOST_SCENERY='2',
                        MIDV_OFFROAD_HOST_LAYER='3', MIDV_OFFROAD_HOST_FUTURE='1',
                        MIDV_OFFROAD_HOST_DISTANCE='3', MIDV_OFFROAD_HOST_FIRST='80', MIDV_OFFROAD_HOST_LAST='150')
        trial = configure(args, 'offroadc', settings.copy(), 200)
        self.assertEqual(trial['metadata_game'], 'offroad')
        self.assertEqual(configure(args, 'offroadc', dict(settings, MIDV_HOST_RUNTIME='continuous'), 200)
                         ['metadata_runtime_stop'], 199)
        for changes in ({'MIDV_OFFROAD_HOST_DISTANCE':'2'}, {'MIDV_OFFROAD_HOST_CLIP_ADMISSION':'1'}):
            with self.assertRaises(ValueError):
                configure(args, 'offroadc', settings | changes, 200)
        with self.assertRaises(ValueError):
            configure(args, 'crusnusa', settings, 200)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); quad = list(range(16))
            fingerprint = 14695981039346656037
            for byte in struct.pack('<16H', *quad):
                fingerprint = ((fingerprint ^ byte)*1099511628211) & 0xffffffffffffffff
            (root/'offroad-host-scenes.csv').write_text(
                f'frame,page,quads,quads_hash\n100,513,1,{fingerprint:016x}\n', encoding='utf-8')
            (root/'stderr.log').write_text('MIDV_FADE_METADATA packets=1 roads=0 captured=1\n', encoding='utf-8')
            for limit, last in ((191040,191039), (141888,191039), (191040,191040)):
                words = [F.integer(z).store() for z in (503,141888,167308,last)]
                raw = b'VFD1'+struct.pack('<IHH16HI4II',100,513,3,*quad,limit,*words,0)
                for name in ('producer','consumer'):
                    (root/f'vunit-fade-{name}.bin').write_bytes(raw)
                if limit == 191040 and last == 191039:
                    self.assertEqual(verify_metadata(trial,root)['captured_crossings'],0)
                else:
                    with self.assertRaises(ValueError):
                        verify_metadata(trial,root)

    def test_continuous_metadata_counts_scenes_outside_capture_window(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);quad=list(range(16))
            words=[F.integer(z).store() for z in (503, 141888, 167308, 191039)]
            raw=b'VFD1'+struct.pack('<IHH16HI4II',100,513,3,*quad,191040,*words,0)
            for name in ('producer','consumer'):
                (root/f'vunit-fade-{name}.bin').write_bytes(raw)
            fingerprint=14695981039346656037
            for byte in struct.pack('<16H',*quad):
                fingerprint=((fingerprint^byte)*1099511628211)&0xffffffffffffffff
            rows='frame,page,quads,quads_hash\n'+''.join(
                f'{frame},513,1,{fingerprint:016x}\n' for frame in (70,100,170))
            (root/'offroad-host-scenes.csv').write_text(rows,encoding='utf-8')
            (root/'stderr.log').write_text('MIDV_FADE_METADATA packets=3 roads=0 captured=1\n',encoding='utf-8')
            trial=dict(frame=100,first=80,last=150,fade_metadata=True,metadata_game='offroad')
            with self.assertRaisesRegex(ValueError,'scene interval'):
                verify_metadata(trial,root)
            self.assertEqual(verify_metadata(dict(trial,metadata_runtime_stop=199),root)['total_packets'],3)
            with self.assertRaisesRegex(ValueError,'scene interval'):
                verify_metadata(dict(trial,metadata_runtime_stop=169),root)

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
            margin = b'VFD1'+struct.pack('<IHH16HI4II',100,513,7,*quad,240000,*words,1)
            for name in ('producer','consumer'):
                (root/f'vunit-fade-{name}.bin').write_bytes(margin)
            with self.assertRaisesRegex(ValueError,'identity or policy'):
                verify_metadata(trial,root)
            self.assertEqual(verify_metadata(dict(trial,margin_coverage=True),root)['captured_roads'],1)
            for name in ('producer','consumer'):
                (root/f'vunit-fade-{name}.bin').write_bytes(raw)
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
