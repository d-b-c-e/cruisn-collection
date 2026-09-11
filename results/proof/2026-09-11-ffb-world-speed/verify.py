"""Verify source and receipt consistency; raw game execution remains external."""
from pathlib import Path
import hashlib
import json
import math
import sys

here=Path(__file__).resolve().parent
root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes

def read(name):return json.loads((here/name).read_text())
def require(value,why):
    if not value:raise ValueError(why)

manifest=read('manifest.json')
require(manifest['schema']==1,'schema')
for name,digest in manifest['files'].items():
    require(Path(name).name==name,'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt digest: '+name)
for name,digest in read('source.json').items():
    path=(root/name).resolve()
    require(path.is_relative_to(root),'source path')
    require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source digest: '+name)
speed=read('speed.json');independent=read('independent-memory.json')
require(speed['passed'] and not speed['normalization_accepted'] and not speed['physical_force'],'speed scope')
require(speed['producer_events']==3486 and speed['matched_hud_reads']==3656 and speed['uncaptured_writer_reads']==126,
        'producer/consumer coverage')
require(speed['hud_reads']==speed['matched_hud_reads']+speed['uncaptured_writer_reads'],'HUD partition')
require(speed['snapshot_samples']==8270 and speed['available_speed_samples']==6838,'frame coverage')
require(speed['mph_factor']==independent['conversion_multiplier']==.489990234375,'exact conversion operand')
require(independent['producer_conversion_mismatches']==0 and independent['independent_original_memory_matches']==8270,
        'independent old memory receipt')
replay=read('replay.json')
require(replay['passed'] and replay['comparison']['passed'] and replay['frames']==9269 and replay['snapshots']==154,
        'full original route/snapshots receipt')
require(replay['physical_ffb']=='0','physical output')
for pair in replay['unchanged_traces'].values():require(len(pair)==2 and pair[0]==pair[1],'unchanged trace hashes')
conditions=read('conditions.json')
require(conditions['passed'] and not conditions['selection']['allow_ocr'] and conditions['selection']['world_speed_probe'],
        'numeric/memory-only selection')
require(not conditions['normalization_accepted'] and not conditions['contacts_reviewed'],'calibration remains open')
require(len({g['executable_sha256'] for g in conditions['games'].values()})==1,'common native source')
require(conditions['games']['world']['world_memory_speed_evidence']==speed,'same verified World source')
for game in conditions['games'].values():
    c=game['coverage']
    require(math.isclose(c['seconds'],game['selected']['seconds']+sum(c['excluded_seconds'].values()),abs_tol=1e-8),
            'coverage duration partition')
require(set(conditions['common_bins'])=={'40-60mps/center/steady','40-60mps/negative-medium/slow'},'shared conditions')
require(math.isclose(conditions['games']['world']['selected']['seconds'],117.248395,abs_tol=1e-6),'World selected duration')
checks=read('python-checks.json')
require(checks['passed'] and checks['source_identity']==checks['source_identity_after'],'unchanged tested source')
require(checks['groups']==['python'] and checks['tests']==dict(passed=True,tests=383,skipped=0,failures=0,errors=0),
        'Python test receipt')
print('PASS source/hash/receipt consistency; raw replay, HUD execution and physical calibration remain external evidence')
