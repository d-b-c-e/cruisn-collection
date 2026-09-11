"""Verify public source hashes and actual-worker receipt consistency.

Does not rerun private recordings, native execution, GPU captures or a wheel.
"""
from pathlib import Path
import hashlib
import json
import sys

here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path.insert(0,str(root/'harness'))
from release_identity import canonical_bytes


def read(name):return json.loads((here/name).read_text(encoding='utf-8'))


def require(value,why):
    if not value:raise ValueError(why)


manifest=read('manifest.json');require(manifest['schema']==1,'schema')
for name,digest in manifest['files'].items():
    require(Path(name).name==name,'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'receipt '+name)
for name,digest in read('source.json').items():
    path=(root/name).resolve();require(path.is_relative_to(root),'source path')
    require(hashlib.sha256(canonical_bytes(path,path.read_bytes())).hexdigest()==digest,'source '+name)
build=read('build.json');require(build['passed'] and build['patch_count']==188,'native export')
require(build['native_commit']=='93684035c6c1995b01ee67aef5537f5b751a8a10','native commit')
require(build['patch_sha256']==read('source.json')['patch/vunit-poc-patches.patch'],'patch binding')
four=read('four-games.json')
require(four['passed'] and not four['normalization_accepted'] and not four['physical_output'],'scope')
expected={'usa':(5012,4569,9947),'world':(9269,8803,17565),
          'offroad':(9644,8820,18006),'exotica':(8860,7476,16195)}
require(set(four['games'])==set(expected),'four games')
for game,item in four['games'].items():
    worker=item['worker'];receipt=worker['receipt']
    require((item['frames'],worker['source_join_rows'],worker['ticks'])==expected[game],'coverage '+game)
    require(item['current_build']==build['candidate_sha256'] and item['physical_ffb']=='0','candidate '+game)
    require(item['comparison']['passed'] and item['comparison']['input_or_time_mismatches']==0
            and item['comparison']['pixel_mismatches']==0,'original comparison '+game)
    require(item['nominal_strength']==50 and item['effective_strength']==(40 if game=='exotica' else 50),'strength '+game)
    require(worker['passed'] and not worker['physical_acceptance'] and not worker['mailbox_causality_verified'],'worker scope '+game)
    require(receipt['complete'] and receipt['device_free'] and not receipt['physical_output']
            and receipt['profile_loaded'] and receipt['profile']=='cruisn-vunit@2'
            and receipt['smoothing_ms']==20 and receipt['sink_final_level']==0,'worker receipt '+game)
    require(receipt['ticks']==worker['ticks'] and receipt['sources']==worker['source_join_rows'],'journal count '+game)
    require(receipt['strength']==item['effective_strength'] and not receipt['impact_axis'],'legacy baseline '+game)
    require(all(v['current']==v['reference'] for v in item['unchanged_game_csvs'].values()),'unchanged game sources '+game)
images=four['games']['exotica']['gl_images']
require(images['count']==21 and images['dimensions']==[3840,2160] and images['crt']
        and images['all_reference_bytes_equal'] and len(images['files'])==21,'sampled Exotica presentation')
controls=read('controls.json')
for name,item in controls.items():
    require(item['comparison']['passed'] and item['candidate_sha256']==build['candidate_sha256'],'control '+name)
require(controls['disabled']['frames']==1200 and not controls['disabled']['observer_artifacts'],'disabled control')
zero=controls['zero'];require(zero['frames']==2400 and zero['nonzero_input_ticks']>0
    and zero['nonzero_output_ticks']==0 and zero['worker']['sink_changes']==0,'zero control')
enhanced=controls['enhanced'];require(enhanced['frames']==5012 and enhanced['worker']['events']>0
    and enhanced['nonzero_envelope_ticks']>0 and enhanced['worker']['receipt']['impact_axis'],'enhanced control')
checks=read('checks.json');require(len({c['source_identity'] for c in checks.values()})==1,'same checked source')
native=checks['ffb-worker-local-checks'];python=checks['ffb-worker-python-checks']
require(native['passed'] and native['groups']==['native'] and native['commands']==135
        and native['native_tests']==51,'native tests')
require(python['passed'] and python['groups']==['python'] and python['python']['passed']
        and python['python']['tests']==411 and python['python']['skipped']==0,'Python tests')
print('PASS source/hash/receipt consistency: four actual worker baselines and controls; normalization/physical acceptance remain open')
