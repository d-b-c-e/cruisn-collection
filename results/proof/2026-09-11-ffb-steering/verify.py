"""Check source and aggregate receipts; raw input/ADC evidence remains local."""
import hashlib
import json
from pathlib import Path
import re
import sys

here = Path(__file__).resolve().parent
root = here.parents[2]
sys.path.insert(0, str(root/'harness'))
from release_identity import canonical_bytes


def read(name): return json.loads((here/name).read_text())
def require(condition, message):
    if not condition: raise ValueError(message)


manifest = read('manifest.json')
require(manifest['schema'] == 1, 'schema')
for name, digest in manifest['files'].items():
    require(Path(name).name == name, 'receipt path')
    require(hashlib.sha256((here/name).read_bytes()).hexdigest() == digest, 'receipt digest: '+name)
for name, digest in read('source.json').items():
    path = (root/name).resolve()
    require(path.is_relative_to(root), 'source path')
    require(hashlib.sha256(canonical_bytes(path, path.read_bytes())).hexdigest() == digest, 'source digest: '+name)
counts = {'usa':5012, 'world':9269, 'offroad':9644, 'exotica':8860}
builds = set()
for name, count in counts.items():
    report = read(name+'.json')
    require(report['passed'] and not report['physical_angle_verified'] and not report['normalization_accepted'], 'scope')
    require(report['frames'] == count and report['inp_frames'] == count+1, 'input coverage')
    require(report['recorded_sensitivity'] == ([20] if name == 'world' else [25])
            and report['recorded_reverse'] == [0], 'stored analog settings')
    require(all(re.fullmatch('[0-9a-f]{64}', digest) for digest in report['inputs'].values()), 'input digests')
    builds.add(report['executable_sha256'])
require(sum(counts.values()) == 32785, 'total frame samples')
require(builds == {'97cd738c6b89f59a7523c9494285c5ee625e9f5041622f542983d94173b37d7a'}, 'common build')
adc = read('exotica.json')['actual_adc']
require(adc['all_matched'] and adc['steering_reads'] == 7060 and adc['first_frame'] == 1800
        and adc['last_frame'] == 8859 and adc['frame_snapshot_differences'] == 25
        and adc['max_frame_snapshot_difference'] == 1, 'actual ADC receipt')
checks = read('python-checks.json')
require(checks['passed'] and checks['source_identity'] == checks['source_identity_after']
        and checks['groups'] == ['python'], 'unchanged tested source')
require(checks['tests'] == dict(passed=True, tests=390, skipped=0, errors=0, failures=0), 'test receipt')
print('PASS source/hash/aggregate receipt consistency; raw INP/ADC and physical calibration remain external')
