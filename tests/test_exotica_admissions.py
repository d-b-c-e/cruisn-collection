import csv
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_admissions import verify


class AdmissionReceipts(unittest.TestCase):
    def csv(self,p,fields,rows):
        with p.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(fields);w.writerows(rows)

    def fixture(self,p):
        self.trial=dict(admit_from=5072,last=5222)
        self.text='MIDZ_MODEL_ADMIT_FIRST=5072\nMIDZ_MODEL_ADMIT_RESULT complete=1 packets=1 bytes=84\n'
        self.packet=struct.pack('<9Q3I',0x31444158,1,9,5072,1,10,1,1,0,20,30,8)
        (p/'exotica-admission-packets.bin').write_bytes(self.packet)
        self.csv(p/'exotica-future-gpu.csv',['scene','frame','quads','mode'],[[9,5072,8,2]])
        fields=['event','slot','epoch','generation','realm','section','source']
        self.csv(p/'exotica-lifetime-events.csv',fields,[['L',0,1,0,0,0,0],['A',4096,1,2,0,0,0],
            ['B',4096,1,2,10,20,30],['F',4096,1,0,0,0,0],['A',4096,1,4,0,0,0],['B',4096,1,4,10,20,30]])
        self.qfields=['id','admitted','first_sequence','first_frame','last_sequence','last_frame','packets','records']
        self.qrows=[[1,1,1,5072,1,5072,1,3],[2,0,0,0,0,0,1,6]]
        self.csv(p/'exotica-endpoint-admissions.csv',self.qfields,self.qrows)
        return [dict(id=i,slot=4096,epoch=1,generation=g,realm=10,section=20,source=30) for i,g in [(1,2),(2,4)]]

    def test_actual_watermarks_retire_source_before_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);originals=self.fixture(p)
            result=verify(self.trial,self.text,p,originals)
            self.assertTrue(result['passed']);self.assertEqual(result['admitted'],1)
            self.qrows[1]=[2,1,1,5072,1,5072,1,6]
            self.csv(p/'exotica-endpoint-admissions.csv',self.qfields,self.qrows)
            with self.assertRaisesRegex(ValueError,'qualification'):verify(self.trial,self.text,p,originals)

    def test_bad_watermarks_empty_draws_and_gpu_claims_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);originals=self.fixture(p)
            for index,value in [(0,0),(1,2),(4,2),(6,32769),(7,7),(8,2)]:
                bad=bytearray(self.packet);struct.pack_into('<Q',bad,index*8,value)
                (p/'exotica-admission-packets.bin').write_bytes(bad)
                with self.subTest(index=index),self.assertRaises(ValueError):verify(self.trial,self.text,p,originals)
            bad=bytearray(self.packet);struct.pack_into('<I',bad,80,0)
            (p/'exotica-admission-packets.bin').write_bytes(bad)
            with self.assertRaises(ValueError):verify(self.trial,self.text,p,originals)
            (p/'exotica-admission-packets.bin').write_bytes(self.packet)
            self.csv(p/'exotica-future-gpu.csv',['scene','frame','quads','mode'],[[9,5072,9,2]])
            with self.assertRaises(ValueError):verify(self.trial,self.text,p,originals)

    def test_disabled_observer_has_no_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertIsNone(verify({},'',temp,[]))
            (Path(temp)/'exotica-admission-packets.bin').touch()
            with self.assertRaises(ValueError):verify({},'',temp,[])

    def test_early_permissions_share_exact_original_lifecycle(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);originals=self.fixture(p)
            self.trial.update(early='endpoint',first=5072)
            self.text+='MIDZ_ENDPOINT_EARLY_RESULT complete=1 scenes=1 permissions=1\n'
            self.csv(p/'exotica-handover-scenes.csv',['scene','end_records'],[[9,3]])
            fields=['scene','frame','records','packets','slot','epoch','generation','realm','section','source',
                    'first_sequence','first_frame','last_sequence','last_frame']
            row=[9,5072,3,1,4096,1,2,10,20,30,1,5072,1,5072]
            self.csv(p/'exotica-early-active.csv',fields,[row])
            result=verify(self.trial,self.text,p,originals)
            self.assertEqual(result['early_permissions'],1);self.assertEqual(result['admitted'],1)
            for index,value in [(2,6),(3,0),(6,4),(8,21),(10,0)]:
                bad=row.copy();bad[index]=value
                self.csv(p/'exotica-early-active.csv',fields,[bad])
                with self.subTest(index=index),self.assertRaises(ValueError):verify(self.trial,self.text,p,originals)
            self.csv(p/'exotica-early-active.csv',fields,[row,row])
            with self.assertRaises(ValueError):verify(self.trial,self.text,p,originals)


if __name__=='__main__':unittest.main()
