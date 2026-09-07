import importlib.util
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('updater_under_test',ROOT/'harness/updater.py')
updater=importlib.util.module_from_spec(spec)
with mock.patch.dict(sys.modules,{'run_rig':types.SimpleNamespace(POC='unused')}):
    spec.loader.exec_module(updater)


def make_zip(path, extras=None):
    files={name:b'new runtime' for name in ('CruisnCollection.exe','CruisnSetup.exe','vunit.exe','SDL2.dll')}
    files['version.txt']=b'v0.4.0'
    files.update(extras or {})
    with zipfile.ZipFile(path,'w') as z:
        for name,data in files.items():z.writestr('CruisnCollection/'+name,data)


class UpdateTests(unittest.TestCase):
    def test_rc_can_upgrade_to_final_and_bad_archives_are_rejected(self):
        self.assertTrue(updater.is_newer('v0.4.0','v0.4.0-rc1'))
        self.assertFalse(updater.is_newer('v0.4.0','v0.4.0'))
        self.assertFalse(updater.is_newer('v0.3.7','v0.4.0-rc1'))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'update.zip'
            make_zip(path);self.assertEqual(updater.validate_update_package(path),'CruisnCollection')
            for extra in ({'../../outside':b'bad'},{'rig/collection.ini':b'personal'},
                          {'roms/game.zip':b'rom'},{'VUNIT.exe':b'duplicate'}):
                make_zip(path,extra)
                with self.assertRaises(ValueError):updater.validate_update_package(path)
            path.write_bytes(b'truncated ZIP')
            with self.assertRaises(zipfile.BadZipFile):updater.validate_update_package(path)

    def test_first_launch_migration_preserves_unknown_files_and_known_backup_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);proxy=root/'dinput8.dll';proxy.write_bytes(b'known test proxy')
            with mock.patch.object(updater,'LEGACY_INPUT_HASHES',{hashlib.sha256(proxy.read_bytes()).hexdigest()}):
                backup=updater.retire_input_proxy(root,root/'rig/update')
            self.assertEqual(backup.read_bytes(),b'known test proxy')
            self.assertFalse(proxy.exists())
            self.assertIsNone(updater.retire_input_proxy(root,root/'rig/update'))
            proxy.write_bytes(b'unknown')
            with self.assertRaisesRegex(RuntimeError,'unrecognized'):
                updater.retire_input_proxy(root,root/'rig/update')
            self.assertEqual(proxy.read_bytes(),b'unknown')

    @unittest.skipUnless(sys.platform=='win32','executes the actual Windows update helper')
    def test_real_helper_handles_quoted_paths_preserves_rig_and_rejects_changed_zip(self):
        with tempfile.TemporaryDirectory(prefix='cruisn-update-') as td:
            app=Path(td)/"Player's Folder";app.mkdir()
            (app/'rig').mkdir();(app/'roms').mkdir()
            (app/'rig/collection.ini').write_bytes(b'current bindings')
            (app/'roms/owned.zip').write_bytes(b'owned ROM')
            (app/'version.txt').write_bytes(b'old')
            package=Path(td)/"Player's update.zip";make_zip(package)
            with mock.patch.object(updater,'frozen',return_value=True), \
                 mock.patch.object(updater,'app_dir',return_value=str(app)), \
                 mock.patch.object(updater.run_rig,'POC',str(app)):
                def prepare():
                    with mock.patch.object(updater.subprocess,'Popen') as launch:
                        script=updater.apply(str(package),relaunch=False)
                        self.assertEqual(launch.call_count,1)
                    return script,launch.call_args.kwargs['env']
                def run(prepared):
                    script,environment=prepared
                    return subprocess.run([os.environ['SystemRoot']+'/System32/WindowsPowerShell/v1.0/powershell.exe',
                        '-NoProfile','-ExecutionPolicy','Bypass','-File',script],capture_output=True,timeout=40,env=environment)
                first=run(prepare())
                self.assertEqual(first.returncode,0,(app/'rig/update/apply.log').read_text(errors='replace')
                                 +first.stderr.decode(errors='replace'))
                self.assertEqual((app/'version.txt').read_bytes(),b'v0.4.0')
                self.assertEqual((app/'rig/collection.ini').read_bytes(),b'current bindings')
                self.assertEqual((app/'roms/owned.zip').read_bytes(),b'owned ROM')
                (app/'version.txt').write_bytes(b'keep this')
                script=prepare();make_zip(package,{'extra.txt':b'changed after validation'})
                second=run(script)
                self.assertNotEqual(second.returncode,0)
                self.assertEqual((app/'version.txt').read_bytes(),b'keep this')
                # Exercise the actual move, retaining a backup. A filename
                # alone never authorizes moving an unknown custom input DLL.
                make_zip(package)
                legacy=b'known legacy input proxy fixture'
                (app/'dinput8.dll').write_bytes(legacy)
                with mock.patch.object(updater,'LEGACY_INPUT_HASHES',
                                       {hashlib.sha256(legacy).hexdigest()}):
                    self.assertTrue(updater.input_proxy_status(app)['known'])
                    migrated=run(prepare())
                self.assertEqual(migrated.returncode,0,(app/'rig/update/apply.log').read_text(errors='replace'))
                self.assertFalse((app/'dinput8.dll').exists())
                retired=list((app/'rig/update').glob('retired-input-*/dinput8.dll'))
                self.assertEqual(len(retired),1)
                self.assertEqual(retired[0].read_bytes(),legacy)
                (app/'dinput8.dll').write_bytes(b'unknown custom input proxy')
                with self.assertRaisesRegex(RuntimeError,'unrecognized dinput8'):
                    prepare()
                self.assertEqual((app/'dinput8.dll').read_bytes(),b'unknown custom input proxy')
