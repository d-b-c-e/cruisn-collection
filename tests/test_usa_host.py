import argparse
import copy
import csv
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from usa_host_options import add_arguments, configure
from analyze_usa_host import COUNTERS, PHASES, evidence
from analyze_world_host import HASH_SEED, QUAD_FIELDS, hash_quad


class UsaHostOptionsTests(unittest.TestCase):
    def args(self, *values):
        parser = argparse.ArgumentParser()
        add_arguments(parser)
        return parser.parse_args(values)

    def test_absent_options_preserve_every_game_and_old_recording(self):
        for rom in ('crusnusa', 'crusnwld24', 'crusnwld', 'offroadc', 'crusnexo'):
            settings = dict(MIDV_GL='1', unrelated='original')
            before = dict(settings)
            self.assertIsNone(configure(self.args(), rom, settings))
            self.assertEqual(settings, before)

    def test_capture_roundtrip_and_explicit_off(self):
        settings = dict(MIDV_GL='1')
        args = self.args('--usa-host-scenery', 'draw', '--usa-host-first', '3500', '--usa-host-last', '5000', '--usa-host-far', '240000')
        result = configure(args, 'crusnusa', settings)
        before = dict(settings)
        self.assertEqual(configure(self.args(), 'crusnusa', settings), result)
        self.assertEqual(before, settings)
        self.assertEqual(result['log'], 'summary')
        self.assertEqual(result['layer'], 'both')
        configure(self.args('--usa-host-scenery', 'off'), 'crusnusa', settings)
        self.assertEqual(settings, dict(MIDV_GL='1', MIDV_USA_HOST_SCENERY='0'))

    def test_incompatible_modes_and_incomplete_recordings_fail(self):
        valid = self.args('--usa-host-scenery', 'draw', '--usa-host-first', '3500', '--usa-host-last', '5000')
        for rom in ('crusnwld24', 'crusnwld', 'offroadc', 'crusnexo'):
            with self.assertRaises(ValueError):
                configure(valid, rom, dict(MIDV_GL='1'))
        for settings in ({}, dict(MIDV_GL='1', MIDV_USA_FAR='160000')):
            with self.assertRaises(ValueError):
                configure(valid, 'crusnusa', settings)
        for field in ('headless', 'native_renderer'):
            args = copy.copy(valid)
            setattr(args, field, True)
            with self.assertRaises(ValueError):
                configure(args, 'crusnusa', dict(MIDV_GL='1'))
        for settings in (dict(MIDV_USA_HOST_SCENERY='1'), dict(MIDV_USA_HOST_SCENERY='bad')):
            with self.assertRaises(ValueError):
                configure(self.args(), 'crusnusa', settings)
        with self.assertRaises(ValueError):
            configure(self.args('--usa-host-far', '240000'), 'crusnusa', {})


class UsaHostEvidenceTests(unittest.TestCase):
    def write(self, run, scenes, quads):
        for name, rows in [('scenes', scenes), ('quads', quads)]:
            with (run/f'usa-host-{name}.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)

    def fixture(self):
        scene = dict(frame=3501, time='60.123456789000', page=513, mode=1, host_far=240000,
                     **dict.fromkeys(COUNTERS, 0), **dict.fromkeys(PHASES, 0), microseconds=0)
        scene.update(pending=1, decoded=1, quads=1, quads_hash=f'{hash_quad(HASH_SEED, range(16)):016x}')
        quad = dict(frame=scene['frame'], time=scene['time'], page=scene['page'], object=0x1000,
                    model=0xc00000, depth=120000, **dict(zip(QUAD_FIELDS, range(16))))
        return scene, quad

    def test_geometry_words_and_snapshot_clock_are_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            scene, quad = self.fixture()
            self.write(run, [scene], [quad])
            self.assertEqual(evidence(run)[2]['totals']['quads'], 1)
            for field, value in [('palette', 123), ('time', '60.123456789001'), ('page', 516)]:
                self.write(run, [scene], [dict(quad, **{field: value})])
                with self.assertRaises(ValueError): evidence(run)

    def test_duplicate_instrumentation_and_incomplete_counts_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            scene, quad = self.fixture()
            for scenes in ([scene, scene], [dict(scene, pending=2)], [dict(scene, quads=2)],
                           [dict(scene, time='NaN')], [dict(scene, prepare_us=-1, microseconds=-1)]):
                self.write(run, scenes, [quad])
                with self.assertRaises(ValueError): evidence(run)
