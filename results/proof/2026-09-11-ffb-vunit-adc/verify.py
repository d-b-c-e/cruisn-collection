"""Validate code and aggregate receipts; does not rerun private game captures."""
from pathlib import Path
import hashlib
import json
import re
import sys

here=Path(__file__).resolve().parent
root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes


def read(name):return json.loads((here/name).read_text())
def require(value,message):
    if not value:raise ValueError(message)


manifest=read('manifest.json')
require(manifest['schema']==1,'manifest schema')
for name,digest in manifest['files'].items():
    require(Path(name).name==name,'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt digest '+name)
for name,digest in read('source.json').items():
    path=(root/name).resolve();require(path.is_relative_to(root),'source path')
    require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source digest '+name)
for game,frames in (('usa',5012),('world',9269),('offroad',9644)):
    p=read(game+'.json');i=p['input_verification'];c=p['counts'];r=p['replay']
    require(p['passed'] and i['passed'] and r['comparison']['passed'],'acceptance')
    require(not p['normalization_accepted'] and not p['physical_angle_verified']
            and not p['conversion_callback_observed'] and p['conversion_schedule_reconstructed'],'scope')
    require(p['conversion_delay_microseconds']==40,'conversion contract')
    require(i['frames']==frames and r['frames']==frames and i['inp_frames']==frames+1,'full input lifetime')
    require(r['comparison']['input_or_time_mismatches']==r['comparison']['pixel_mismatches']==0,'original replay')
    require(i['executable_sha256']=='97cd738c6b89f59a7523c9494285c5ee625e9f5041622f542983d94173b37d7a','common native')
    require(sum(c[k] for k in ('C','W','R'))<=p['collector_event_limit'],'collector bound')
    require(p['collector_event_limit']==(196608 if game=='offroad' else 131072),'collector version')
    require(0<p['steering_conversions_read']<=c['steering_reads']<=c['R'],'steering coverage')
    require(sum(p['steering_consumer_pcs'].values())==c['steering_reads'],'consumer count')
    require({'force-source.csv','force-gate.csv','signals.csv'}<=set(r['unchanged_force_and_telemetry']),'unchanged force evidence')
    require(all(re.fullmatch('[0-9a-f]{64}',s) for s in p['evidence_sha256'].values()),'trace digests')
checks=read('python-checks.json')
require(checks['passed'] and checks['groups']==['python']
        and checks['source_identity']==checks['source_identity_after'],'tested source')
require(checks['tests']==dict(passed=True,tests=405,skipped=0,failures=0,errors=0),'test receipt')
failure=read('retained-failures.json')
require(not failure['usa_analysis']['passed'] and not failure['offroad_capture']['complete'],'retained failures')
require(failure['offroad_capture']['rows']==131073 and failure['offroad_failed_csv_bytes']==6826795,'old bounded capture')
print('PASS code/hash/aggregate receipt consistency; raw game execution and wheel acceptance are separate')
