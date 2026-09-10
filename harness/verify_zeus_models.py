"""Verify original Zeus models against exact ordered projected polygons and state.

Copies of model state are decoded independently in Python and optionally C++.
This does not draw extra scenery or establish future-material residency.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import subprocess
import sys
import numpy as np
from zeus_models import parse,validate
from zeus_model import decode
from zeus_capture import parse_records
from verification import sha256_file,write_json


def verify(directory,native=None):
    directory=Path(directory)
    models=parse(directory/'models.bin')
    actual=[payload for kind,payload in parse_records(directory/'records.bin') if kind==1]
    frame=max(struct.unpack_from('<I',p)[0] for p in actual)
    validate(directory,frame,len(actual))
    counts=Counter();covered=0
    for model in models:
        projected,stats=decode(model);counts.update(stats)
        original=actual[model['first_quad']:model['last_quad']]
        if len(projected)!=len(original):
            raise ValueError(f'model{model["id"]}: projected count {len(projected)} != {len(original)}')
        for i,((fields,vertices),record) in enumerate(zip(projected,original)):
            padded=np.zeros((8,6),dtype='<f4');padded[:len(vertices)]=vertices
            expected=struct.pack('<17I',*fields)+padded.tobytes()
            if expected!=record:
                raise ValueError(f'model{model["id"]}/quad{i}: ordered geometry/state mismatch')
        covered+=len(original)
    native_result=None
    if native:
        result=subprocess.run([str(Path(native).resolve()),str(directory/'models.bin'),str(directory/'records.bin')],
                              text=True,capture_output=True,timeout=120)
        if result.returncode:
            raise ValueError(f'native model oracle exit{result.returncode}: {result.stdout[:1500]} {result.stderr[:500]}')
        native_result=json.loads(result.stdout)
        if (native_result.get('passed') is not True or native_result['models']!=len(models) or
                native_result['covered_quads']!=covered or native_result['total_quads']!=len(actual)):
            raise ValueError('native Zeus model coverage mismatch')
    return {'schema':1,'passed':True,'scope':__doc__.strip(),'models':len(models),
            'covered_quads':covered,'total_quads':len(actual),'counts':dict(counts),
            'quad_sizes':dict(Counter(r['quad_size'] for r in models)),
            'rendering_programs':dict(Counter(hex(r['ucode']) for r in models)),
            'native':native_result,'native_sha256':sha256_file(native) if native else None,
            'sources':{name:sha256_file(directory/name) for name in ('models.bin','models.json','records.bin')}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--native',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args(argv)
    try:result=verify(args.directory,args.native)
    except (ValueError,KeyError,TypeError,OSError,subprocess.TimeoutExpired) as error:
        result={'schema':1,'passed':False,'error':str(error)}
    write_json(args.report,result);print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1


if __name__=='__main__':sys.exit(main())
