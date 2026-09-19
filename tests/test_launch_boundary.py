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
    def test_blocking_wrapper_forwards_launch_only_force_off(self):
        import run_rig
        process = mock.Mock(recording=None)
        process.poll.return_value = 0
        with mock.patch.object(run_rig, 'launch_game_async', return_value=(process, None)) as launch, \
             mock.patch.object(run_rig, 'wait_or_kill', return_value=0):
            self.assertEqual(run_rig.launch_game(ffb=65, force_ffb_off=True), 0)
        self.assertIs(launch.call_args.kwargs['force_ffb_off'], True)
        self.assertEqual(launch.call_args.kwargs['ffb'], 65)

    def exercise_launch(self, rom, enabled, recording=False, trial=None, imported=True, config=None, telemetry=None, strength=0, expected_ffb="0", environment=None, stopped=False, capable=False, inventory=None, controls=False):
        import cheats
        import run_rig

        class SpawnReached(Exception):
            pass

        with tempfile.TemporaryDirectory() as td, ExitStack() as stack:
            root = Path(td)
            rig = root/'rig'
            rig.mkdir()
            if stopped: (rig/'ffb-user-stopped').write_bytes(b'')
            if config or telemetry:
                (rig/'collection.ini').write_text('[collection]\n'+''.join(f'{k}={v}\n' for k,v in (config or {}).items())+
                    '[telemetry]\n'+''.join(f'{k}={v}\n' for k,v in (telemetry or {}).items()),encoding='utf-8')
            if controls:
                from control_preferences import commit_proposals, make_proposal
                path = rig/'collection.ini'
                commit_proposals(path, [make_proposal('steer', inventory[0]['identity'], 'XAXIS')],
                    expected_original=path.read_bytes() if path.exists() else None, inventory=inventory)
            (root/'lua').mkdir()
            (root/'lua/cheats.lua').write_text('-- fixture, never executed')
            (rig/'cheats').mkdir()
            xml = b'<mamecheat version="1"><cheat desc="Continuous fixture"><script state="run"><action>maincpu.pb@1234=1</action></script></cheat></mamecheat>'
            if imported: (rig/'cheats'/(rom+'.xml')).write_bytes(xml)
            cat = cheats.catalog(rig, rom)
            cheats.save(rig, cat, {'1': 1} if enabled else {})
            for target, value in (('POC', str(root)), ('ROMPATH', str(root/'roms'))):
                stack.enter_context(mock.patch.object(run_rig, target, value))
            stack.enter_context(mock.patch.dict('os.environ', {'MIDV_CHEATS': 'stale-parent-selection', **(environment or {})}, clear=True))
            stack.enter_context(mock.patch.object(run_rig, 'prepare_rig', return_value=(str(rig), str(rig))))
            stack.enter_context(mock.patch.object(run_rig, 'sanitized_ctrlrpath', return_value=str(rig)))
            stack.enter_context(mock.patch.object(run_rig, 'kill_stale_vunit'))
            stack.enter_context(mock.patch.object(run_rig, 'deploy_force_profiles'))
            stack.enter_context(mock.patch('control_launch.supported', return_value=capable))
            stack.enter_context(mock.patch.object(run_rig.dinput_axes, 'inventory', return_value=inventory or []))
            spawn = stack.enter_context(mock.patch.object(run_rig.subprocess, 'Popen', side_effect=SpawnReached))
            options = dict(trial or {})
            if recording:
                options['record_case'] = str(root/'case')
                # Recording's real freeze/path binding has separate tests. Here
                # exercise the launch branches without reading ROMs or executables.
                stack.enter_context(mock.patch('session_case.Recording.prepare',
                    side_effect=lambda command, env, source: (command, env, rig)))
            preference = rig/'collection.ini'
            saved = preference.read_bytes() if preference.exists() else None
            with self.assertRaises(SpawnReached):
                run_rig.launch_game_async(rom=rom, ffb=strength, windowed=True,
                                          mame=str(root/'vunit.exe'), **options)
            self.assertEqual(preference.read_bytes() if preference.exists() else None, saved)
            command = spawn.call_args.args[0]
            env = spawn.call_args.kwargs['env']
            self.assertEqual(env['MIDV_FFB'], expected_ffb)
            self.assertEqual(env['MIDV_FFB_STOP_FILE'], str(rig/'ffb-user-stopped'))
            self.assertEqual('-cheat' in command, imported)
            self.assertEqual('-nocheat' in command, not imported)
            self.assertEqual('MIDV_CHEATS' in env, imported)
            if imported:
                self.assertTrue((Path(env['MIDV_CHEATS'])/'settings.lua').is_file())
                self.assertIn('-autoboot_script', command)
            return env

    def test_verified_device_output_and_calibration_reach_launch_without_stale_paths(self):
        identity = dict(backend='dinput', product_guid='0006346e-0000-0000-0000-504944564944',
                        instance_guid='11111111-2222-3333-4444-555555555555',
                        hid_path=r'\\?\HID#FIXTURE', ffb_capable=True)
        inventory = [dict(identity=identity, name='Fixture wheel', axes=['XAXIS'])]
        for rom in ('crusnusa', 'crusnwld24', 'offroadc', 'crusnexo'):
            env = self.exercise_launch(rom, False, imported=False, capable=True, inventory=inventory,
                controls=True, strength=50, expected_ffb='1', config={'ffb_enabled': '1'},
                environment={'MIDV_FFB_DEVICE': 'wrong-wheel', 'MIDV_INPUT_PROFILE': 'owner-stale-path'})
            self.assertEqual(env['MIDV_FFB_DEVICE'], 'path:'+identity['hid_path'])
            self.assertTrue(env['MIDV_INPUT_PROFILE'].endswith('control-calibration.txt'))
            env = self.exercise_launch(rom, False, imported=False, capable=True,
                strength=50, config={'ffb_enabled': '1'},
                environment={'MIDV_FFB_DEVICE': 'wrong-wheel', 'MIDV_INPUT_PROFILE': 'owner-stale-path'})
            self.assertEqual(env['MIDV_FFB'], '0')
            self.assertNotIn('MIDV_FFB_DEVICE', env)
            self.assertNotIn('MIDV_INPUT_PROFILE', env)
            # Device is now resolved, but a prior explicit Continue without FFB
            # cannot be undone by that change or inherited environment values.
            env = self.exercise_launch(rom, False, imported=False, capable=True, inventory=inventory,
                controls=True, strength=65, config={'ffb_enabled': '1', 'ffb': '65'},
                trial={'force_ffb_off': True}, environment={'MIDV_FFB': '1', 'MIDV_FFB_TEST': '50'})
            self.assertEqual(env['MIDV_FFB'], '0')
            self.assertNotIn('MIDV_FFB_TEST', env)

    def test_saved_ffb_switch_and_explicit_diagnostic_off(self):
        for rom in ('crusnusa','crusnwld24','crusnwld','offroadc','crusnexo'):
            for on in (False, True):
                with self.subTest(rom=rom,on=on):
                    env=self.exercise_launch(rom,False,imported=False,strength=65,
                        expected_ffb='1' if on else '0',
                        config={'ffb':'65','ffb_enabled':'1' if on else '0'})
                    if on:
                        self.assertEqual(env['MIDV_FFB_STRENGTH'],'52' if rom=='crusnexo' else '65')
                    if rom.startswith('crusnwld'):
                        self.assertNotEqual(env.get('MIDV_FFB_GAME_GATE'),'1')
            self.exercise_launch(rom,False,imported=False,strength=80,stopped=True,
                config={'ffb_enabled':'1'},environment={'MIDV_FFB':'1'})
            self.exercise_launch(rom,False,imported=False,strength=65,
                config={'ffb_enabled':'1'},environment={'MIDV_FFB':'0'})
            env=self.exercise_launch(rom,False,imported=False,strength=None,
                config={'ffb':'0'},environment={'MIDV_FFB':'1','MIDV_FFB_TEST':'1'})
            self.assertNotIn('MIDV_FFB_TEST',env)

    def test_saved_telemetry_switch_reaches_all_game_launches(self):
        for rom in ('crusnusa','crusnwld24','crusnwld','offroadc','crusnexo'):
            for on in (False,True):
                with self.subTest(rom=rom,on=on):
                    env=self.exercise_launch(rom,False,imported=False,
                        telemetry=dict(enabled='1' if on else '0',forza='192.0.2.5:5300',udp='127.0.0.1:20777'))
                    self.assertEqual('MIDV_TELEM_FORZA' in env,on)
                    self.assertEqual('MIDV_TELEM_UDP' in env,on)
                    if on:self.assertEqual(env['MIDV_TELEM_FORZA'],'192.0.2.5:5300')

    def test_every_game_reaches_process_creation_with_cheats_on_and_off(self):
        import cheats
        for rom in cheats.ROMS:
            for enabled in (False, True):
                with self.subTest(rom=rom, cheats=enabled):
                    self.exercise_launch(rom, enabled)
            self.exercise_launch(rom, False, imported=False)

    def test_exotica_feedback_experiment_reaches_normal_and_recording_launch(self):
        for recording in (False,True):
            for value,expected in (('0','1'),('1','0')):
                env=self.exercise_launch('crusnexo',False,recording=recording,
                    config={'menu_feedback_crusnexo':value},trial={'scale':1,'margin':0})
                self.assertEqual(env['MIDV_FFB_GAME_GATE'],expected)
                self.assertEqual(env['MIDV_FFB'],'0')

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
