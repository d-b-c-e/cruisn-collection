from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_transform import prepare,packet
from scenery_c31 import F
from verify_exotica_transforms import check_row,verify


def fixture():
    f=lambda n:F.integer(n).store()
    identity=[f(i%4==0) for i in range(9)]
    obj=[0]*32;obj[1:4]=[f(10),f(20),f(30)];obj[5:14]=identity
    obj[17]=0xa00000;obj[20]=30;obj[22]=f(255)
    p=prepare(obj[1:4],[f(0)]*3,identity,identity,identity,0)
    r=dict(schema=1,id=1,frame=3500,native_frame=3499,time=60.,pc=0x6964,
        object=0x2000,object_words=obj,flags=0,descriptor=0xa00000,selected=0xa00000,
        primary=[0,0,0,2000,5],metadata=[0,0,0,2000,5],view=identity,camera=[f(0)]*3,
        rotation=identity,alternate=identity,prepared=identity,translation=p['translation'],
        matrix_cursor=0x87ff53,scale=f(1),ring=0x31000,preceding=[0]*3+packet(p,f(1),1),
        previous_alpha=f(255),matrix_update=1)
    e=dict(id=1,frame=3500,native_frame=3499,time=60.00001,pc=0x6970,object=0x2000,
        selected=0xa00000,ring=0x31002,packet=[0x24860005,2000])
    return r,e


class ExoticaEvidenceTests(unittest.TestCase):
    def test_actual_packet_and_clock_boundary(self):
        r,e=fixture();self.assertFalse(check_row(r,e)[2])
        boundary=dict(e,native_frame=3500);check_row(r,boundary)
        for change in ({'selected':0xa00001},{'ring':0x31004},{'native_frame':3501},
                       {'time':59.},{'packet':[0x24860005,2001]}):
            with self.assertRaises(ValueError):check_row(r,dict(e,**change))
        for key in ('translation','preceding','primary'):
            wrong=deepcopy(r);wrong[key][-1]^=1
            with self.assertRaises(ValueError):check_row(wrong,e)
        with self.assertRaises(ValueError):check_row(dict(r,matrix_update=0),e)
        with self.assertRaises(ValueError):check_row(r,None)
        special=dict(r,flags=0x80)
        self.assertTrue(check_row(special,None)[2])
        with self.assertRaises(ValueError):check_row(special,e)

    def test_complete_capture_counts_and_unique_emissions(self):
        r,e=fixture()
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            capture=dict(schema=1,first=3500,last=3500,window_frames=1,calls=1,emissions=1,complete=True)
            (p/'exotica-models.jsonl').write_text(json.dumps(r)+'\n')
            (p/'exotica-emissions.jsonl').write_text(json.dumps(e)+'\n')
            (p/'exotica-model-capture.json').write_text(json.dumps(capture))
            self.assertEqual(verify(p)['ordinary_emissions'],1)
            for change in ({'complete':False},{'calls':2},{'window_frames':2},{'first':3499}):
                (p/'exotica-model-capture.json').write_text(json.dumps(dict(capture,**change)))
                with self.assertRaises(ValueError):verify(p)
            (p/'exotica-model-capture.json').write_text(json.dumps(dict(capture,emissions=2)))
            (p/'exotica-emissions.jsonl').write_text((json.dumps(e)+'\n')*2)
            with self.assertRaises(ValueError):verify(p)


if __name__=='__main__':unittest.main()
