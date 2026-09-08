"""Verify byte/native bindings and recompute distance counts without ROMs."""
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import tempfile
import zipfile

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda data:hashlib.sha256(data).hexdigest()
archive=root/'derived-evidence.zip'
assert sha(archive.read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==len(set(z.namelist()))
    assert set(z.namelist())==set(manifest['entries'])
    for name,digest in manifest['entries'].items():assert sha(z.read(name))==digest,name
    read=lambda name:json.loads(z.read(name))
    tree=ast.parse(z.read('source/analyze_distance_capability.py').decode('utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='summarize'
           or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROFILES' for t in n.targets)]
    namespace={'csv':csv,'math':math,'Path':Path,'sha256_file':lambda path:sha(Path(path).read_bytes())}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'archived analyzer','exec'),namespace)
    with tempfile.TemporaryDirectory() as td:
        for run in manifest['runs']:
            prefix=run['id']+'/'
            path=Path(td)/(run['id']+'.csv');path.write_bytes(z.read(prefix+'distance-capability.csv'))
            actual=namespace['summarize'](path,run['rom'])
            assert actual==read(prefix+'distance-summary.json'),run['id']
            report=read(prefix+'report.json');invocation=read(prefix+'invocation.json')
            assert report['passed']==run['passed']
            assert report['comparison']['input_or_time_mismatches']==0
            assert report['probe_script']['sha256']==sha(z.read('source/distance_capability.lua'))
            assert invocation['executable_sha256']==manifest['native_sha256']
            assert invocation['environment']['MIDV_FFB']=='0'
            if run['id']=='exotica-gl':
                assert report['gl_comparison']['passed'] and report['gl_comparison']['frames']==21
                assert report['evidence']['frames']==6000
            else:assert report['evidence']['frames']==4305
    assert z.read('exotica/distance-capability.csv')==z.read('exotica-gl/distance-capability.csv')
print('PASS: archived hashes, six native bindings, five revisions; all distance counts recompute')
