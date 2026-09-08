"""Recompute admission, sphere, input and timing evidence with the companion far archive.

Completed pixels and Zeus state comparisons remain hash-bound receipts. This
verifier needs no ROMs or third-party packages and retains both geometry FAILs.
"""
import csv,hashlib,io,json,math,sys,tempfile,zipfile
from pathlib import Path

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((root/'derived-evidence.zip').read_bytes())==manifest['archive_sha256']
parent=root.parent/manifest['companion']['directory']/'derived-evidence.zip'
assert sha(parent.read_bytes())==manifest['companion']['archive_sha256']
with zipfile.ZipFile(root/'derived-evidence.zip') as z,zipfile.ZipFile(parent) as companion:
    assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(manifest['entries'])
    for name,digest in manifest['entries'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(z.read(name))==digest,name
    read=lambda name:json.loads(z.read(name))
    def data(name):
        if name not in manifest['byte_exact_reconstructions']:return z.read(name)
        spec=manifest['byte_exact_reconstructions'][name]
        result=(companion if spec['companion'] else z).read(spec['source'])
        if spec.get('admission_column') is not None:
            column=spec['admission_column'];lines=[]
            for i,line in enumerate(result.split(b'\n')):
                if i and line:
                    parts=line.split(b',')
                    if parts[2] in (b'admission',b'admission_check'):
                        parts[column]=b'190000'+(b'\r' if parts[column].endswith(b'\r') else b'')
                    line=b','.join(parts)
                lines.append(line)
            result=b'\n'.join(lines)
        assert sha(result)==spec['sha256'],name
        return result
    def inputs(raw):
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8')));rows=list(reader)
        assert rows and all(None not in r and all(v is not None for v in r.values()) for r in rows)
        assert [int(r['frame']) for r in rows]==list(range(1,len(rows)+1))
        fields=[k for k in reader.fieldnames if k not in ('host_seconds','speed_percent')]
        return fields,[tuple(r[k] for k in fields) for r in rows],rows
    reference=inputs(companion.read('reference/frames.csv'))
    deployment=read('checks/deployment.json');ci=read('checks/ci.json')
    assert deployment['source_commit']==manifest['source_commit']==ci['headSha']
    assert ci['conclusion']=='success' and len(ci['jobs'])==4 and all(j['conclusion']=='success' for j in ci['jobs'])
    identity=read('checks/source-identity.json')
    assert identity==read('checks/source-identity-ubuntu-latest.json')==read('checks/source-identity-windows-latest.json')
    matrix=read('checks/trial-report.json');checks=read('checks/independent-checks.json')
    assert matrix['completed'] and not matrix['physical_force'] and len(matrix['trials'])==4
    assert matrix['native_sha256']==deployment['native_sha256']
    receipts=read('checks/file-receipts.json')
    with tempfile.TemporaryDirectory() as td:
        directory=Path(td)
        for name in manifest['entries']:
            if name.startswith('source/harness/'):(directory/Path(name).name).write_bytes(z.read(name))
        sys.path.insert(0,str(directory))
        from analyze_exotica_frustum import summarize as frustum
        from analyze_exotica_streaming import summarize as streaming
        def trace(prefix,name):
            dest=directory/(prefix.replace('/','_')+name);dest.write_bytes(data(prefix+name));return dest
        def runtime(prefix,frames):
            r=read(prefix+'report.json');assert not r.get('error') and r['evidence']['frames']==frames
            assert r['comparison']['input_or_time_mismatches']==0
            actual=inputs(data(prefix+'frames.csv'))
            assert actual[0]==reference[0] and actual[1]==reference[1][:frames]
            inv=read(prefix+'invocation.json')
            assert inv['executable_sha256']==deployment['native_sha256'] and inv['environment']['MIDV_FFB']=='0'
            assert sha(data(prefix+'probe.lua'))==r['probe_script']['sha256']
            return actual[2]
        runtime('control/',6000)
        assert streaming(trace('control/','exotica-streaming.csv'))==read('checks/control-streaming.json')
        for item,check in zip(matrix['trials'],checks['trials'],strict=True):
            name=item['name'];assert name==check['name'];prefix='matrix/'+name+'/'
            rows=runtime(prefix,6000)
            assert frustum(trace(prefix,'exotica-frustum.csv'))==item['frustum']
            assert streaming(trace(prefix,'exotica-streaming.csv'))==check['streaming']
            timing=check['timing'];a=rows[timing['first_frame']-1];b=rows[timing['last_frame']-1]
            ratio=(float(b['emulated_seconds'])-float(a['emulated_seconds']))/(float(b['host_seconds'])-float(a['host_seconds']))
            assert math.isclose(ratio,timing['emulation_ratio'],rel_tol=1e-12)
            caps=list(csv.DictReader(io.StringIO(data(prefix+'captures.csv').decode())))
            assert [int(r['completed_frame']) for r in caps]==list(range(4500,5991,100))
            assert all((int(r['width']),int(r['height']),int(r['dropped_messages']))==(1920,1080,0) for r in caps)
            print(name,'admission/sphere branches, inputs and timing verified',flush=True)
        for name in ('admit190','admit160-repeat'):
            assert receipts['matrix/'+name]==receipts['matrix/admit160']
            assert data('matrix/'+name+'/exotica-frustum.csv')==data('matrix/admit160/exotica-frustum.csv')
        assert data('matrix/admit160-repeat/exotica-streaming.csv')==data('matrix/admit160/exotica-streaming.csv')
        for name in ('coherent','admit160'):
            prefix='scene/'+name+'/';runtime(prefix,4703)
            assert streaming(trace(prefix,'exotica-streaming.csv'))['frames']==[4500,4700]
            assert frustum(trace(prefix,'exotica-frustum.csv'))['frames']==[4500,4700]
            caps=list(csv.DictReader(io.StringIO(data(prefix+'captures.csv').decode())))
            assert [int(r['completed_frame']) for r in caps]==[4699,4700]
            assert all((int(r['width']),int(r['height']),int(r['dropped_messages']))==(3840,2160,0) for r in caps)
    for alignment in ('frame','scene'):
        r=read('checks/scene-4700-'+alignment+'.json')
        assert r['verdict']=='FAIL' and r['resources_equal'] and not r['only_additions']
        assert r['original_records']==2831 and r['candidate_records']==2972
    changes=read('checks/scene-4700-state-deltas.json')
    assert changes['quads']==[2612,2753] and changes['identical_geometry_multiset']==2560
    assert changes['ordered_identical_geometry']==2409
    assert changes['record_sha256']==[receipts['resources-'+n]['records.bin']['sha256'] for n in ('coherent','admit160')]
    gl=read('checks/scene-4700-gl.json')
    assert not gl['passed'] and [r['changed_pixels'] for r in gl['pixel_changes']]==[367,374]
print('PASS: numerical checks recompute; strict scene/frame failures retained; GPU results remain receipts.')
