import argparse
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from game_patch import read_patch
from world_distance import add_arguments, configure, compose
from run_world_distance_trials import motion_script


class GlobalDistanceTests(unittest.TestCase):
    def test_trial_motion_interval_is_frozen_in_evidence(self):
        script = motion_script(1500,8780)
        self.assertNotIn('CRUISN_MOTION_FIRST',script)
        self.assertNotIn('CRUISN_MOTION_LAST',script)
        self.assertIn('tonumber(1500)',script)
        with self.assertRaises(ValueError): motion_script(1500,15000)

    def args(self, *words):
        parser = argparse.ArgumentParser()
        add_arguments(parser)
        return parser.parse_args(words)

    def test_explicit_revision_and_separate_axes(self):
        settings = {'MIDV_SCENERY': 'all'}
        self.assertIsNone(configure(self.args(), 'crusnwld24', settings))
        with self.assertRaises(ValueError): configure(self.args('--world-lead','4'), 'crusnwld24', settings)
        with self.assertRaises(ValueError): configure(self.args('--world-far','100000'), 'crusnwld23', settings)
        self.assertEqual(configure(self.args('--world-far','100000'), 'crusnwld', {}),
                         dict(far=100000,lead=0,cpu=100))
        actual = configure(self.args('--world-far','100000','--world-lead','4','--world-cpu','125'), 'crusnwld24', settings)
        self.assertEqual(actual, dict(far=100000,lead=4,cpu=125))
        self.assertEqual(settings['MIDV_SCENERY'],'off')
        self.assertEqual(settings['MIDV_WORLD_CPU_PERCENT'],'125')

    def test_preserves_base_patch_and_rejects_conflicting_limits(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = root/'base.txt'
            base.write_text('247 0C800000 08620056\n')
            result = read_patch(compose(base, root/'combined.txt',100000))
            self.assertEqual(result[0x247], (0x0c800000,0x08620056))
            self.assertEqual(result[0x40],(80000,100000))
            self.assertEqual(result[0xae],(0x04e31387,0x04e3186a))
            base.write_text('40 00013880 00027100\n')
            with self.assertRaises(ValueError): compose(base,root/'conflict.txt',100000)
            with self.assertRaises(FileExistsError): compose(base,root/'combined.txt',100000)

    def test_three_times_patch_and_bounded_lookahead(self):
        settings = {}
        args = self.args('--world-far', '240000', '--world-lead', '12')
        self.assertEqual(configure(args, 'crusnwld24', settings), dict(far=240000, lead=12, cpu=100))
        with tempfile.TemporaryDirectory() as td:
            patch = read_patch(compose(None, Path(td)/'three.txt', 240000))
            self.assertEqual(patch[0x40], (80000, 240000))
            self.assertEqual(patch[0xae], (0x04e31387, 0x04e33a98))
        args.world_lead = 13
        with self.assertRaises(ValueError): configure(args, 'crusnwld24', settings)
        for rom in ('crusnwld23', 'crusnusa', 'offroadc', 'crusnexo'):
            with self.assertRaises(ValueError): configure(self.args('--world-far', '240000'), rom, {})
