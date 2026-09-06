import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gpu'))
from tjunctions import align


def scene(p=(7,11), uv=(9,18)):
    a=(2,2,0,0); b=(12,22,20,40); c=(20,2,36,0); d=(0,22,0,40)
    p=(*p,*uv)
    quads=np.zeros((3,16),np.uint16)
    for q,vertices in zip(quads,((a,b,c,c),(b,p,d,d),(p,a,d,d))):
        q[0]=0x100;q[1]=0x200
        q[2:10]=np.array([v[:2] for v in vertices],np.int16).ravel().view(np.uint16)
        q[10:14]=[v[2]+256*v[3] for v in vertices]
    return quads


class TjunctionTests(unittest.TestCase):
    def test_closed_join_moves_shared_vertex_only(self):
        q=scene(); positions,repairs=align(q)
        self.assertEqual(len(repairs),1)
        np.testing.assert_allclose(positions[1,1],(6.6,11.2),atol=1e-6)
        np.testing.assert_array_equal(positions[1,1],positions[2,0])
        self.assertEqual(np.count_nonzero(positions!=q[:,2:10].copy().view(np.int16).reshape(-1,4,2)),4)

    def test_rejects_unproven_connections(self):
        variants=[scene()[:2],scene(p=(8,10)),scene(uv=(30,2)),scene(p=(7,12),uv=(10,20))]
        for change in ((0,0x900),(1,0x400),(14,1)):
            q=scene();q[1,change[0]]=change[1];variants.append(q)
        for q in variants:
            with self.subTest(quads=q.tolist()):
                positions,repairs=align(q)
                self.assertEqual(repairs,[])
                np.testing.assert_array_equal(positions,q[:,2:10].copy().view(np.int16).reshape(-1,4,2))


if __name__=='__main__':unittest.main()
