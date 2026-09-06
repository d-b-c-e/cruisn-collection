"""Compare the shared C++ geometry helper to the offline Python reference."""
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_tjunctions import scene, align


def main():
    exe=str(Path(sys.argv[1]).resolve())
    examples=[scene(),scene()[:2],scene(p=(8,10)),scene(uv=(30,2)),scene(p=(7,12),uv=(10,20))]
    for change in ((0,0x900),(1,0x400),(14,1)):
        q=scene();q[1,change[0]]=change[1];examples.append(q)
    for offset in (-1200,-100,100,1200):
        q=scene();xy=q[:,2:10].copy().view(np.int16);xy+=offset;q[:,2:10]=xy.view(np.uint16);examples.append(q)
    with tempfile.TemporaryDirectory() as folder:
        source=Path(folder)/'quads.bin';target=Path(folder)/'positions.bin'
        for q in examples:
            q.astype('<u2').tofile(source)
            run=subprocess.run([exe,str(source),str(target)],check=True,capture_output=True,text=True)
            positions,repairs=align(q)
            assert int(run.stdout)==len(repairs)
            actual=np.fromfile(target,'<f4').reshape(-1,4,2)
            np.testing.assert_array_equal(actual,positions)
    print(f'PASS: {len(examples)} native/Python geometry cases')


if __name__=='__main__':main()
