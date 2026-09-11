"""Verify source and receipt consistency, not raw execution or force acceptance."""
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
def require(condition,message):
    if not condition:raise ValueError(message)

manifest=read('manifest.json')
require(manifest['schema']==1,'manifest schema')
for name,digest in manifest['files'].items():
    require(Path(name).name==name,'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt digest: '+name)
for name,digest in read('source.json').items():
    path=(root/name).resolve()
    require(path.is_relative_to(root),'source path')
    require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source digest: '+name)
checks=read('python-checks.json')
require(checks['source_identity']==checks['source_identity_after'],'changed source during tests')
require(checks['groups']==['python'] and checks['tests']==dict(errors=0,failures=0,passed=True,skipped=0,tests=368),
        'Python test receipt')
reports=[read('strict.json'),read('exploratory-ocr.json')]
for r in reports:
    require(r['passed'] and not r['normalization_accepted'] and not r['contacts_reviewed'] and not r['physical_force'],
            'scope/acceptance')
    require(set(r['games'])=={'usa','world','offroad','exotica'},'four-game coverage')
    require(len({v['executable_sha256'] for v in r['games'].values()})==1,'common native')
    for v in r['games'].values():
        coverage=v['coverage']
        require(math.isclose(coverage['seconds'],coverage['end_seconds']-coverage['start_seconds'],abs_tol=1e-8),'clock extent')
        require(math.isclose(v['selected']['seconds']+sum(coverage['excluded_seconds'].values()),coverage['seconds'],abs_tol=1e-8),
                'duration partition')
        require(len(v['intervals_sha256'])==64 and len(v['inputs'])==6,'input receipt')
    for bucket,games in r['common_bins'].items():
        require(set(games)==set(r['games']),'shared bin games')
        require(all(v['seconds']>=r['selection']['minimum_seconds_per_game_per_bin'] for v in games.values()),'bin threshold')
require(not reports[0]['selection']['allow_ocr'] and not reports[0]['shared_condition_coverage'],'strict selection')
require(reports[0]['games']['world']['selected']['seconds']==0,'World strict speed provenance')
require(reports[1]['selection']['allow_ocr'] and set(reports[1]['common_bins'])=={
    '40-60mps/center/steady','40-60mps/negative-medium/slow'},'exploratory shared bins')
for game in reports[0]['games']:
    require(reports[0]['games'][game]['inputs']==reports[1]['games'][game]['inputs'],'same captured inputs')
print('PASS source/hash/coverage receipt consistency; raw execution and normalization remain outside this proof')
