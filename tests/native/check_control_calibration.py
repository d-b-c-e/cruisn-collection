"""Compare compiled native calibration with independent shared golden vectors."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    fixture=ROOT/'fixtures/control-calibration.json'
    vectors=json.loads(fixture.read_text(encoding='utf-8'))
    count=0
    for case in vectors['vectors']:
        c=case['calibration'] or dict(kind='steering',left=-1,centre=0,right=1,invert=False,deadzone=0)
        for raw,expected in case['samples']:
            values=[c['kind'],int(c['invert']),c['released'] if c['kind']=='pedal' else c['left'],
                    c.get('centre',0),c['full'] if c['kind']=='pedal' else c['right'],c['deadzone'],raw,
                    'run' if case['calibration'] else 'pass']
            run=subprocess.run([str(args.executable.resolve()),*map(str,values)],capture_output=True,text=True,check=True,timeout=10)
            value=float(run.stdout)
            if not math.isfinite(value) or abs(value-expected)>vectors['absolute_tolerance']:
                raise ValueError(f"{case['name']} raw{raw}: native{value} expected{expected}")
            count+=1
    result=dict(passed=True,cases=len(vectors['vectors']),samples=count,
                fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                executable_sha256=hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256((ROOT/'native/control_calibration.h').read_bytes()).hexdigest(),
                scope='Native normalization math; runtime transport/input acceptance separate')
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
