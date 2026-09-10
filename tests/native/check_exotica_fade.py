"""Cross-check native fade operands and reject truncated analyzer input."""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'harness'))
from verify_exotica_fade import step

native=Path(sys.argv[1]).resolve()
rows=[]
for alpha in range(256):
    for increment in (1,8,127,255):
        if alpha+increment<=255:
            rows.append((0x7f000000 | alpha<<16 | 0x1357,0x04008133,increment))
text=''.join(' '.join(map(str,row))+'\n' for row in rows)
p=subprocess.run([str(native)],input=text,capture_output=True,text=True,timeout=30)
assert p.returncode==0,p.stderr
expected=[list(map(int,step(*row))) for row in rows]
assert [list(map(int,line.split())) for line in p.stdout.splitlines()]==expected
valid='2013794903 67141939 8\n'
for suffix in ('1','1 2','invalid','4294967296 67109120 8','0 67109120 18446744073709551616'):
    p=subprocess.run([str(native)],input=valid+suffix,capture_output=True,text=True,timeout=30)
    assert p.returncode==2,(suffix,p.returncode)
for invalid,code in [('',2),(' \n',2),('0 0 8',1),('0 67109120 0',1),(valid*8193,2)]:
    p=subprocess.run([str(native)],input=invalid,capture_output=True,text=True,timeout=30)
    assert p.returncode==code,(len(invalid),p.returncode,code)
print(f'PASS {len(rows)} independent native fade steps and 10 malformed/domain/budget inputs')
