"""Recompute Exotica far/pose/input/timing evidence without ROMs or third-party packages.

GPU images, captured resources and occlusion queries are hash-bound receipts;
their pixels/rasterization are not recomputed by this standard-library verifier.
"""
import csv,hashlib,io,json,math,sys,tempfile,zipfile
from pathlib import Path

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((root/'derived-evidence.zip').read_bytes())==manifest['archive_sha256']
with zipfile.ZipFile(root/'derived-evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['entries'])
    for name,digest in manifest['entries'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(z.read(name))==digest,name
    read=lambda name:json.loads(z.read(name))
    def inputs(name):
        reader=csv.DictReader(io.StringIO(z.read(name).decode('utf-8')));rows=list(reader)
        assert rows and all(None not in r and all(v is not None for v in r.values()) for r in rows)
        assert [int(r['frame']) for r in rows]==list(range(1,len(rows)+1))
        fields=[k for k in reader.fieldnames if k not in ('host_seconds','speed_percent')]
        return fields,[tuple(r[k] for k in fields) for r in rows],rows
    reference=inputs('reference/frames.csv')
    deployment=read('checks/deployment.json');matrix=read('matrix/report.json')
    assert matrix['completed'] and len(matrix['trials'])==5 and not matrix['physical_force']
    assert matrix['candidate_sha256']==deployment['native_sha256']
    assert deployment['source_commit']==manifest['source_commit']
    ci=read('checks/ci.json')
    assert ci['headSha']==manifest['source_commit'] and ci['conclusion']=='success'
    assert len(ci['jobs'])==4 and all(j['conclusion']=='success' for j in ci['jobs'])
    identity=read('checks/source-identity.json')
    assert identity==read('checks/source-identity-ubuntu-latest.json')==read('checks/source-identity-windows-latest.json')
    receipts=read('checks/file-receipts.json')
    with tempfile.TemporaryDirectory() as td:
        directory=Path(td)
        for name in manifest['entries']:
            if name.startswith('source/harness/'):
                dest=directory/Path(name).name;dest.write_bytes(z.read(name))
        sys.path.insert(0,str(directory))
        from analyze_exotica_frustum import summarize
        from compare_exotica_distance import compare
        traces={}
        for item in matrix['trials']:
            name=item['name'];prefix='matrix/'+name+'/'
            if name in manifest['byte_exact_reconstructions']:
                spec=manifest['byte_exact_reconstructions'][name];data=z.read(spec['source'])
                if spec['far_column'] is not None:
                    index=spec['far_column'];value=spec['far_value'].encode()
                    data=b'\n'.join(b','.join(line.split(b',')[:index]+[value]+line.split(b',')[index+1:])
                        if i and line else line for i,line in enumerate(data.split(b'\n')))
                assert len(data)==spec['size'] and sha(data)==spec['sha256']
            else:data=z.read(prefix+'exotica-frustum.csv')
            trace=directory/(name+'.csv');trace.write_bytes(data);traces[name]=trace
            assert summarize(trace)==item['frustum']
            report=read(prefix+'report.json');assert not report.get('error') and report['evidence']['frames']==6000
            assert report['comparison']['input_or_time_mismatches']==0
            actual=inputs(prefix+'frames.csv');assert actual[:2]==reference[:2]
            inv=read(prefix+'invocation.json')
            assert inv['executable_sha256']==deployment['native_sha256'] and inv['environment']['MIDV_FFB']=='0'
            assert sha(z.read(prefix+'probe.lua'))==item['probe_sha256']==report['probe_script']['sha256']
            timing=item['timing'];a=actual[2][timing['first_frame']-1];b=actual[2][timing['last_frame']-1]
            ratio=(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
            assert math.isclose(ratio,timing['emulation_ratio'],rel_tol=1e-12)
            captures=list(csv.DictReader(io.StringIO(z.read(prefix+'captures.csv').decode())))
            assert [int(r['completed_frame']) for r in captures]==list(range(4500,5991,100))
            assert all((int(r['width']),int(r['height']),int(r['dropped_messages']))==(1920,1080,0) for r in captures)
            if name in ('far2','far3','far2-repeat'):
                comparison=compare(traces['coherent'],trace)
                assert json.loads(json.dumps(comparison))==read('checks/pose-coherent-'+name+'.json')
                assert comparison['passed'] and comparison['additions_at_equal_pose']==3035
                assert receipts['matrix/'+name]==receipts['matrix/coherent']
            print(name,'branches, inputs and timing verified',flush=True)
        assert traces['far2'].read_bytes()==traces['far2-repeat'].read_bytes()
    strict=read('checks/scene-4864-geometry.json');aligned=read('checks/scene-4864-aligned.json')
    assert strict['verdict']=='FAIL' and aligned['verdict']=='PASS'
    assert aligned['equal_records']==aligned['original_records']==2606
    assert aligned['candidate_records']==2813 and len(aligned['ignored_frame_changes'])==438
    assert aligned['resources_equal'] and aligned['only_additions']
    assert receipts['scene/coherent']==receipts['scene/far2']
    for name,depth in [('scene-4864-occlusion.json',1),('scene-4864-occlusion-depth2.json',2)]:
        r=read('checks/'+name);assert r['depth_scale']==depth
        assert r['quads']==199 and r['visible_samples']==0 and r['unoccluded_samples']==173
        assert r['records_sha256']==receipts['scene-resources']['far2']['records.bin']['sha256']
        assert r['wave_sha256']==receipts['scene-resources']['far2']['waveram.bin']['sha256']
        assert sum(x['visible_samples'] for x in r['items'])==r['visible_samples']
        assert sum(x['unoccluded_samples'] for x in r['items'])==r['unoccluded_samples']
print('PASS: archived numerical evidence recomputes; strict timing failure retained; GPU results remain receipts.')
