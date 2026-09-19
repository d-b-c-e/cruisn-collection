from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from check_release_package import inspect,REQUIRED,FREEPLAY,MEDIA


class PackageTests(unittest.TestCase):
    def test_missing_runtime_wrong_binary_and_personal_data_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);exe=root/'candidate.exe';exe.write_bytes(b'candidate')
            files={n:b'fixture' for n in REQUIRED+MEDIA};files['vunit.exe']=b'candidate'
            for rom,(filename,addresses) in FREEPLAY.items():
                data=bytearray(max(addresses)+1)
                if rom=='offroadc':
                    data=bytearray(0x8000);data[0x37c]=0x12
                for a in addresses:data[a]=1
                if rom=='offroadc':
                    from cmos_settings import set_bytes
                    data=set_bytes(data,rom,filename,addresses,1)
                files[f'fixtures/nvram-{rom}/{filename}']=data
            def check(changes):
                payload=dict(files);payload.update(changes)
                with zipfile.ZipFile(root/'package.zip','w') as z:
                    for name,data in payload.items():
                        if data is not None:z.writestr('CruisnCollection/'+name,data)
                return inspect(root/'package.zip',exe)
            self.assertTrue(check({})['passed'])
            source = dict(schema=1, executable_sha256=hashlib.sha256(b'candidate').hexdigest(),
                          native_commit='a'*40, native_tree='b'*40,
                          patch_sha256=hashlib.sha256(files['patch/vunit-poc-patches.patch']).hexdigest(),
                          build_log_sha256='d'*64)
            from control_launch import FEATURES
            capability = json.dumps(dict(version=1, sha256=source['executable_sha256'],
                                   native_commit=source['native_commit'], features=sorted(FEATURES))).encode('utf-8')
            native = {'vunit.exe.build.json': json.dumps(source).encode('utf-8'),
                      'vunit.exe.features.json': capability}
            Path(str(exe)+'.features.json').write_bytes(capability)
            self.assertTrue(check(native)['passed'])
            for invalid in ({'vunit.exe.features.json': None},
                            {'vunit.exe.features.json': b'[]'},
                            {'vunit.exe.features.json': b'{}'},
                            {'vunit.exe.build.json': None},
                            {'patch/vunit-poc-patches.patch': b'wrong renderer lineage'}):
                with self.assertRaises(ValueError):
                    check({**native, **invalid})
            Path(str(exe)+'.features.json').unlink()
            invalid_sum = bytearray(files['fixtures/nvram-offroadc/nvram'])
            invalid_sum[0x35c] ^= 1
            with self.assertRaisesRegex(ValueError, 'checksum'):
                check({'fixtures/nvram-offroadc/nvram':invalid_sum})
            for bad in ({'SDL2.dll':None},{'vunit.exe':b'wrong'},{'rig/collection.ini':b'personal'},
                        {'audio/menumusic.mp3':None},{'bgfx/chains/crt-geom-deluxe.json':None},
                        {'source/harness/__pycache__/private.pyc':b'stale'},
                        {'roms/game.zip':b'rom'}, {'collection.ini':b'personal'},
                        {'force-profiles.user.ini':b'personal'}, {'source/harness/collection.ini':b'personal'},
                        {'control-calibration.txt':b'personal'}, {'ffb-user-stopped':b'owner off marker'},
                        {'cfg/crusnusa.cfg':b'bindings'}, {'cheats/settings.json':b'personal'},{'../outside':b'bad'}, {'dinput8.dll':b'old plugin'},
                        {'fixtures/nvram-crusnexo/m48t35':bytes(0x74)},
                        {'fixtures/nvram-offroadc/nvram':bytes(0x8000)}):
                with self.assertRaises(ValueError):check(bad)
