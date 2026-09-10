from pathlib import Path
import csv,hashlib,json,re,statistics
root=Path(__file__).parent;read=lambda n:json.loads((root/n).read_text(encoding='utf-8'))
for name,digest in read('manifest.json')['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
identity=read('source-identity.json');checks=read('checks.json');native=read('native-export.json');defaults=read('defaults.json')
payload=''.join(f'{k}\0{v}\n' for k,v in sorted(identity['files'].items())).encode()
assert hashlib.sha256(payload).hexdigest()==identity['sha256']==checks['source_identity']==checks['source_identity_after']==defaults['source_identity']
assert checks['passed'] and len(checks['steps'])==111 and all(s['returncode']==0 for s in checks['steps'])
assert read('unit-tests.json')==dict(passed=True,tests=317,skipped=0,errors=0,failures=0)
assert native['passed'] and native['patch_count']==164 and native['native_commit']=='ac10f2aae6e14650958f6a5ae249216b0cde1f31'
assert native['candidate_sha256']==defaults['candidate_sha256']=='9daeb048e585bda8426fc9be83cd75eb3393a4d6e5d0193e1718436a4fce23cd'
assert native['personal_sha256']=='87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'
assert defaults['passed'] and defaults['subset'] is None and len(defaults['cases'])==7 and not defaults['physical_force']
assert all(c['passed'] and c['telemetry']['passed'] for c in defaults['cases'])
assert len([c for c in defaults['cases'] if 'force_gate' in c])==4 and all(c['force_gate']['passed'] for c in defaults['cases'] if 'force_gate' in c)
cases=read('evidence.json')['cases'];assert len(cases)==9
images=verified=0
for name,case in cases.items():
    for path,data in case['reports'].items():
        r=data['receipt'];assert r.get('passed',True),path
        if path.endswith('-gl.json'):assert not r['different_frames'];images+=r['frames']
        if path.endswith('-motion.json'):assert r['adc_times_equal'] and r['camera_equal']
    for line in case['acknowledgments']:
        match=re.fullmatch(r'MIDZ_HOST_MATERIAL_PAGES_RESULT mode=2 verified=(\d+)',line)
        if match:verified+=int(match[1])
assert images==440 and verified==10204
for name in ['full-source7187-scan','full-source7187-written3','full-source7187-verify3']:
    r=cases[name]['reports'][name+'-7187-oracle.json']['receipt'];assert r['passed'] and r['original_context']['exact_context']
with (root/'staging.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
means={}
for name in ['private-material5072-on3','written5072-on3']:
    subset=[float(r['stage_us']) for r in rows if r['run']==name and int(r['generation'])>1]
    assert len(subset)==2456;means[name]=statistics.mean(subset);print(name,'mean steady staging',round(means[name],3),'us')
assert means['written5072-on3']<means['private-material5072-on3']/10
print('PASS9 trial receipts,10204 exact live scan comparisons,440 paired4K images, all7defaults and staging improvement. Raw GPU/resource/route bytes are not recomputed here.')
