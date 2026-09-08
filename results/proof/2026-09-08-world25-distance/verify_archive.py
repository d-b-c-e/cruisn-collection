"""Recompute distance/residency counters and verify archived run bindings."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha((root/'derived-evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'derived-evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist()))
    assert set(z.namelist())==set(manifest['entries'])
    for name,digest in manifest['entries'].items():assert sha(z.read(name))==digest,name
    read=lambda name:json.loads(z.read(name))
    native=manifest['native_sha256']
    def invocation(name):
        r=read(name);assert r['executable_sha256']==native
        assert r['environment']['MIDV_FFB']=='0'
    def analyzer(name,constants=()):
        tree=ast.parse(z.read('source/'+name).decode('utf-8'))
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='summarize'
            or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
        ns={'csv':csv,'Path':Path,'sha256_file':lambda p:sha(Path(p).read_bytes()),'__doc__':ast.get_docstring(tree),
            'FAR_VALUES':(80000,100000,160000,240000),'MAXIMUM_LEAD':12}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'archived analyzer','exec'),ns)
        return ns['summarize']
    distance=analyzer('analyze_world_distance.py',('FIELDS',))
    residency=analyzer('analyze_usa_residency.py')
    trials=read('trials/report.json');assert trials['completed'] and trials['candidate_sha256']==native
    assert len(trials['trials'])==3
    with tempfile.TemporaryDirectory() as td:
        for row in trials['trials']:
            prefix='trials/'+row['name']+'/'
            path=Path(td)/'world-distance.csv';path.write_bytes(z.read(prefix+'world-distance.csv'))
            assert distance(path)==row['native_distance']
            report=read(prefix+'report.json');assert report['evidence']['frames']==6000
            assert report['comparison']['input_or_time_mismatches']==0
            assert report['passed']==(row['name']=='original')
            assert row['gl']['frames']==42 and not row['gl']['size_mismatches']
            invocation(prefix+'invocation.json')
        path=Path(td)/'usa-residency.csv';path.write_bytes(z.read('usa/usa-residency.csv'))
        assert residency(path)==read('usa/admission-summary.json')
    assert read('two-times-case/report.json')['passed']
    assert read('two-times-case/replay.json')['passed']
    assert read('two-times-repeat-gl.json')['passed']
    assert read('two-times-repeat-gl.json')['frames']==11
    for name in ('record','replay'):invocation('two-times-case/'+name+'-invocation.json')
    assert read('two-vs-three-gl.json')['passed']
    assert read('two-vs-three-native.json')['passed']
    assert not read('two-vs-three-motion.json')['passed']
    assert read('world24-existing-2x/report.json')['passed']
    invocation('world24-existing-2x/invocation.json')
    assert read('usa/report.json')['passed'];invocation('usa/invocation.json')
    controls=read('defaults/report.json')
    assert controls['passed'] and len(controls['cases'])==7 and controls['candidate_sha256']==native
    for row in controls['cases']:
        assert row['passed'];invocation('defaults/'+row['id']+'/invocation.json')
        r=read('defaults/'+row['id']+'/report.json');assert r['passed']
        if row['id']=='exotica':assert r['gl_comparison']['passed'] and r['gl_comparison']['frames']==21
    ids=[read('checks/'+name) for name in ('source-identity.json','windows-identity.json','linux-identity.json')]
    assert ids[0]==ids[1]==ids[2] and controls['source_identity']==ids[0]['sha256']
    assert ids[0]['sha256']==manifest['source_identity']
    assert read('checks/ci.json')['conclusion']=='success'
    assert len(read('checks/ci.json')['jobs'])==4
    assert all(j['conclusion']=='success' for j in read('checks/ci.json')['jobs'])
    assert read('checks/export.json')['passed'] and read('checks/export.json')['patches']==125
    assert read('checks/native-vectors.json')['passed']
print('PASS: native/source bindings, seven defaults, three distance trials and USA admission counts')
