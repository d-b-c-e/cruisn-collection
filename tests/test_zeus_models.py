import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_models import HEADER,parse,validate


def record(**updates):
    fields=[1,4700,1,1,0,10,1,0,1,0xc0,0,0,0,0,2,0]
    for index,value in updates.items():fields[int(index)]=value
    header=HEADER.pack(*fields,80.,*([0.]*16),*([0]*208))
    return struct.pack('<II',0x31534d5a,len(header)+8)+header+struct.pack('<II',0,0)


class ZeusModelJournalTests(unittest.TestCase):
    def test_header_spans_and_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);binary=p/'models.bin';binary.write_bytes(record())
            self.assertEqual(parse(binary)[0]['words'],[0,0])
            receipt=dict(schema=1,complete=True,models=1,bytes=binary.stat().st_size,quads=1)
            (p/'models.json').write_text(json.dumps(receipt))
            self.assertEqual(validate(p,4700,1)['covered_quads'],1)
            for key,value in [('complete',False),('models',2),('quads',2),('bytes',1)]:
                (p/'models.json').write_text(json.dumps(dict(receipt,**{key:value})))
                with self.assertRaises(ValueError):validate(p,4700,1)
            for bad in (record()[:-1],record()+b'\0',record()+record(),
                        record(**{'5':8}),record(**{'8':0,'7':1}),record(**{'14':4}),record(**{'15':1})):
                binary.write_bytes(bad)
                with self.assertRaises(ValueError):parse(binary)


if __name__=='__main__':unittest.main()
