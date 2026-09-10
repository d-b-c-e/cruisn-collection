import argparse
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_scene_options import add_arguments, configure, snapshots, verify_receipt


class ExoticaSceneOptions(unittest.TestCase):
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

    def args(self, *items):
        p = argparse.ArgumentParser();add_arguments(p);p.add_argument('--candidate')
        return p.parse_args(items)

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
