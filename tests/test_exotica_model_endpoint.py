import argparse
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_model_endpoint as endpoint


class EndpointObservation(unittest.TestCase):
    def args(self,*words):
        p=argparse.ArgumentParser();p.add_argument('--candidate');endpoint.add_arguments(p)
        return p.parse_args(words)

    def test_explicit_candidate_and_surrounding_lifetime_required(self):
        base=['--candidate','test.exe','--exotica-model-endpoint','observe',
              '--exotica-endpoint-first','2000','--exotica-endpoint-last','2004',
              '--exotica-endpoint-snapshot','2001']
        life=dict(mode='observe',first=1799,last=2010);settings={'OTHER':'1'}
        trial=endpoint.configure(self.args(*base),'crusnexo',settings,life)
        self.assertEqual(trial,dict(mode='observe',first=2000,last=2004,snapshot=2001))
        self.assertEqual(settings['MIDV_FFB'],'0');self.assertEqual(settings['OTHER'],'1')
        for args,rom,lifetime in [(base[2:],'crusnexo',life),(base,'crusnusa',life),
                (base,'crusnexo',None),(base,'crusnexo',dict(mode='off')),
                (base,'crusnexo',dict(mode='observe',first=2000,last=2010)),
                (base,'crusnexo',dict(mode='observe',first=1799,last=2004)),
                (base+['--exotica-endpoint-snapshot','2005'],'crusnexo',life),
                (base+['--exotica-endpoint-last','2121'],'crusnexo',life)]:
            with self.subTest(args=args,rom=rom,lifetime=lifetime),self.assertRaises(ValueError):
                endpoint.configure(self.args(*args),rom,{},lifetime)

    def test_disabled_and_inherited_modes(self):
        settings={'OTHER':'1'}
        self.assertIsNone(endpoint.configure(self.args(),'offroadc',settings,None))
        self.assertEqual(settings,{'OTHER':'1'})
        for settings in [{'MIDZ_MODEL_ENDPOINT':'1'},{'MIDZ_MODEL_ENDPOINT_FIRST':'2000'}]:
            with self.assertRaises(ValueError):endpoint.configure(self.args(),'crusnexo',settings,None)
        with self.assertRaises(ValueError):
            endpoint.configure(self.args('--exotica-endpoint-first','2000'),'crusnexo',{},None)
        with tempfile.TemporaryDirectory() as temp:
            self.assertIsNone(endpoint.verify_receipt(None,'',temp))
            with self.assertRaises(ValueError):endpoint.verify_receipt(None,'MIDZ_MODEL_ENDPOINT=1',temp)
            (Path(temp)/'exotica-endpoint-inputs.txt').touch()
            with self.assertRaises(ValueError):endpoint.verify_receipt(None,'',temp)

    def fixture(self,directory):
        self.trial=dict(mode='observe',first=2000,last=2004,snapshot=2001)
        self.text=('MIDZ_MODEL_ENDPOINT=1 first=2000 last=2004 snapshot=2001\n'
          'MIDZ_MODEL_ENDPOINT_RESULT complete=1 commits=1 consumed=1 untracked=3 '
          'prepared=1 rejected=0 snapshots=1 bytes=520 remaining=0\n')
        self.row=dict(zip(endpoint.FIELDS,[1,2000,1.,2001,1.01,1,2,0x1000,1,2,3,
                                           0x30000,0x24860000,1,0x04000100,0xf8080001,1,1,1,1]))
        self.input=[0]*354
        self.input[:4]=[1,2001,1,0];self.input[235]=self.row['flags'];self.input[253]=self.row['packed']
        self.input[350]=1
        self.write(directory)
        (directory/'exotica-endpoint-1-original.bin').write_bytes(bytes(260))
        (directory/'exotica-endpoint-1-endpoint.bin').write_bytes(bytes(28)+b'\x01'+bytes(231))

    def write(self,directory):
        with (directory/'exotica-endpoint-models.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,endpoint.FIELDS);w.writeheader();w.writerow(self.row)
        (directory/'exotica-endpoint-inputs.txt').write_text(' '.join(map(str,self.input))+'\n')

    def test_receipt_and_corrupt_command_time_status_rejections(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);self.fixture(p)
            self.assertTrue(endpoint.verify_receipt(self.trial,self.text,p)['passed'])
            for key,value in [('id',2),('device_time',.9),('device_time',float('nan')),
                    ('commit_frame',1999),('epoch',0),('end',0x32000),('opcode',0x24870000),
                    ('slot',0x30000),('status',0),('changed',0),('snapshot',0),('base',0)]:
                old=self.row[key];self.row[key]=value;self.write(p)
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                    endpoint.verify_receipt(self.trial,self.text,p)
                self.row[key]=old
            self.write(p)
            for before,after in [('complete=1','complete=0'),('remaining=0','remaining=1'),
                                 ('bytes=520','bytes=521'),('prepared=1','prepared=0')]:
                with self.subTest(before=before),self.assertRaises(ValueError):
                    endpoint.verify_receipt(self.trial,self.text.replace(before,after),p)

    def test_input_extent_identity_and_unexpected_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);self.fixture(p)
            for index,value in [(0,2),(3,1),(235,0),(253,0),(350,17)]:
                old=self.input[index];self.input[index]=value;self.write(p)
                with self.subTest(index=index),self.assertRaises(ValueError):
                    endpoint.verify_receipt(self.trial,self.text,p)
                self.input[index]=old
            self.write(p);(p/'exotica-endpoint-extra.bin').touch()
            with self.assertRaises(ValueError):endpoint.verify_receipt(self.trial,self.text,p)

    def test_vertex_and_unrelated_state_changes_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);self.fixture(p)
            for offset in [0,36,44,68,259]:
                value=bytearray(260);value[offset]=1
                (p/'exotica-endpoint-1-endpoint.bin').write_bytes(value)
                with self.subTest(offset=offset),self.assertRaises(ValueError):
                    endpoint.verify_receipt(self.trial,self.text,p)


if __name__=='__main__':unittest.main()
