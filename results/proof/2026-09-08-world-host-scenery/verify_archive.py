"""Recompute CPU/input/force evidence and selected completed pixels without ROMs.

Requires Pillow for the archived full-resolution images. Model reconstruction and
uncaptured GPU/resource comparisons remain hash-bound receipts, not rerenders.
"""
import csv,hashlib,io,itertools,json,math,sys,tempfile,zipfile
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((root/'derived-evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'derived-evidence.zip') as z, tempfile.TemporaryDirectory() as td:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['entries'])
    for name,digest in manifest['entries'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(z.read(name))==digest,name
    read=lambda name:json.loads(z.read(name))
    table=lambda name:list(csv.DictReader(io.StringIO(z.read(name).decode())))
    work=Path(td)
    for name in manifest['entries']:
        if name.startswith('source/') and name.endswith('.py'):(work/Path(name).name).write_bytes(z.read(name))
    sys.path.insert(0,str(work))
    from analyze_world_host import scene_summary
    from analyze_drivetrain import analyze as drivetrain
    from analyze_force_gate import analyze as force
    from verify_world_sections import check as sections
    from verify_world_sections_v1 import check as sections_v1
    from verification import image_signature
    def extract(prefix):
        directory=work/prefix;directory.mkdir(parents=True,exist_ok=True)
        for name in manifest['entries']:
            if name.startswith(prefix+'/') and '/' not in name[len(prefix)+1:]:
                (directory/Path(name).name).write_bytes(z.read(name))
        return directory
    def inputs(path):
        rows=table(path);assert rows
        assert [int(r['frame']) for r in rows]==list(range(1,len(rows)+1))
        keys=[k for k in rows[0] if k not in ('host_seconds','speed_percent')]
        return keys,[tuple(r[k] for k in keys) for r in rows]
    def runtime(prefix,reference='reference/frames.csv'):
        report=read(prefix+'/report.json');inv=read(prefix+'/invocation.json')
        assert report['passed'] and report['comparison']['passed']
        assert not inv['error'] and inv['returncode']==0 and inv['environment']['MIDV_FFB']=='0'
        actual=inputs(prefix+'/frames.csv');expected=inputs(reference)
        assert actual[0]==expected[0] and actual[1]==expected[1][:len(actual[1])]
        assert len(actual[1])==report['evidence']['frames']
        assert sha(z.read(prefix+'/probe.lua'))==report['probe_script']['sha256']
        if prefix+'/captures.csv' in manifest['entries']:
            captures=table(prefix+'/captures.csv');frames=[int(r['completed_frame']) for r in captures]
            assert frames==sorted(set(frames))
            assert all(r['completed_frame']==r['last_received_frame'] and int(r['dropped_messages'])==0 for r in captures)
            assert frames==report['evidence']['gl_captures']['completed_frames']
        return report
    ci=read('checks/ci-final/report.json');identity=read('checks/ci-final/local-source-identity.json')
    assert ci['headSha']==manifest['source_commit'] and ci['conclusion']=='success'
    assert len(ci['jobs'])==4 and all(j['conclusion']=='success' for j in ci['jobs'])
    assert identity==read('checks/ci-final/windows/source-identity.json')==read('checks/ci-final/linux/source-identity.json')
    deployment=read('checks/deployment.json');native=read('checks/native-final-build-identity.json')
    assert deployment['native_sha256']==native['native_sha256']
    assert deployment['source_commit']==ci['headSha']
    names=['native-full-observe-4k','native-full-draw80-4k','native-full-draw160-4k',
           'native-full-draw240-4k','native-full-draw160-repeat-4k','native-draw160-oracle-4k',
           'native-observe-v1','native-draw-v1','native-draw-v2',
           'native-draw160-dense3-4k','native-draw240-dense3-4k']
    for name in names:
        report=runtime(name);summary=scene_summary(extract(name))
        if name.startswith('native-full-'):
            assert report['evidence']['frames']==9269 and summary['scenes']==3731
        if name in ('native-full-draw240-4k','native-full-draw160-repeat-4k','native-draw160-oracle-4k'):
            assert read(name+'/invocation.json')['executable_sha256']==native['native_sha256']
        print(name,'inputs, scene counts and clocks verified',flush=True)
    def gl(prefix):
        report=read(prefix+'/report.json')['evidence']['gl_captures']
        return {int(r['completed_frame']):report['files'][r['file']] for r in table(prefix+'/captures.csv')}
    for check,a,b in [('full80-check','native-full-observe-4k','native-full-draw80-4k'),
                      ('full160-check','native-full-draw80-4k','native-full-draw160-4k'),
                      ('full160-repeat-check','native-full-draw160-4k','native-full-draw160-repeat-4k'),
                      ('full240-equality','native-full-draw160-4k','native-full-draw240-4k'),
                      ('triple-dense-check','native-draw160-dense3-4k','native-draw240-dense3-4k')]:
        saved=read('checks/'+check+'.json')
        assert all(z.read(a+'/'+f)==z.read(b+'/'+f) for f in ('world-camera.csv','world-adc.csv'))
        aa,bb=gl(a),gl(b);assert aa.keys()==bb.keys()
        different=[n for n in aa if aa[n]!=bb[n]]
        assert different==saved['gl']['different_frames']
        assert not saved['gl']['size_mismatches']
    assert z.read('native-full-draw160-4k/world-host-quads.csv')==z.read('native-full-draw160-repeat-4k/world-host-quads.csv')
    assert z.read('native-full-observe-4k/world-host-quads.csv')==z.read('native-full-draw80-4k/world-host-quads.csv')
    def groups(prefix):
        reader=csv.reader(io.StringIO(z.read(prefix+'/world-host-quads.csv').decode()));next(reader)
        for key,rows in itertools.groupby(reader,lambda r:(r[0],r[1])):yield key,[tuple(r) for r in rows]
    added=removed=0
    for (ka,a),(kb,b) in zip(groups('native-full-draw160-4k'),groups('native-full-draw240-4k'),strict=True):
        assert ka==kb;added+=sum((Counter(b)-Counter(a)).values());removed+=sum((Counter(a)-Counter(b)).values())
        it=iter(b);assert all(any(v==old for v in it) for old in a)
    assert (added,removed)==(132,0)
    assert not read('checks/full240-check.json')['passed']  # rejected assumption of sampled extra visibility
    for name in manifest['entries']:
        if name.startswith('images/native-full-'):
            _,run,file=name.split('/');path=work/file;path.write_bytes(z.read(name))
            assert image_signature(path)==gl(run)[int(Path(file).stem)]
    resources=read('checks/resource-checks.json');assert resources['passed']
    assert read('checks/native-draw160-oracle-4k/host-quad-oracle.json')['passed']
    assert read('checks/native-draw160-oracle-4k/transform-report.json')['passed']
    section=extract('section-v1');runtime('section-v1')
    assert sections_v1(section/'world-section-placement.jsonl')==read('checks/section-v1/placement-report.json')
    section=extract('section-v2');runtime('section-v2')
    assert sections(section/'world-section-placement.jsonl',True)==read('checks/section-v2/placement-report.json')
    defaults=read('defaults/report.json');plan=read('defaults/suite.json')
    assert defaults['passed'] and len(defaults['cases'])==7 and not defaults['physical_force']
    original_identity=read('checks/default-source-identity.json');delta=read('checks/default-source-delta.json')
    assert defaults['candidate_sha256']==native['native_sha256'] and defaults['source_identity']==original_identity['sha256']
    changes=sorted(k for k in set(identity['files'])|set(original_identity['files'])
                   if identity['files'].get(k)!=original_identity['files'].get(k))
    assert changes==delta['changed_files']==['fixtures/scenery/world-yaw-vectors.json',
        'harness/verify_world_sections.py','lua/world_section_capture.lua','tests/test_world_host_scenery.py']
    assert delta['old_sha256']==original_identity['sha256'] and delta['new_sha256']==identity['sha256']
    assert all(c['telemetry']['probe'] not in changes for c in plan['cases'])
    for case,item in zip(plan['cases'],defaults['cases'],strict=True):
        prefix='defaults/'+case['id'];directory=extract(prefix);runtime(prefix,prefix+'/reference-frames.csv')
        assert read(prefix+'/invocation.json')['environment'].get('MIDV_WORLD_HOST_SCENERY','0')=='0'
        t=case['telemetry'];actual=drivetrain(directory,directory/t['memory'])
        expected=dict(item['telemetry']);assert expected.pop('coverage_passed')
        assert actual==expected and actual['passed']
        if t.get('force_gate_game'):
            assert force(directory,directory/t['memory'],t['force_gate_game'],t.get('force_gate_policy','driving'),t.get('force_polarity',False))==item['force_gate']
        print(case['id'],'default inputs/UDP/memory/force verified',flush=True)
print('PASS: derived numerical checks and selected image pixels recompute; model/other GPU/resource results remain receipts.')
