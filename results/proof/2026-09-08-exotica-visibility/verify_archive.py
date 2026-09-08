"""Recompute Exotica visibility conclusions from derived data, without ROMs or GL."""
from collections import Counter
import csv,difflib,hashlib,io,json,sys,tempfile,zipfile
from pathlib import Path

root=Path(__file__).resolve().parent
m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
sha=lambda data:hashlib.sha256(data).hexdigest()
data={}
for archive,description in m['archives'].items():
    assert sha((root/archive).read_bytes())==description['sha256']
    with zipfile.ZipFile(root/archive) as z:
        assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(description['entries'])
        for name,digest in description['entries'].items():
            payload=z.read(name);assert sha(payload)==digest,name
            assert name not in data;data[name]=payload
read=lambda name:json.loads(data[name])

baseline=root/m['baseline_archive'];assert sha(baseline.read_bytes())==m['baseline_archive_sha256']
with zipfile.ZipFile(baseline) as z:lines=z.read('trace.csv').splitlines()
stock=b'\r\n'.join([lines[0]+b',original_factor,reciprocal,margin']+
    [r+b','+r.split(b',')[13]+b',0,0' for r in lines[1:]])+b'\r\n'
assert sha(stock)==read('checks/stock-reconstruction.json')['sha256']

def inputs(name):
    reader=csv.DictReader(io.StringIO(data[name].decode('utf-8')))
    fields=[k for k in reader.fieldnames if k not in ('host_seconds','speed_percent')]
    rows=[tuple(r[k] for k in fields) for r in reader]
    assert [int(r[0]) for r in rows]==list(range(1,len(rows)+1))
    return fields,rows

reference=inputs('reference/frames.csv')
def invocation(prefix,native):
    r=read(prefix+'invocation.json')
    assert r['executable_sha256']==native and r['environment']['MIDV_FFB']=='0'
    assert r['returncode']==0 and not r['error']
    return r

def completed(prefix,native,frames=6000,report_name='report.json'):
    r=read(prefix+report_name)
    assert r['evidence']['frames']==frames and not r.get('error')
    assert r['comparison']['input_or_time_mismatches']==0
    assert inputs(prefix+'frames.csv')==(reference[0],reference[1][:frames])
    invocation(prefix,native)
    return r

with tempfile.TemporaryDirectory() as td:
    p=Path(td)
    for name,payload in data.items():
        if name.startswith('source/') and name.endswith('.py'):(p/Path(name).name).write_bytes(payload)
    sys.path.insert(0,td)
    from analyze_exotica_frustum import summarize
    from compare_exotica_visibility import compare
    from analyze_exotica_visibility import summarize as native_summary
    (p/'stock.csv').write_bytes(stock)
    trials=read('lua/report.json');assert trials['completed']
    assert trials['candidate_sha256']==m['lua_native_sha256']
    summaries={}
    for row in trials['trials']:
        name=row['name'];path=p/(name+'.csv')
        path.write_bytes(stock if name=='stock' else data[('both' if name=='both-repeat' else name)+'.csv'])
        actual=summarize(path);assert actual==row['frustum'],name;summaries[name]=actual
        prefix='lua/'+name+'/'
        r=completed(prefix,m['lua_native_sha256'])
        assert r['probe_script']['sha256']==sha(data[prefix+'probe.lua'])==row['probe_sha256']
        assert row['gl']['frames']==19 and not row['gl']['size_mismatches']
        if name in ('reciprocal','margins','both'):
            result=compare(p/'stock.csv',path)
            assert result==read('checks/'+name+'-pose.json')
            assert not result['passed'] and not result['prediction_errors'] and not result['losses_at_equal_pose']
    assert summaries['both']['source_sha256']==summaries['both-repeat']['source_sha256']
    assert trials['trials'][-1]['repeat_gl']['passed'] and trials['trials'][-1]['repeat_frustum']
    for name in ('stock','margins','projection','both','both-repeat'):
        prefix='native/'+name+'/'
        r=completed(prefix,m['native_sha256'])
        path=p/(name+'-native.csv');path.write_bytes(data[prefix+'exotica-visibility.csv'])
        assert native_summary(path,6000)==read(prefix+'counters.json')
        assert read(prefix+'timing.json')['emulation_ratio']>=.99
        if name=='stock':assert r['gl_comparison']['passed'] and r['gl_comparison']['frames']==21
    assert data['native/both/exotica-visibility.csv']==data['native/both-repeat/exotica-visibility.csv']
    assert read('checks/native-repeat-gl.json')['passed']
    for name in ('margins','projection','both'):assert read('checks/lua-native-'+name+'-gl.json')['passed']
    for name in ('margins','both'):
        prefix='cases/'+name+'/'
        case=read(prefix+'case.json');r=read(prefix+'report.json');rr=read(prefix+'replay-report.json')
        assert r['passed'] and r['identity_replay_passed'] and rr['passed']
        assert len(r['expected_gl_frames'])==35 and rr['gl_comparison']['passed'] and rr['gl_comparison']['frames']==35
        assert case['settings']['MIDZ_VISIBILITY']==name and case['dependencies']['vunit.exe']==m['native_sha256']
        assert not case['attended_ffb'] and case['evidence']['frames']==6000
        for stage in ('record','replay'):
            invocation(prefix+stage+'/',m['native_sha256'])
            assert inputs(prefix+stage+'/frames.csv')==reference
            path=p/(name+'-'+stage+'.csv');path.write_bytes(data[prefix+stage+'/exotica-visibility.csv'])
            assert native_summary(path,6000)==read(prefix+stage+'-counters.json')
        assert data[prefix+'record/exotica-visibility.csv']==data[prefix+'replay/exotica-visibility.csv']

for name in ('stock','margins','both'):
    r=completed('scene/'+name+'/',m['lua_native_sha256'],3503)
    assert r['zeus_capture']['requested_frame']==3500
    assert r['probe_script']['sha256']==sha(data['scene/'+name+'/probe.lua'])
for name,expected in (('margins',True),('both',False)):
    r=read('checks/scene-'+name+'-geometry.json')
    original=[tuple(s) for s in r['reference_signatures']];candidate=[tuple(s) for s in r['candidate_signatures']]
    ops=difflib.SequenceMatcher(a=original,b=candidate,autojunk=False).get_opcodes()
    edits=[dict(operation=op,reference=[a,b],candidate=[c,d]) for op,a,b,c,d in ops if op!='equal']
    assert edits==r['edits'] and all(e['operation']=='insert' for e in edits)==expected
    assert r['resources_equal'] and (r['verdict']=='PASS')==expected
    for resource in ('waveram.bin','pal_table.bin'):
        assert r['reference']['sha256'][resource]==r['candidate']['sha256'][resource]
    if expected:
        assert r['equal_records']==r['original_records']==3691 and r['candidate_records']==3693
        assert len(r['changed_candidate_quads'])==1
        assert all(x>511 for x,y in r['changed_candidate_quads'][0]['xy'])

reg=read('regressions/report.json');assert reg['passed'] and len(reg['cases'])==7
assert reg['source_identity']==read('checks/source-identity.json')['sha256']
for row in reg['cases']:
    assert row['passed']
    prefix='regressions/'+row['id']+'/'
    r=read(prefix+'report.json');assert r['passed'] and not r.get('error')
    invocation(prefix,m['native_sha256'])
    assert inputs(prefix+'frames.csv')==inputs(prefix+'reference-frames.csv')
    assert not r['comparison']['input_or_time_mismatches'] and not r['comparison']['pixel_mismatches']
    if row['id']=='exotica':assert r['gl_comparison']['passed'] and r['gl_comparison']['frames']==21
for name in ('ci-code','ci-menu'):
    ci=read('checks/'+name+'.json')
    assert ci['conclusion']=='success' and len(ci['jobs'])==4 and all(j['conclusion']=='success' for j in ci['jobs'])
assert 'Ran 157 tests' in data['checks/tests-menu.log'].decode('utf-8-sig')
assert read('checks/export.json')['commit']==m['native_commit'] and read('checks/export.json')['passed']
deployment=read('checks/deployment.json')
assert deployment['native_sha256']==m['native_sha256'] and deployment['native_commit']==m['native_commit']
assert deployment['release_tag']=='c098290aeaa1f19ca37d7bee56c747cbf51350b5'
assert deployment['release_zip_sha256']=='fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a'
print('PASS: all Lua decisions/pose failures, native counters, recorded inputs, candidate repeats, geometry hashes and bound GL/CI/regression receipts')
