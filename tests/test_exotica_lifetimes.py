import argparse
import copy
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_lifetimes import FIELDS,add_arguments,configure,verify_receipt


class ExoticaLifetimes(unittest.TestCase):
    def args(self,*args):
        parser=argparse.ArgumentParser()
        parser.add_argument('--candidate')
        add_arguments(parser)
        return parser.parse_args(args)

    def test_configuration_preserves_default_and_recorded_modes(self):
        settings={'MIDZ_OTHER':'1'}
        self.assertIsNone(configure(self.args(),'crusnusa',settings))
        self.assertEqual(settings,{'MIDZ_OTHER':'1'})
        result=configure(self.args('--candidate','test.exe','--exotica-lifetimes','observe',
            '--exotica-lifetime-first','1799','--exotica-lifetime-last','8858'),'crusnexo',settings)
        saved=dict(settings)
        self.assertEqual(configure(self.args(),'crusnexo',settings),result)
        self.assertEqual(settings,saved)
        self.assertEqual(configure(self.args('--candidate','test.exe','--exotica-lifetimes','off'),
            'crusnexo',settings),{'mode':'off'})
        self.assertEqual(settings,{'MIDZ_OTHER':'1','MIDZ_LIFETIME':'0'})

    def test_rejects_incomplete_or_wrong_game_configuration(self):
        base=['--candidate','test.exe','--exotica-lifetimes','observe']
        cases=[(['--exotica-lifetimes','observe'],'crusnexo',{}),
            (['--exotica-lifetime-first','2000'],'crusnexo',{}),
            (base,'crusnexo',{}),
            (base+['--exotica-lifetime-first','2000','--exotica-lifetime-last','2001'],'offroadc',{}),
            (base+['--exotica-lifetime-first','1798','--exotica-lifetime-last','2000'],'crusnexo',{}),
            (base+['--exotica-lifetime-first','1800','--exotica-lifetime-last','11801'],'crusnexo',{}),
            (base+['--exotica-lifetime-first','2000','--exotica-lifetime-last','1999'],'crusnexo',{}),
            ([],'crusnexo',{'MIDZ_LIFETIME_FIRST':'2000'}),
            ([],'crusnexo',{'MIDZ_LIFETIME':'2'}),
            ([],'crusnexo',{'MIDZ_LIFETIME':'1','MIDZ_LIFETIME_FIRST':'2000'}),
            (['--candidate','test.exe','--exotica-lifetimes','off','--exotica-lifetime-first','2000'],'crusnexo',{})]
        for args,rom,settings in cases:
            with self.subTest(args=args,rom=rom,settings=settings),self.assertRaises(ValueError):
                configure(self.args(*args),rom,settings)

    def fixture(self):
        def row(event,**kwargs):
            return dict.fromkeys(FIELDS,0)|dict(event=event,frame=1800,time=31.5,epoch=1)|kwargs
        source=dict(owner=1,realm=(1<<32)|0xa00080,section=0xa01000,source=0xa02000)
        rows=[row('L',slot=0x1100,reason=1172),
              row('F',sequence=1,slot=0x1200,reason=1,flags=1173),
              row('A',sequence=2,generation=2,slot=0x1100,flags=1172),
              row('B',sequence=2,generation=2,slot=0x1100,flags=0x04000100,**source),
              row('D',sequence=2,generation=2,slot=0x1100,reason=3,flags=0x04000100,**source),
              row('D',sequence=2,generation=2,slot=0x1100,reason=2,flags=0x04000100,**source),
              row('D',sequence=2,generation=2,slot=0x1100,reason=4,**source),
              row('F',sequence=3,slot=0x1100,flags=1173),
              row('R',sequence=4,epoch=2,slot=0x19000,reason=1201,flags=1200)]
        text=('MIDZ_LIFETIME=1 first=1799 last=8858\n'
              'MIDZ_LIFETIME_RESULT complete=1 records=9 transitions=4 bindings=1 emissions=20 owned=10 draws=3 first_draws=1 fading=2 opaque=1 epochs=2\n')
        return rows,text

    def verify(self,rows,text,trial=None):
        with tempfile.TemporaryDirectory() as temp:
            with (Path(temp)/'exotica-lifetime-events.csv').open('w',newline='',encoding='utf-8') as stream:
                writer=csv.DictWriter(stream,fieldnames=FIELDS)
                writer.writeheader();writer.writerows(rows)
            return verify_receipt(trial or dict(mode='observe',first=1799,last=8858),text,temp)

    def test_complete_pool_binding_submission_reset_fold(self):
        result=self.verify(*self.fixture())
        self.assertTrue(result['passed'])
        self.assertEqual((result['unknown_frees'],result['first_draws'],result['epochs']),(1,1,2))

    def test_rejects_stale_handles_bad_transitions_bounds_and_clocks(self):
        mutations=[(0,'epoch',0),(0,'time',-0.5),(2,'generation',1),
            (3,'realm',0),(3,'owner',2),(4,'source',0xa02004),(4,'generation',1),
            (4,'reason',2),(5,'reason',3),(6,'reason',0),(7,'reason',1),
            (8,'slot',0),(8,'slot',0x2f000),(8,'epoch',1),
            (5,'time','nan'),(5,'time',31.4),(5,'frame',1799),(5,'flags',1<<32),
            (5,'frame',8859),(3,'slot',0x30000),(2,'sequence',3),(2,'flags',1171)]
        for index,key,value in mutations:
            rows,text=self.fixture();rows[index][key]=value
            with self.subTest(index=index,key=key,value=value),self.assertRaises(ValueError):
                self.verify(rows,text)

    def test_rejects_incomplete_miscounted_and_disabled_observation(self):
        rows,text=self.fixture()
        for changed in (text.replace('complete=1','complete=0'),text.replace('records=9','records=8'),
            text.replace('first_draws=1','first_draws=0'),text.replace('owned=10','owned=2'),
            text.replace('emissions=20','emissions=20000001'),text+text,text.splitlines()[0]):
            with self.subTest(text=changed),self.assertRaises(ValueError):self.verify(rows,changed)
        with self.assertRaisesRegex(ValueError,'disabled'):
            self.verify(rows,'',dict(mode='off'))
        with tempfile.TemporaryDirectory() as temp:
            self.assertIsNone(verify_receipt(None,'',temp))
            with self.assertRaisesRegex(ValueError,'disabled'):verify_receipt(None,text,temp)

    def test_reset_invalidates_owner_and_prohibits_unknown_free(self):
        rows,text=self.fixture()
        for op in ('D','F'):
            changed=copy.deepcopy(rows)
            extra=dict(rows[4]) if op=='D' else dict(rows[1])
            extra.update(event=op,sequence=4 if op=='D' else 5,epoch=2)
            changed.append(extra)
            with self.subTest(op=op),self.assertRaises(ValueError):
                self.verify(changed,text.replace('records=9','records=10'))


if __name__=='__main__':unittest.main()
