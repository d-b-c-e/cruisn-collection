from pathlib import Path
from types import SimpleNamespace
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_shutdown as shutdown

class ShutdownTests(unittest.TestCase):
    def fixture(self):
        rows={k:dict.fromkeys(v,0) for k,v in shutdown.FIELDS.items()}
        rows['CPU'].update(frame=1400,prepared=8,matched=8,requested=8,completed=8)
        rows['GPU']['frame']=1399
        rows['JOIN'].update(read=1048576,written=1048576,joined=1)
        return rows

    def verify(self,rows,extra=''):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)
            (path/'stdout.log').write_text(shutdown.KEY+'=1\n',encoding='utf-8')
            (path/'stderr.log').write_text('\n'.join('MIDZ_SHUTDOWN_'+k+' '+' '.join(f'{f}={v}' for f,v in row.items()) for k,row in rows.items())+'\n'+extra,encoding='utf-8')
            return shutdown.verify(dict(mode='observe'),path)

    def test_quiescent_interrupted_and_failed_are_distinct(self):
        rows=self.fixture();self.assertEqual(self.verify(rows)['classification'],'quiescent')
        rows['CPU']['scene_open']=1;rows['JOIN']['written']+=8
        result=self.verify(rows);self.assertEqual(result['classification'],'interrupted');self.assertEqual(result['queued_bytes'],8)
        rows['GPU']['writer_failed']=1
        self.assertEqual(self.verify(rows)['classification'],'failed')

    def test_rejects_missing_malformed_or_inconsistent_receipts(self):
        for tag,key,value in (('CPU','scene_open',2),('CPU','matched',9),('CPU','completed',9),
                              ('GPU','frame',1402),('JOIN','read',1048584),('JOIN','joined',0),
                              ('JOIN','written',1048577),('JOIN','written',2**64)):
            rows=self.fixture();rows[tag][key]=value
            with self.subTest(tag=tag,key=key),self.assertRaises(ValueError):self.verify(rows)
        with self.assertRaises(ValueError):self.verify(self.fixture(),'MIDZ_SHUTDOWN_OBSERVE=1\n')

    def test_configuration_requires_explicit_ready_candidate(self):
        args=SimpleNamespace(candidate='test.exe',exotica_shutdown='observe')
        settings=dict(MIDV_FFB='0',MIDZ_BOOTSTRAP='3')
        self.assertFalse(shutdown.configure(args,'crusnexo',settings)['changes_shutdown'])
        for key in ('MIDV_FFB','MIDZ_BOOTSTRAP'):
            with self.assertRaises(ValueError):shutdown.configure(args,'crusnexo',dict(settings,**{key:'bad'}))
        with self.assertRaises(ValueError):shutdown.configure(SimpleNamespace(),'crusnexo',settings)

if __name__=='__main__':unittest.main()
