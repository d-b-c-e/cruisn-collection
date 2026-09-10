import argparse
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_scene_options import add_arguments, configure, snapshots, verify_receipt


class ExoticaSceneOptions(unittest.TestCase):
    def test_active_margin_modes_require_fence_and_materials(self):
        base = ('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                '--exotica-host-first', '5000', '--exotica-host-last', '5002')
        settings = {}
        self.assertEqual(configure(self.args(*base), 'crusnexo', settings)['active'], 0)
        self.assertNotIn('MIDZ_HOST_ACTIVE', settings)
        for extra in ((), ('--exotica-host-fence', 'observe'), ('--exotica-host-materials', 'observe')):
            with self.assertRaisesRegex(ValueError, 'require command fence'):
                configure(self.args(*base, *extra, '--exotica-host-active', 'draw'), 'crusnexo', {})
        for mode, number in [('off', 0), ('observe', 1), ('draw', 2)]:
            result = configure(self.args(*base, '--exotica-host-fence', 'observe',
                '--exotica-host-materials', 'observe', '--exotica-host-active', mode), 'crusnexo', settings)
            self.assertEqual(result['active'], number)
            saved = dict(settings)
            self.assertEqual(configure(self.args(), 'crusnexo', settings)['active'], number)
            self.assertEqual(settings, saved)
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-active', 'draw'), 'crusnexo', {})
        configure(self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertEqual(settings, {'MIDZ_HOST_SCENE': '0'})

    def test_command_fence_is_explicit_and_recorded(self):
        args = ('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                '--exotica-host-first', '5000', '--exotica-host-last', '5002')
        settings = {}
        self.assertFalse(configure(self.args(*args), 'crusnexo', settings)['fence'])
        self.assertNotIn('MIDZ_HOST_FENCE', settings)
        self.assertTrue(configure(self.args(*args, '--exotica-host-fence', 'observe'), 'crusnexo', settings)['fence'])
        saved = dict(settings)
        self.assertTrue(configure(self.args(), 'crusnexo', settings)['fence'])
        self.assertEqual(saved, settings)
        settings['MIDZ_HOST_FENCE'] = '2'
        with self.assertRaisesRegex(ValueError, 'command fence mode'):
            configure(self.args(), 'crusnexo', settings)
        configure(self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertEqual(settings, {'MIDZ_HOST_SCENE': '0'})
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-fence', 'observe'), 'crusnexo', {})

    def test_early_depth_is_explicit_and_recorded(self):
        args = ('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                '--exotica-host-first', '5000', '--exotica-host-last', '5002')
        settings = {}
        self.assertEqual(configure(self.args(*args), 'crusnexo', settings)['early_depth'], 0)
        self.assertNotIn('MIDZ_HOST_EARLY_DEPTH', settings)
        for mode, number in [('off', 0), ('on', 1), ('verify', 2)]:
            self.assertEqual(configure(self.args(*args, '--exotica-host-early-depth', mode), 'crusnexo', settings)['early_depth'], number)
            before = dict(settings)
            self.assertEqual(configure(self.args(), 'crusnexo', settings)['early_depth'], number)
            self.assertEqual(settings, before)
        configure(self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertEqual(settings, {'MIDZ_HOST_SCENE': '0'})
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-early-depth', 'on'), 'crusnexo', {})

    def test_early_depth_requires_full_comparison_and_log_counts(self):
        text = ('MIDZ_HOST_SCENE=1 first=5000 last=5002 multiplier=3 snapshots=0\n'
                'MIDZ_HOST_EARLY_DEPTH=2\n'
                'MIDZ_HOST_SCENE_RESULT complete=1 prepared=1 matched=1 quads=5 snapshots=0 pending=0 remaining=0\n'
                'MIDZ_HOST_EARLY_DEPTH_RESULT mode=2 tested=4 verified=3 skipped=0\n')
        trial = dict(self.trial(), early_depth=2)
        with self.assertRaisesRegex(ValueError, 'early depth comparison'):
            verify_receipt(trial, text, 'unused')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'exotica-host-scenes.csv'
            columns = 'frame,cpu_frame,cpu_time,device_time,quads,viewport,guest_cycles,multiplier,scene,scene_frame,scene_time,depth_mode,depth_tests,depth_verified,depth_skipped\n'
            row = '5001,5000,1.0,1.001,5,4,0,3,170,5000,0.999,2,4,4,0\n'
            path.write_text(columns+row, encoding='utf-8')
            text = text.replace('verified=3', 'verified=4')
            self.assertTrue(verify_receipt(trial, text, temp)['passed'])
            path.write_text(columns+row.replace(',2,4,4,0', ',2,3,3,0'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'totals disagree'):
                verify_receipt(trial, text, temp)

    def test_source_cache_is_explicit_and_preserves_recordings(self):
        args = ('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                '--exotica-host-first', '5000', '--exotica-host-last', '5002')
        settings = {}
        self.assertEqual(configure(self.args(*args), 'crusnexo', settings)['source_cache'], 0)
        self.assertNotIn('MIDZ_HOST_SOURCE_CACHE', settings)
        for mode, number in [('off', 0), ('on', 1), ('verify', 2)]:
            trial = configure(self.args(*args, '--exotica-host-source-cache', mode), 'crusnexo', settings)
            self.assertEqual(trial['source_cache'], number)
            before = dict(settings)
            self.assertEqual(configure(self.args(), 'crusnexo', settings)['source_cache'], number)
            self.assertEqual(settings, before)
        settings['MIDZ_HOST_SOURCE_CACHE'] = '3'
        with self.assertRaisesRegex(ValueError, 'source cache mode'):
            configure(self.args(), 'crusnexo', settings)
        configure(self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertEqual(settings, {'MIDZ_HOST_SCENE': '0'})
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-source-cache', 'on'), 'crusnexo', {})

    def test_source_cache_verification_covers_every_scene(self):
        text = ('MIDZ_HOST_SCENE=1 first=5000 last=5002 multiplier=3 snapshots=0\n'
                'MIDZ_HOST_SOURCE_CACHE=2\n'
                'MIDZ_HOST_SCENE_RESULT complete=1 prepared=1 matched=1 quads=5 snapshots=0 pending=0 remaining=0\n'
                'MIDZ_HOST_SOURCE_CACHE_RESULT mode=2 verified=0 hits=0 misses=1\n')
        with self.assertRaisesRegex(ValueError, 'source cache comparison'):
            verify_receipt(dict(self.trial(), source_cache=2), text, 'unused')
        with self.assertRaisesRegex(ValueError, 'source cache comparison'):
            verify_receipt(dict(self.trial(), source_cache=2), text.replace('verified=0', 'verified=1').replace('misses=1', 'misses=0'), 'unused')

    def test_bounds_are_explicit_and_recorded(self):
        args = ('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                '--exotica-host-first', '5000', '--exotica-host-last', '5002')
        settings = {}
        self.assertFalse(configure(self.args(*args), 'crusnexo', settings)['bounds'])
        self.assertNotIn('MIDZ_HOST_BOUNDS', settings)
        self.assertTrue(configure(self.args(*args, '--exotica-host-bounds', 'on'), 'crusnexo', settings)['bounds'])
        before = dict(settings)
        self.assertTrue(configure(self.args(), 'crusnexo', settings)['bounds'])
        self.assertEqual(settings, before)
        self.assertFalse(configure(self.args(*args, '--exotica-host-bounds', 'off'), 'crusnexo', settings)['bounds'])
        self.assertEqual(settings['MIDZ_HOST_BOUNDS'], '0')
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-bounds', 'on'), 'crusnexo', {})

    def test_materials_are_explicit_and_preserve_old_recordings(self):
        args = ('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                '--exotica-host-first', '5000', '--exotica-host-last', '5002')
        settings = {}
        self.assertFalse(configure(self.args(*args), 'crusnexo', settings)['materials'])
        self.assertNotIn('MIDZ_HOST_MATERIALS', settings)
        self.assertTrue(configure(self.args(*args, '--exotica-host-materials', 'observe'), 'crusnexo', settings)['materials'])
        before = dict(settings)
        self.assertTrue(configure(self.args(), 'crusnexo', settings)['materials'])
        self.assertEqual(before, settings)
        configure(self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertEqual(settings, {'MIDZ_HOST_SCENE': '0'})
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-materials', 'observe'), 'crusnexo', {})

    def args(self, *items):
        p = argparse.ArgumentParser();add_arguments(p);p.add_argument('--candidate')
        return p.parse_args(items)

    def test_written_page_mode_requires_materials_and_roundtrips(self):
        args = ('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                '--exotica-host-first', '5000', '--exotica-host-last', '5002')
        settings = {}
        self.assertEqual(configure(self.args(*args), 'crusnexo', settings)['material_pages'], 0)
        self.assertNotIn('MIDZ_HOST_MATERIAL_PAGES', settings)
        with self.assertRaisesRegex(ValueError, 'private material observation'):
            configure(self.args(*args, '--exotica-host-material-pages', 'written'), 'crusnexo', {})
        for mode, number in [('scan', 0), ('written', 1), ('verify', 2)]:
            trial = configure(self.args(*args, '--exotica-host-materials', 'observe',
                                       '--exotica-host-material-pages', mode), 'crusnexo', settings)
            self.assertEqual(trial['material_pages'], number)
            saved = dict(settings)
            self.assertEqual(configure(self.args(), 'crusnexo', settings)['material_pages'], number)
            self.assertEqual(saved, settings)
        configure(self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertEqual(settings, {'MIDZ_HOST_SCENE': '0'})
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-material-pages', 'verify'), 'crusnexo', {})

    def test_written_page_comparison_requires_all_scenes(self):
        text = ('MIDZ_HOST_SCENE=1 first=5000 last=5002 multiplier=3 snapshots=0\n'
                'MIDZ_HOST_MATERIAL_PAGES=2\n'
                'MIDZ_HOST_SCENE_RESULT complete=1 prepared=1 matched=1 quads=5 snapshots=0 pending=0 remaining=0\n'
                'MIDZ_HOST_MATERIAL_PAGES_RESULT mode=2 verified=0\n')
        with self.assertRaisesRegex(ValueError, 'page comparison'):
            verify_receipt(dict(self.trial(), material_pages=2), text, 'unused')

    def trial(self, captured=None):
        return dict(mode='observe', first=5000, last=5002, multiplier=3, snapshots=captured or [])

    def test_original_recordings_unchanged_and_explicit_candidate(self):
        settings = dict(MIDZ_GL='1', MIDV_FFB='80');before = dict(settings)
        self.assertIsNone(configure(self.args(), 'crusnexo', settings))
        self.assertEqual(settings, before)
        with self.assertRaisesRegex(ValueError, 'explicit candidate'):
            configure(self.args('--exotica-host-scene', 'observe'), 'crusnexo', settings)
        with self.assertRaisesRegex(ValueError, 'explicit mode'):
            configure(self.args('--exotica-host-first', '5000'), 'crusnexo', settings)

    def test_recorded_roundtrip_and_off_removes_all_observer_controls(self):
        settings = {}
        a = self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'observe',
                      '--exotica-host-first', '5000', '--exotica-host-last', '5002',
                      '--exotica-host-multiplier', '3', '--exotica-host-snapshots', '5000,5002')
        first = configure(a, 'crusnexo', settings);saved = dict(settings)
        second = configure(self.args(), 'crusnexo', settings)
        self.assertEqual(settings, saved)
        self.assertEqual({k:v for k,v in first.items() if k != 'explicit'},
                         {k:v for k,v in second.items() if k != 'explicit'})
        configure(self.args('--candidate', 'candidate.exe', '--exotica-host-scene', 'off'), 'crusnexo', settings)
        self.assertEqual(settings, dict(MIDZ_HOST_SCENE='0'))
        for rom, initial in (('crusnusa', {}), ('crusnexo', dict(MIDZ_UPSTREAM_RENDER='1'))):
            with self.assertRaises(ValueError):
                configure(a, rom, initial)

    def test_snapshot_budgets_and_native_completion(self):
        for text in ('', '5000,', '5000,5000', '-1', ','.join(str(i) for i in range(17))):
            with self.assertRaises(ValueError):snapshots(text)
        text = ('MIDZ_HOST_SCENE=1 first=5000 last=5002 multiplier=3 snapshots=0\n'
                'MIDZ_HOST_SCENE_RESULT complete=1 prepared=1 matched=1 quads=5 snapshots=0 pending=0 remaining=0\n')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'exotica-host-scenes.csv'
            columns = 'frame,cpu_frame,cpu_time,device_time,quads,viewport,guest_cycles,multiplier,scene,scene_frame,scene_time\n'
            row = '5001,5000,1.0,1.001,5,4,0,3,170,5000,0.999\n'
            path.write_text(columns+row, encoding='utf-8')
            self.assertTrue(verify_receipt(self.trial(), text, temp)['passed'])
            with self.assertRaisesRegex(ValueError, 'bounds acknowledgment'):
                verify_receipt(dict(self.trial(), bounds=True), text, temp)
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                verify_receipt(self.trial(), text.replace('complete=1', 'complete=0'), temp)
            with self.assertRaisesRegex(ValueError, 'acknowledgment'):
                verify_receipt(self.trial(), text.replace('multiplier=3', 'multiplier=2'), temp)
            path.write_text(columns+row.replace(',0,3', ',100,3'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'cycle contract'):
                verify_receipt(self.trial(), text, temp)
            path.write_text(columns+row.replace('170,5000,0.999', '170,4999,0.999'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'cycle contract'):
                verify_receipt(self.trial(), text, temp)
            with self.assertRaisesRegex(ValueError, 'disabled'):
                verify_receipt(dict(mode='off'), text, temp)
