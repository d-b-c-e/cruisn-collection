import argparse
import csv
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_waiting as w
import exotica_lifetimes as life


class ExoticaWaitingTests(unittest.TestCase):
    def args(self,*args):
        p=argparse.ArgumentParser();p.add_argument('--candidate');p.add_argument('--headless',action='store_true')
        w.add_arguments(p);return p.parse_args(args)

    def settings(self):
        return dict(MIDZ_GL='1',MIDZ_DEPTH_MIRROR='2',MIDZ_HOST_MATERIALS='1')

    def scene(self):return dict(first=1800,last=5998,future=1,snapshots=[5072])
    def lifetime(self):return dict(mode='observe',first=1799,last=5999)

    def test_default_explicit_and_recorded_modes(self):
        settings=self.settings();saved=dict(settings)
        self.assertIsNone(w.configure(self.args(),'crusnusa',settings,None,None))
        self.assertEqual(settings,saved)
        result=w.configure(self.args('--candidate','test.exe','--exotica-host-waiting','observe'),
                           'crusnexo',settings,self.scene(),self.lifetime())
        self.assertEqual(result['last'],5999)
        self.assertEqual(w.configure(self.args(),'crusnexo',settings,self.scene(),self.lifetime()),result)
        self.assertEqual(w.configure(self.args('--candidate','test.exe','--exotica-host-waiting','off'),
                                    'crusnexo',settings,None,None),dict(mode='off'))
        self.assertEqual(settings['MIDZ_HOST_WAITING'],'0')

    def test_rejects_incomplete_wrong_game_and_incompatible_configuration(self):
        args=self.args('--candidate','test.exe','--exotica-host-waiting','observe')
        for key,value in [('MIDZ_GL','0'),('MIDZ_DEPTH_MIRROR','1'),('MIDZ_HOST_MATERIALS','0'),
                          ('MIDZ_HOST_ACTIVE','1'),('MIDZ_DEPTH_STREAM_FRAME','5073')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                w.configure(args,'crusnexo',self.settings()|{key:value},self.scene(),self.lifetime())
        for scene,lifetime in [(None,self.lifetime()),(self.scene()|{'future':0},self.lifetime()),
                               (self.scene(),None),(self.scene(),self.lifetime()|{'first':1800}),
                               (self.scene(),self.lifetime()|{'last':5998})]:
            with self.subTest(scene=scene,lifetime=lifetime),self.assertRaises(ValueError):
                w.configure(args,'crusnexo',self.settings(),scene,lifetime)
        with self.assertRaises(ValueError):w.configure(args,'offroadc',self.settings(),self.scene(),self.lifetime())
        with self.assertRaises(ValueError):w.configure(self.args('--exotica-host-waiting','observe'),'crusnexo',self.settings(),self.scene(),self.lifetime())
        args.headless=True
        with self.assertRaises(ValueError):w.configure(args,'crusnexo',self.settings(),self.scene(),self.lifetime())
        with self.assertRaises(ValueError):w.configure(self.args(),'crusnexo',{'MIDZ_HOST_WAITING':'2'},None,None)

    def fixture(self,root):
        realm=(1<<32)|0xa00080
        def event(op,**kw):return dict.fromkeys(life.FIELDS,0)|dict(event=op,frame=1800,time=31.5,epoch=1)|kw
        events=[event('L',slot=0x1100,reason=1172),
                event('A',slot=0x1100,sequence=1,generation=1,flags=1171),
                event('B',slot=0x1100,sequence=1,generation=1,owner=1,realm=realm,section=0xa01000,source=0xa02000),
                event('A',slot=0x1200,sequence=2,generation=2,flags=1170),
                event('B',slot=0x1200,sequence=2,generation=2,owner=2,realm=realm,section=0xa01000,source=0xa02006),
                event('D',slot=0x1200,sequence=2,generation=2,owner=2,realm=realm,section=0xa01000,source=0xa02006,reason=1)]
        row=dict(scene=1,frame=1800,device_time='31.500000000000',epoch=1,sequence=2,records=6,
                 historical=2,unowned=0,submitted=1,future=3,bound_future=0,bound_future_submitted=0,
                 candidates=1,instances=1,quads=1,hash=w.fingerprint(bytes(260)),guest_cycles=0)
        def csvfile(path,fields,rows):
            with path.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        csvfile(root/'exotica-lifetime-events.csv',life.FIELDS,events)
        csvfile(root/'exotica-waiting-scenes.csv',w.FIELDS,[row])
        csvfile(root/'exotica-host-scenes.csv',['scene','frame','device_time'],[{k:row[k] for k in ('scene','frame','device_time')}])
        prefix=root/'exotica-waiting-1800'
        Path(str(prefix)+'-owners.bin').write_bytes(struct.pack('<6Q',realm,0xa01000,0xa02000,0x1100,1,1))
        Path(str(prefix)+'-quads.bin').write_bytes(bytes(260))
        Path(str(prefix)+'-instances.bin').write_bytes(struct.pack('<11I',0xa01000,0xa02000,0xa03000,0x100,1,1,0x100,0x84003f,100,0,1))
        text=('MIDZ_LIFETIME=1 first=1799 last=5999\n'
              'MIDZ_LIFETIME_RESULT complete=1 records=6 transitions=2 bindings=2 emissions=10 owned=2 draws=1 first_draws=1 fading=0 opaque=0 epochs=1\n'
              'MIDZ_HOST_WAITING=1\n'
              'MIDZ_HOST_WAITING_RESULT complete=1 scenes=1 candidates=1 quads=1 snapshots=1 remaining=0\n')
        return dict(mode='observe',first=1800,last=5999,snapshots=[1800],lifetime=self.lifetime()),text

    def test_complete_registry_prefix_and_snapshot_ownership(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);trial,text=self.fixture(root)
            result=w.verify_receipt(trial,text,root)
            self.assertEqual(result['snapshot_owners_verified'],1)
            self.assertTrue(result['passed'])

    def test_rejects_bad_clock_counts_prefix_and_missing_completion(self):
        changes={'device_time':'nan','records':'7','sequence':'1','epoch':'2','candidates':'2',
                 'quads':'131073','instances':'2','historical':'1','bound_future':'4','guest_cycles':'1','hash':'0'*16}
        for key,value in changes.items():
            with self.subTest(key=key),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);trial,text=self.fixture(root);path=root/'exotica-waiting-scenes.csv'
                rows=w.bounded_rows(path,w.FIELDS);rows[0][key]=value
                with path.open('w',newline='') as stream:
                    writer=csv.DictWriter(stream,fieldnames=w.FIELDS);writer.writeheader();writer.writerows(rows)
                with self.assertRaises(ValueError):w.verify_receipt(trial,text,root)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);trial,text=self.fixture(root)
            for changed in (text+text,text.replace('snapshots=1','snapshots=0'),text.replace('MIDZ_HOST_WAITING=1',''),
                            text.replace('complete=1 scenes','complete=0 scenes')):
                with self.subTest(text=changed),self.assertRaises(ValueError):w.verify_receipt(trial,changed,root)

    def test_rejects_stale_or_submitted_owners_and_broken_instance_ranges(self):
        for change in ('generation','submitted','quad','range','orphan'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);trial,text=self.fixture(root)
                prefix=root/'exotica-waiting-1800'
                if change in ('generation','submitted'):
                    path=Path(str(prefix)+'-owners.bin');words=list(struct.unpack('<6Q',path.read_bytes()))
                    if change=='generation':words[-1]=2
                    else:words[2]=0xa02006;words[3]=0x1200;words[-1]=2
                    path.write_bytes(struct.pack('<6Q',*words))
                elif change=='quad':Path(str(prefix)+'-quads.bin').write_bytes(bytes(259))
                elif change=='range':
                    path=Path(str(prefix)+'-instances.bin');words=list(struct.unpack('<11I',path.read_bytes()))
                    words[-2]=1;path.write_bytes(struct.pack('<11I',*words))
                else:(root/'exotica-waiting-1801-owners.bin').write_bytes(b'')
                with self.assertRaises(ValueError):w.verify_receipt(trial,text,root)

    def test_disabled_mode_has_no_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertIsNone(w.verify_receipt(None,'',temp))
            root=Path(temp);self.fixture(root)
            with self.assertRaisesRegex(ValueError,'disabled'):w.verify_receipt(dict(mode='off'),'',root)

    def test_equal_timestamp_events_use_the_explicit_record_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);trial,text=self.fixture(root)
            path=root/'exotica-waiting-scenes.csv';rows=w.bounded_rows(path,w.FIELDS)
            rows[0]['records']='5'  # The first original draw is later at the SAME time.
            with path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=w.FIELDS);writer.writeheader();writer.writerows(rows)
            path=root/'exotica-waiting-1800-owners.bin'
            words=list(struct.unpack('<6Q',path.read_bytes()));words[2]=0xa02006;words[3]=0x1200;words[-1]=2
            path.write_bytes(struct.pack('<6Q',*words))
            path=root/'exotica-waiting-1800-instances.bin'
            words=list(struct.unpack('<11I',path.read_bytes()));words[1]=0xa02006
            path.write_bytes(struct.pack('<11I',*words))
            self.assertTrue(w.verify_receipt(trial,text,root)['passed'])


if __name__=='__main__':unittest.main()
