import importlib.util
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
