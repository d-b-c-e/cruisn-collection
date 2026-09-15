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
            for index in (0,3,4,7,10,12,16,17,53,1000,len(words)-1):
                changed=list(words);changed[index]^=1;write(changed,lines)
                with self.subTest(index=index),self.assertRaises(ValueError):b.verify(trial,root)
            for records in (lines[:2],lines+[lines[1]],[lines[0],lines[1],lines[2].replace('complete=1','complete=0')]):
                write(words,records)
                with self.assertRaises(ValueError):b.verify(trial,root)
            write(words[:-1],lines)
            with self.assertRaises(ValueError):b.verify(trial,root)

if __name__=='__main__':unittest.main()
