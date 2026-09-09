"""Exercise actual launch preparation through Popen without starting an emulator."""
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))


@unittest.skipUnless(sys.platform == 'win32', 'launcher uses Windows APIs')
class LaunchBoundaryTests(unittest.TestCase):
    def exercise_launch(self, rom, enabled, recording=False, trial=None):
        import cheats
        import run_rig

        class SpawnReached(Exception):
            pass

        with tempfile.TemporaryDirectory() as td, ExitStack() as stack:
            root = Path(td)
            rig = root/'rig'
            rig.mkdir()
            (root/'lua').mkdir()
            (root/'lua/cheats.lua').write_text('-- fixture, never executed')
            (rig/'cheats').mkdir()
            xml = b'<mamecheat version="1"><cheat desc="Continuous fixture"><script state="run"><action>maincpu.pb@1234=1</action></script></cheat></mamecheat>'
            (rig/'cheats'/(rom+'.xml')).write_bytes(xml)
            cat = cheats.catalog(rig, rom)
            cheats.save(rig, cat, {'1': 1} if enabled else {})
            for target, value in (('POC', str(root)), ('ROMPATH', str(root/'roms'))):
                stack.enter_context(mock.patch.object(run_rig, target, value))
            stack.enter_context(mock.patch.dict('os.environ', {'MIDV_CHEATS': 'stale-parent-selection'}, clear=True))
            stack.enter_context(mock.patch.object(run_rig, 'prepare_rig', return_value=(str(rig), str(rig))))
            stack.enter_context(mock.patch.object(run_rig, 'sanitized_ctrlrpath', return_value=str(rig)))
            stack.enter_context(mock.patch.object(run_rig, 'kill_stale_vunit'))
            stack.enter_context(mock.patch.object(run_rig, 'deploy_force_profiles'))
            spawn = stack.enter_context(mock.patch.object(run_rig.subprocess, 'Popen', side_effect=SpawnReached))
            options = dict(trial or {})
            if recording:
                options['record_case'] = str(root/'case')
                # Recording's real freeze/path binding has separate tests. Here
                # exercise the launch branches without reading ROMs or executables.
                stack.enter_context(mock.patch('session_case.Recording.prepare',
                    side_effect=lambda command, env, source: (command, env, rig)))
            with self.assertRaises(SpawnReached):
                run_rig.launch_game_async(rom=rom, ffb=0, windowed=True,
                                          mame=str(root/'vunit.exe'), **options)
            command = spawn.call_args.args[0]
            env = spawn.call_args.kwargs['env']
            self.assertEqual(env['MIDV_FFB'], '0')
            self.assertEqual('-cheat' in command, enabled)
            self.assertEqual('-nocheat' in command, not enabled)
            self.assertEqual('MIDV_CHEATS' in env, enabled)
            if enabled:
                self.assertTrue((Path(env['MIDV_CHEATS'])/'settings.lua').is_file())
                self.assertIn('-autoboot_script', command)
            return env

    def test_every_game_reaches_process_creation_with_cheats_on_and_off(self):
        import cheats
        for rom in cheats.ROMS:
            for enabled in (False, True):
                with self.subTest(rom=rom, cheats=enabled):
                    self.exercise_launch(rom, enabled)

    def test_recording_and_each_explicit_trial_reach_process_creation(self):
        cases = [
            ('crusnusa', 'record_usa_trial', dict(far=160000, residency=0), 'MIDV_USA_FAR', '160000'),
            ('crusnwld24', 'record_world_trial', dict(far=160000, lead=8, cpu=100), 'MIDV_WORLD_FAR', '160000'),
            ('crusnwld', 'record_world_trial', dict(far=160000, lead=8, cpu=100), 'MIDV_WORLD_FAR', '160000'),
            ('offroadc', 'record_offroad_trial', dict(multiplier=2), 'MIDV_OFFROAD_DISTANCE', '2'),
            ('crusnexo', 'record_exotica_trial', dict(mode='margins'), 'MIDZ_VISIBILITY', 'margins'),
        ]
        for rom, option, trial, key, value in cases:
            for enabled in (False, True):
                with self.subTest(rom=rom, cheats=enabled):
                    self.exercise_launch(rom, enabled, recording=True)
                    env = self.exercise_launch(rom, enabled, recording=True, trial={option: trial})
                    self.assertEqual(env[key], value)
