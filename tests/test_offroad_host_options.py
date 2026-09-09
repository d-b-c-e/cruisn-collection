import argparse
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from offroad_host_options import add_arguments, configure


class OffroadHostOptionsTests(unittest.TestCase):
    def args(self, *values):
        parser = argparse.ArgumentParser()
        add_arguments(parser)
        return parser.parse_args(values)

    def trial(self):
        return self.args('--offroad-host-scenery', 'draw', '--offroad-host-first', '1800',
                         '--offroad-host-last', '5990', '--offroad-host-distance', '3',
                         '--offroad-host-source', 'future')

    def test_absent_preserves_all_games_and_recorded_trial_roundtrip(self):
        for rom in ('crusnusa', 'crusnwld24', 'crusnwld', 'offroadc', 'crusnexo'):
            settings = dict(MIDV_GL='1', unrelated='preserved')
            before = dict(settings)
            self.assertIsNone(configure(self.args(), rom, settings))
            self.assertEqual(settings, before)
        result = configure(self.trial(), 'offroadc', settings)
        before = dict(settings)
        self.assertEqual(configure(self.args(), 'offroadc', settings), result)
        self.assertEqual(settings, before)
        self.assertEqual((result['distance'], result['source']), (3, 'future'))
        configure(self.args('--offroad-host-scenery', 'off'), 'offroadc', settings)
        self.assertEqual(settings, dict(MIDV_GL='1', unrelated='preserved', MIDV_OFFROAD_HOST_SCENERY='0'))

    def test_conflicting_guest_distance_wrong_game_and_incomplete_saved_trial(self):
        for rom in ('crusnusa', 'crusnwld24', 'crusnwld', 'crusnexo'):
            with self.assertRaises(ValueError): configure(self.trial(), rom, dict(MIDV_GL='1'))
        for guest in ('1', '2', '3'):
            with self.assertRaises(ValueError):
                configure(self.trial(), 'offroadc', dict(MIDV_GL='1', MIDV_OFFROAD_DISTANCE=guest))
        configure(self.trial(), 'offroadc', dict(MIDV_GL='1', MIDV_OFFROAD_DISTANCE='0'))
        for settings in (dict(MIDV_OFFROAD_HOST_SCENERY='1'), dict(MIDV_OFFROAD_HOST_SCENERY='bad')):
            with self.assertRaises(ValueError): configure(self.args(), 'offroadc', settings)
        for field in ('headless', 'native_renderer'):
            args = copy.copy(self.trial()); setattr(args, field, True)
            with self.assertRaises(ValueError): configure(args, 'offroadc', dict(MIDV_GL='1'))
        with self.assertRaises(ValueError): configure(self.args('--offroad-host-source', 'future'), 'offroadc', {})

    def test_absent_source_remains_absent_and_corrupt_replay_is_rejected(self):
        args = self.trial(); args.offroad_host_source = None
        settings = dict(MIDV_GL='1')
        configure(args, 'offroadc', settings)
        self.assertNotIn('MIDV_OFFROAD_HOST_FUTURE', settings)
        configure(self.args(), 'offroadc', settings)
        self.assertNotIn('MIDV_OFFROAD_HOST_FUTURE', settings)
        for name, value in [('DISTANCE', '4'), ('FIRST', '-1'), ('LAST', '1000001'), ('FUTURE', '2')]:
            bad = dict(settings); bad['MIDV_OFFROAD_HOST_'+name] = value
            with self.assertRaises(ValueError): configure(self.args(), 'offroadc', bad)


if __name__ == '__main__':
    unittest.main()
