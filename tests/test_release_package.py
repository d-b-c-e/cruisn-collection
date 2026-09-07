from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from check_release_package import inspect,REQUIRED,FREEPLAY


class PackageTests(unittest.TestCase):
    def test_missing_runtime_wrong_binary_and_personal_data_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);exe=root/'candidate.exe';exe.write_bytes(b'candidate')
            files={n:b'fixture' for n in REQUIRED};files['vunit.exe']=b'candidate'
            for rom,(filename,addresses) in FREEPLAY.items():
                data=bytearray(max(addresses)+1)
                for a in addresses:data[a]=1
                files[f'fixtures/nvram-{rom}/{filename}']=data
            def check(changes):
                payload=dict(files);payload.update(changes)
                with zipfile.ZipFile(root/'package.zip','w') as z:
                    for name,data in payload.items():
                        if data is not None:z.writestr('CruisnCollection/'+name,data)
                return inspect(root/'package.zip',exe)
            self.assertTrue(check({})['passed'])
            for bad in ({'SDL2.dll':None},{'vunit.exe':b'wrong'},{'rig/collection.ini':b'personal'},
                        {'roms/game.zip':b'rom'},{'../outside':b'bad'}, {'dinput8.dll':b'old plugin'},
                        {'fixtures/nvram-crusnexo/m48t35':bytes(0x74)}):
                with self.assertRaises(ValueError):check(bad)
