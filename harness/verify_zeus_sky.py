"""Verify periodic backdrop inference against actual original submitted quads."""
import argparse,json,struct,subprocess
from pathlib import Path
import numpy as np
from zeus_capture import parse_records
from zeus_rasterize import QUAD_DTYPE
from zeus_sky_repeat import plan
from verification import write_json,sha256_file


def tiles(path):
    result=[]
    for kind,p in parse_records(path):
        if kind!=1:continue
        q=np.frombuffer(p,QUAD_DTYPE)[0]
        if int(q['flags'])&~512!=52:break
        result.append(q.copy())
        if len(result)>64:raise ValueError('background exceeds tile budget')
    return result


def native_words(rows,margin):
    out=[len(rows),margin]
    for q in rows:
        out.extend(np.frombuffer(q.tobytes(),'<u4')[2:17].tolist())
        out.extend(q['verts'][:4].view('<u4').ravel().tolist())
    return out


def verify(path,native=None):
    source=Path(path)/'records.bin';rows=tiles(source);p=plan(rows)
    if not p['accepted']:raise ValueError('original backdrop not structurally verified: '+p['reason'])
    if native:
        run=subprocess.run([str(Path(native).resolve())],input=' '.join(map(str,native_words(rows,88)))+'\n',text=True,capture_output=True,timeout=30)
        if run.returncode:raise ValueError('native sky analyzer failed: '+run.stderr[:500])
        fields=run.stdout.split();expected=[str(len(p['copies']))]
        for copy in p['copies']:expected.extend([str(copy['index']),str(struct.unpack('<I',struct.pack('<f',copy['shift']))[0])])
        if (len(fields)<4 or fields[0]!='1' or float(fields[1])!=p['period'] or fields[2]!=str(p['overlap_comparisons']) or fields[3:]!=expected):
            raise ValueError('native/Python sky plan mismatch: '+run.stdout)
    return dict(passed=True,tiles=len(rows),plan=p,native_verified=bool(native),records_sha256=sha256_file(source),
                native_sha256=sha256_file(native) if native else None,
                scope='All duplicate texture/UV/depth rectangles match inferred period at original overlapping positions. Planned added tiles retain material and shape outside original512 columns. GPU, ordering and future geometry acceptance separate.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--native',type=Path);p.add_argument('--report',required=True,type=Path);a=p.parse_args()
    try:r=verify(a.capture,a.native)
    except (ValueError,OSError,KeyError,subprocess.TimeoutExpired) as e:r=dict(passed=False,error=str(e))
    write_json(a.report,r);print('PASS' if r['passed'] else 'FAIL',a.report);return 0 if r['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
