"""Independent lifecycle scenarios and strict event-input rejection."""
import subprocess
import sys

native=sys.argv[1]
def run(text):return subprocess.run([native],input=text,text=True,capture_output=True,timeout=10)
initial='L 100 131 2 1\n'
valid=initial+'F 100\nA 100\nB 100 4294967301 50 60\nD 100 1 2 4294967301 50 60 100\nD 100 1 2 4294967301 50 60 100\nR 200 231 2\nA 200\nB 200 4294967301 50 60\nD 200 2 4 4294967301 50 60 1\n'
r=run(valid)
expected='L 0 1 0 0\nF 1 1 0 1\nA 2 1 2 0\nB 2 1 2 0\nD 2 1 2 1\nD 2 1 2 0\nR 3 2 0 0\nA 4 2 4 0\nB 4 2 4 0\nD 4 2 4 1\n'
assert r.returncode==0 and r.stdout==expected,(r.stdout,r.stderr)
prefix=initial+'A 100\nB 100 1 50 60\nD 100 1 1 1 50 60 10\n'
invalid=['','\n','L 100 131 0 1\n','L 100 131 4097 1\n','L 100 131 2 2\n',
 initial+'L 100 131 2 1\n',initial+'A -1\n',initial+'A 18446744073709551616\n',
 initial+'A 4294967296\n',initial+'A 100 suffix\n',initial+'A 100 1\n',
 prefix+'D 100 1 1 1 50 60 9\n',prefix+'D 100 1 2 1 50 60 11\n',
 prefix+'D 100 1 1 2 50 60 11\n',prefix+'F 100\nD 100 1 1 1 50 60 11\n',
 prefix+'R 100 131 2\nD 100 1 1 1 50 60 11\n',initial+'A '+('0'*257)+'\n']
for case in invalid:
 result=run(case);assert result.returncode!=0,(case,result.stdout)
print('PASS independent reset/reuse/submission scenario and',len(invalid),'input rejections')
