"""Qualify optional Off-Road camera/quad depths from saved original model captures."""
import argparse
import json
from pathlib import Path
import struct
import subprocess

from scenery_c31 import F, signed
from verify_offroad_model import check as check_original, native_records
from verification import write_json


def check(run, binary):
    original = check_original(run, binary)
    if not original['passed']:
        raise ValueError('original transform/projection/DMA qualification failed')
    records = [json.loads(line) for line in (run/'offroad-model-transform.jsonl').read_text(encoding='utf-8').splitlines()]
    reciprocal = struct.unpack('<67776I',(run/'offroad-model-reciprocals.bin').read_bytes())
    baseline = native_records(binary, records, reciprocal)
    actual = native_records(binary, records, reciprocal, with_depths=True)
    vertices = quads = clamped = 0
    for record in records:
        call = record['call']; points, output, depths, quad_depths = actual[call]
        if (points,output) != baseline[call]:
            raise ValueError('depth capture changed original projection or polygons')
        matrix = list(map(F.load,record['matrix']))
        expected = []
        for i in range(record['vertices']):
            x,y,z = map(F.load,record['vertex_words'][3*i:3*i+3])
            depth = ((x*matrix[8]+matrix[11])+y*matrix[9])+z*matrix[10]
            expected.append(depth.store())
            clamped += ((record['path']==0x1e3b and depth.fix() < -4096) or
                        (record['path']==0x1e60 and depth.fix() > 63679))
        selected = []
        for i in range(record['polygons']):
            p = record['polygon_words'][6*i:6*i+6]
            indices = [p[4]&65535,p[4]>>16,p[5]&65535,p[5]>>16]
            xy = [signed(points[2*(j//3)+k]) for j in indices for k in (0,1)]
            x0,y0,x1,y1,x2,y2 = xy[:6]
            if signed((x0-x1)*(y2-y1)-(y0-y1)*(x2-x1)) <= 0:
                selected.append([expected[j//3] for j in indices])
        if depths != expected or quad_depths != selected:
            raise ValueError('camera depths or post-cull polygon order differ from independent arithmetic')
        vertices += len(depths); quads += len(quad_depths)
    return dict(passed=True, original=original, records=len(records), vertices=vertices,
                quads=quads, clamped_vertices=clamped, original_output_exact=True,
                scope='Actual captured transforms and unchanged original XY/DMA with independently checked '
                      'camera-depth words. No host admission, GPU depth interpolation or fade-policy acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--native',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('preserve the existing report')
    try:
        result = check(args.run,args.native)
    except (OSError,ValueError,KeyError,TypeError,struct.error,subprocess.SubprocessError) as exc:
        result = dict(passed=False,error=str(exc))
    write_json(args.report,result)
    print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
