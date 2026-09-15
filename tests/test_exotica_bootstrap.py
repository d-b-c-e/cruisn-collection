from pathlib import Path
from types import SimpleNamespace
import struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_bootstrap as b

class BootstrapTests(unittest.TestCase):
    def test_explicit_candidate_and_ffb(self):
        args=SimpleNamespace(candidate='test.exe',exotica_bootstrap='observe')
        self.assertFalse(b.configure(args,'crusnexo',{'MIDV_FFB':'0'},2100)['changes_startup'])
        for rom,settings in [('crusnusa',{'MIDV_FFB':'0'}),('crusnexo',{'MIDV_FFB':'1'}),('crusnexo',{})]:
            with self.assertRaises(ValueError):b.configure(args,rom,settings,2100)
        with self.assertRaises(ValueError):b.configure(SimpleNamespace(),'crusnexo',{b.KEY:'1'},2100)
        self.assertIsNone(b.configure(SimpleNamespace(),'crusnexo',{},2100))

    def test_lifetime_activation_requires_captured_proof_and_earlier_boundary(self):
        args=SimpleNamespace(candidate='test.exe',exotica_bootstrap='lifetimes')
        for settings in ({'MIDV_FFB':'0'},{'MIDV_FFB':'0','MIDZ_LIFETIME':'1','MIDZ_HOST_JOURNALS':'quiet'}):
            with self.assertRaises(ValueError):b.configure(args,'crusnexo',settings,5300)
        settings={'MIDV_FFB':'0','MIDZ_LIFETIME':'1'}
        trial=b.configure(args,'crusnexo',settings,5300)
        self.assertEqual(settings[b.KEY],'2')
        life=dict(mode='observe',first=1799,last=5298)
        proof=dict(passed=True,changes_startup=True,frame=1385,base=112061)
        resolved=b.lifetime_trial(trial,proof,life)
        self.assertEqual((resolved['first'],resolved['requested_first'],resolved['bootstrap_base']),(1385,1799,112061))
        self.assertEqual(life['first'],1799)
        for bad in (None,dict(proof,passed=False),dict(proof,changes_startup=False),dict(proof,frame=1800)):
            with self.assertRaises(ValueError):b.lifetime_trial(trial,bad,life)

    def test_scene_configuration_and_atomic_resolution(self):
        from exotica_journals import REQUIRED
        args=SimpleNamespace(candidate='test.exe',exotica_bootstrap='scenes')
        settings=dict(REQUIRED,MIDZ_DEPTH_FIRST='2',MIDZ_HOST_FIRST='1800',MIDZ_MODEL_ENDPOINT_FIRST='1800',MIDZ_MODEL_ADMIT_FIRST='1800')
        for key in (*REQUIRED,'MIDZ_DEPTH_FIRST'):
            with self.subTest(key=key),self.assertRaises(ValueError):b.configure(args,'crusnexo',dict(settings,**{key:'bad'}),5300)
        trial=b.configure(args,'crusnexo',settings,5300)
        self.assertEqual(settings[b.KEY],'3')
        scene=dict(first=1800,compose=True,early_visibility=dict(first=1800,last=5288))
        waiting=dict(first=1800,mode='observe');handover=dict(mode='draw',waiting=waiting,early_visibility=dict(scene['early_visibility']))
        endpoint=dict(mode='draw',first=1800,admit_from=1800)
        proof=dict(passed=True,frame=1385,scene_frame=1400)
        with self.assertRaises(ValueError):b.resolve_scenes(trial,dict(proof,scene_frame=1801),scene,waiting,handover,endpoint)
        self.assertEqual(scene['first'],1800)
        b.resolve_scenes(trial,proof,scene,waiting,handover,endpoint)
        self.assertEqual((scene['first'],waiting['first'],endpoint['first'],endpoint['admit_from']),(1400,)*4)
        self.assertEqual(handover['early_visibility']['first'],1400)
        self.assertEqual(handover['waiting']['first'],1400)

    def test_proof_and_missing_or_wrong_transaction(self):
        base=0x20000;tail=base+1200*31
        words=[0x31534258,1,600,600,base,len(b.CODE),1201,0xbbc9,0xbbd5,tail,tail,0,0xffffffff,base,1200,0]
        words+=[v for pair in b.CODE for v in pair]+[base+(i+1)*31 for i in range(1200)]+[0]
        lines=['MIDZ_BOOTSTRAP=1',f'MIDZ_BOOTSTRAP_READY begin=600 frame=600 base={base} links=1201','MIDZ_BOOTSTRAP_RESULT complete=1 frame=600']
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);trial=dict(frames=2100)
            def write(data,records):
                (root/'exotica-bootstrap.bin').write_bytes(struct.pack('<'+'I'*len(data),*data))
                (root/'stdout.log').write_text(records[0]+'\n',encoding='utf-8')
                (root/'stderr.log').write_text('\n'.join(records[1:])+'\n',encoding='utf-8')
            write(words,lines);self.assertEqual(b.verify(trial,root)['bytes'],5012)
            write(words,['MIDZ_BOOTSTRAP=2',*lines[1:]])
            self.assertTrue(b.verify(dict(trial,mode='lifetimes'),root)['changes_startup'])
            with self.assertRaises(ValueError):b.verify(trial,root)
            for index in (0,3,4,7,10,12,16,17,53,1000,len(words)-1):
                changed=list(words);changed[index]^=1;write(changed,lines)
                with self.subTest(index=index),self.assertRaises(ValueError):b.verify(trial,root)
            for records in (lines[:2],lines+[lines[1]],[lines[0],lines[1],lines[2].replace('complete=1','complete=0')]):
                write(words,records)
                with self.assertRaises(ValueError):b.verify(trial,root)
            write(words[:-1],lines)
            with self.assertRaises(ValueError):b.verify(trial,root)
            st=dict(trial,mode='scenes',latest_scene_start=1799)
            write(words,['MIDZ_BOOTSTRAP=3',*lines[1:], 'MIDZ_BOOTSTRAP_SCENE frame=605 scene=1'])
            sp=[0x31534358,1,605,600,0x67f6,0xff2,0xffffffff,0xffffffff,0x67f5,0x15200ff2,0x681f,0x082fbbb5,0x6835,0x082fbbb9,1,0]
            path=root/'exotica-bootstrap-scene.bin'
            path.write_bytes(struct.pack('<16I',*sp))
            self.assertEqual(b.verify(st,root)['scene_frame'],605)
            for i in range(16):
                bad=list(sp);bad[i]^=1;path.write_bytes(struct.pack('<16I',*bad))
                with self.subTest(scene_word=i),self.assertRaises(ValueError):b.verify(st,root)
            path.unlink()
            with self.assertRaises(ValueError):b.verify(st,root)

if __name__=='__main__':unittest.main()
