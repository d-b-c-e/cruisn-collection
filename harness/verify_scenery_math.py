"""Check the host math against actual BSD MAME CPU helper bodies, without ROMs."""
import argparse
import json
import os
from pathlib import Path
import random
import shutil
import subprocess

from scenery_c31 import F
from verification import sha256_file, write_json


def cpu_body(source, name):
    signature = 'void tms320c3x_device::'+name+'('
    # Select the integer implementation under #else, not the USE_FP alternative.
    offset = source.index(signature, source.index(signature)+len(signature))
    start = source.index('{', offset)
    depth = 1
    end = start+1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[offset:end]


def run(mame, output, compiler):
    output.mkdir(parents=True, exist_ok=False)
    source_path = mame/'src/devices/cpu/tms320c3x/320c3x_ops.ipp'
    source = source_path.read_text()
    if '#define USE_FP              0' not in source:
        raise ValueError('CPU arithmetic implementation changed')
    prelude = '''// CPU bodies below retain MAME's BSD-3-Clause/Aaron Giles attribution.
#include <bit>
#include <cstdint>
#include <iostream>
using std::uint32_t; using std::int32_t; using std::int64_t;
uint32_t flags;
#define CLR_NZVUF() ((void)0)
#define OR_NZF(x) ((void)0)
#define OR_NZ(x) ((void)0)
#define IREG(x) flags
#define UFFLAG 0
#define LUFFLAG 0
#define VFLAG 0
#define LVFLAG 0
int count_leading_zeros_32(uint32_t v) {return std::countl_zero(v);}
int count_leading_ones_32(uint32_t v) {return std::countl_one(v);}
struct tmsreg {
 int32_t m=0; int8_t e=-128;
 int32_t mantissa()const{return m;} int exponent()const{return e;}
 void set_mantissa(uint32_t v){m=int32_t(v);} void set_exponent(int v){e=int8_t(v);}
};
struct tms320c3x_device {
 void addf(tmsreg&,tmsreg&,tmsreg&); void subf(tmsreg&,tmsreg&,tmsreg&);
 void mpyf(tmsreg&,tmsreg&,tmsreg&); void negf(tmsreg&,tmsreg&);
 void int2float(tmsreg&); void float2int(tmsreg&,bool);
};
'''
    bodies = '\n'.join(cpu_body(source, name) for name in
                       ('addf', 'subf', 'mpyf', 'negf', 'int2float', 'float2int'))
    main = '''
int main(){
 tms320c3x_device cpu; int32_t am,bm; int ae,be;
 while(std::cin>>am>>ae>>bm>>be){
  tmsreg a,b,d; a.m=am;a.e=int8_t(ae);b.m=bm;b.e=int8_t(be);
  cpu.addf(d,a,b);std::cout<<d.m<<' '<<d.exponent()<<' ';
  cpu.subf(d,a,b);std::cout<<d.m<<' '<<d.exponent()<<' ';
  cpu.mpyf(d,a,b);std::cout<<d.m<<' '<<d.exponent()<<' ';
  cpu.negf(d,a);std::cout<<d.m<<' '<<d.exponent()<<' ';
  d=a;cpu.float2int(d,false);std::cout<<d.m<<' ';
  d.m=am;cpu.int2float(d);std::cout<<d.m<<' '<<d.exponent()<<'\\n';
 }
}
'''
    cpp = output/'cpu-math.cpp'
    cpp.write_text(prelude+bodies+main)
    binary = output/('cpu-math.exe' if os.name == 'nt' else 'cpu-math')
    env = dict(os.environ)
    env['PATH'] = str(Path(compiler).resolve().parent)+os.pathsep+env.get('PATH','')
    compiled = subprocess.run([compiler, '-std=c++20', '-O2', str(cpp), '-o', str(binary)],
                              capture_output=True, text=True, env=env)
    (output/'build.log').write_text(compiled.stdout+compiled.stderr)
    compiled.check_returncode()
    rng = random.Random(0xC31)
    # Cover projection-domain extended registers, cancellation, sign boundaries,
    # zero, large exponent gaps, and conversion saturation. Not CPU status flags.
    edges = [F.integer(n) for n in (0, 1, -1, 2, -2, 255, -255, 2147483647, -2147483648)]
    vectors = [(a, b) for a in edges for b in edges]
    vectors += [(F(rng.randrange(-2**31, 2**31), rng.randrange(-45, 46)),
                 F(rng.randrange(-2**31, 2**31), rng.randrange(-45, 46))) for _ in range(10000)]
    text = ''.join(f'{a.mantissa} {a.exponent} {b.mantissa} {b.exponent}\n' for a,b in vectors)
    (output/'inputs.txt').write_text(text)
    native = subprocess.run([str(binary)], input=text, capture_output=True, text=True, env=env, check=True)
    (output/'native.txt').write_text(native.stdout)
    failures = []
    actual_lines = native.stdout.splitlines()
    if len(actual_lines) != len(vectors):
        raise ValueError('incomplete native math oracle')
    for i, ((a,b), line) in enumerate(zip(vectors, actual_lines)):
        calculated = []
        for f in (a+b, a-b, a*b, -a):
            calculated.extend((f.mantissa, f.exponent))
        integer = F.integer(a.mantissa)
        calculated.extend((a.fix(), integer.mantissa, integer.exponent))
        expected = list(map(int, line.split()))
        if calculated != expected:
            failures.append(dict(row=i, host=calculated, native=expected))
    report = dict(schema=1, passed=not failures, vectors=len(vectors), operations=6,
                  scope='arithmetic values in projection exponent range -45..45; no CPU flags',
                  cpu_source_sha256=sha256_file(source_path),
                  hashes={p.name:sha256_file(p) for p in (cpp,output/'inputs.txt',output/'native.txt')},
                  failures=failures)
    write_json(output/'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mame-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compiler', default=shutil.which('g++') or 'E:/msys64/mingw64/bin/g++.exe')
    args = parser.parse_args()
    report = run(args.mame_root, args.output, args.compiler)
    print('PASS' if report['passed'] else 'FAIL', args.output/'report.json')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
