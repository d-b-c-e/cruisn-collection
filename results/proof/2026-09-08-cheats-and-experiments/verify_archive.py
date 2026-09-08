"""Check archived bytes/bindings and recompute timer effects without ROMs."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
archive=root/'derived-evidence.zip'
assert sha(archive.read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==len(set(z.namelist()))
    assert set(z.namelist())==set(manifest['entries'])
    for name,digest in manifest['entries'].items():assert sha(z.read(name))==digest,name
    read=lambda name:json.loads(z.read(name))
    controls=read('default-controls.json')
    assert controls['candidate_sha256']==manifest['native_sha256']
    assert len(controls['cases'])==7 and all(r['passed'] for r in controls['cases'])
    assert not read('defaults/initial-report.json')['passed']
    assert read('defaults/exotica-4k-report.json')['passed']
    replay=read('defaults/exotica-4k-replay.json')
    assert replay['gl_comparison']['passed'] and replay['gl_comparison']['frames']==21
    assert replay['display_target']['reference_size']==[3840,2160]
    for row in controls['cases']:
        invocation=read('defaults/'+row['id']+'-invocation.json')
        assert invocation['executable_sha256']==manifest['native_sha256']
        assert invocation['environment']['MIDV_FFB']=='0'
    # Execute only the archived pure analysis function, not its CLI/launcher.
    source=ast.parse(z.read('source/check_cheats.py').decode())
    function=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='inspect')
    namespace={'csv':csv,'Path':Path,'sha256_file':lambda path:sha(Path(path).read_bytes())}
    exec(compile(ast.Module(body=[function],type_ignores=[]),'archived timer analyzer','exec'),namespace)
    summary=read('timer-effects.json')
    assert summary['candidate_sha256']==manifest['native_sha256'] and len(summary['cases'])==5
    with tempfile.TemporaryDirectory() as td:
        for row in summary['cases']:
            rom=row['rom'];path=Path(td)/rom;path.mkdir()
            (path/'cheat-probe.csv').write_bytes(z.read('timers/'+rom+'/cheat-probe.csv'))
            actual=namespace['inspect'](path,rom)
            assert json.loads(json.dumps(actual))==row['timer'],rom
            assert read('timers/'+rom+'/invocation.json')['executable_sha256']==manifest['native_sha256']
            report=read('replays/'+rom+'/report.json');assert report['passed'] and report['evidence']['frames']==4000
            assert read('replays/'+rom+'/invocation.json')['executable_sha256']==manifest['native_sha256']
            for name in ('events.csv','selection.json'):
                assert report['evidence']['cheats'][name]==sha(z.read('replays/'+rom+'/'+name))
    frozen=read('frozen/report.json')
    assert frozen['passed'] and len(frozen['games'])==5 and len(frozen['pages'])==9
    assert frozen['games'][-1]['cheat_enabled'] and frozen['support']['passed']
    assert frozen['package']['package_sha256']==manifest['dev_package_sha256']
    assert read('checks/ci.json')['conclusion']=='success'
print('PASS: 75 archived files, native bindings, five recomputed timer effects; no ROMs required')
