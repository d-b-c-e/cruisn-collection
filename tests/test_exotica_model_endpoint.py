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

    def test_admission_requires_actual_covered_future_drawing(self):
        args=self.args('--candidate','test.exe','--exotica-model-endpoint','observe',
             '--exotica-endpoint-first','5218','--exotica-endpoint-last','5222',
             '--exotica-endpoint-snapshot','5219','--exotica-endpoint-admit-from','5072')
        life=dict(mode='observe',first=1799,last=5258)
        scene=dict(future=2,materials=True,first=1800,last=5250)
        settings={};trial=endpoint.configure(args,'crusnexo',settings,life,scene)
        self.assertEqual(trial['admit_from'],5072)
        self.assertEqual(settings['MIDZ_MODEL_ADMIT_FIRST'],'5072')
        for bad in [None,dict(scene,future=1),dict(scene,materials=False),dict(scene,first=5100),dict(scene,last=5221)]:
            with self.subTest(scene=bad),self.assertRaises(ValueError):endpoint.configure(args,'crusnexo',{},life,bad)
        args.exotica_model_endpoint='draw';settings={}
        self.assertEqual(endpoint.configure(args,'crusnexo',settings,life,scene)['mode'],'draw')
        self.assertEqual(settings['MIDZ_MODEL_ENDPOINT'],'2')
        args.exotica_endpoint_admit_from=None
        with self.assertRaises(ValueError):endpoint.configure(args,'crusnexo',{},life,scene)

    def test_private_pair_receipts_require_exact_qualified_quad_order(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            (p/'exotica-endpoint-admissions.csv').write_text('id,admitted\n1,1\n2,0\n')
            (p/'exotica-endpoint-gpu.csv').write_text('frame,model,index,count\n5219,1,0,2\n5219,1,1,2\n')
            originals=[dict(id=1,status=1,quads=2,device_frame=5219),dict(id=2,status=1,quads=1,device_frame=5219)]
            text='MIDZ_ENDPOINT_GPU_RESULT complete=1 pairs=2\n'
            self.assertEqual(endpoint.verify_draw(dict(mode='draw'),text,p,originals)['pairs'],2)
            with self.assertRaises(ValueError):endpoint.verify_draw(dict(mode='observe'),text,p,originals)
            (p/'exotica-endpoint-gpu.csv').write_text('frame,model,index,count\n5219,1,1,2\n5219,1,0,2\n')
            with self.assertRaises(ValueError):endpoint.verify_draw(dict(mode='draw'),text,p,originals)

    def test_early_visibility_is_explicit_and_requires_private_handover(self):
        words=['--candidate','test.exe','--exotica-model-endpoint','draw',
               '--exotica-endpoint-first','5218','--exotica-endpoint-last','5248',
               '--exotica-endpoint-snapshot','5219','--exotica-endpoint-admit-from','5072']
        life=dict(mode='observe',first=1799,last=5258)
        scene=dict(future=2,materials=True,first=1800,last=5248,compose=True,active=2)
        args=self.args(*words,'--exotica-early-visibility','endpoint');settings={}
        self.assertEqual(endpoint.configure(args,'crusnexo',settings,life,scene)['early'],'endpoint')
        self.assertEqual(settings['MIDZ_ENDPOINT_EARLY'],'1')
        with self.assertRaises(ValueError):endpoint.configure(args,'crusnexo',{},life,dict(scene,compose=False))
        args.exotica_model_endpoint='observe'
        with self.assertRaises(ValueError):endpoint.configure(args,'crusnexo',{},life,scene)
        with self.assertRaises(ValueError):endpoint.configure(self.args(*words),'crusnexo',settings,life,scene)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);self.fixture(p)
            with self.assertRaises(ValueError):endpoint.verify_receipt(dict(self.trial,early='endpoint'),self.text,p)
            with self.assertRaises(ValueError):endpoint.verify_receipt(self.trial,self.text+'MIDZ_ENDPOINT_EARLY=1\n',p)

    def test_full_drive_requires_explicit_marked_scope(self):
        args=self.args('--candidate','test.exe','--exotica-model-endpoint','observe',
            '--exotica-endpoint-first','1800','--exotica-endpoint-last','8848',
            '--exotica-endpoint-snapshot','5219')
        life=dict(mode='observe',first=1799,last=8858)
        with self.assertRaises(ValueError):endpoint.configure(args,'crusnexo',{},life)
        args.exotica_endpoint_scope='marked';settings={}
        self.assertEqual(endpoint.configure(args,'crusnexo',settings,life)['scope'],'marked')
        self.assertEqual(settings['MIDZ_ENDPOINT_MARKED'],'1')
        args.exotica_endpoint_scope=None
        with self.assertRaises(ValueError):endpoint.configure(args,'crusnexo',settings,life)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);self.fixture(p)
            with self.assertRaises(ValueError):endpoint.verify_receipt(dict(self.trial,scope='marked'),self.text,p)
            text=self.text+'MIDZ_ENDPOINT_MARKED=1\n'
            self.assertTrue(endpoint.verify_receipt(dict(self.trial,scope='marked'),text,p)['passed'])
            with self.assertRaises(ValueError):endpoint.verify_receipt(self.trial,text,p)

    def test_marked_scope_retains_first_rejected_operands_outside_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);self.fixture(p)
            self.row.update(device_frame=2000,status=2,quads=0,changed=0)
            self.input[1]=2000;self.write(p)
            for kind in ('original','endpoint'):(p/f'exotica-endpoint-1-{kind}.bin').unlink()
            text=self.text.replace('prepared=1 rejected=0','prepared=0 rejected=1').replace('bytes=520','bytes=0')+'MIDZ_ENDPOINT_MARKED=1\n'
            trial=dict(self.trial,scope='marked')
            self.assertEqual(endpoint.verify_receipt(trial,text,p)['rejected'],1)
            self.row['snapshot']=0;self.write(p)
            with self.assertRaises(ValueError):endpoint.verify_receipt(trial,text,p)


if __name__=='__main__':unittest.main()
