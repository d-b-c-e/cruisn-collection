from pathlib import Path
import argparse,struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import zeus_command_stream as J
import zeus_depth_mirror as D

def record(kind,payload):return struct.pack('<2I',kind,len(payload))+payload
def header():return struct.pack('<10I',J.MAGIC,1,3,2736,4096,86,4,255,13,0)
def end(frame=3):return record(6,struct.pack('<2Id',0,frame,.5))

class CommandStreamTests(unittest.TestCase):
    def test_ordered_upload_and_completion(self):
        raw=header()+record(6,struct.pack('<I',0x1900000))+record(5,struct.pack('<2I',16777214,2)+b'ab')+record(2,bytes(1024))+end()
        h,r=J.parse(raw);self.assertEqual(h['frame'],3);self.assertEqual([k for k,_ in r],[6,5,2,6])
        text=f'MIDZ_DEPTH_STREAM_RESULT complete=1 frame=3 commands=4 bytes={len(raw)} written=3 failed=0 rejected=0\n'
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            for k,v in dict(wave=bytes(16777216),palette=bytes(262144),records=raw).items():(p/f'zeus-stream-3-{k}.bin').write_bytes(v)
            r=J.verify(3,text,p);self.assertTrue(r['passed']);self.assertEqual(r['upload_bytes'],2)
            for bad in (text.replace('complete=1','complete=0'),text.replace('written=3','written=2'),text.replace('commands=4','commands=3'),text+text):
                with self.assertRaises(ValueError):J.verify(3,bad,p)
            with self.assertRaises(ValueError):J.verify(None,text,p)

    def test_corruption_and_missing_end_are_rejected(self):
        good=header()+end();self.assertEqual(J.parse(good)[0]['scale'],4)
        cases=[good[:-1],header(),header()+record(6,bytes(4)),header()+end(4),good+end(),header()+record(7,b'abc')+end(),
            header()+record(5,struct.pack('<2I',16777215,2)+b'ab')+end(),header()+record(5,struct.pack('<2I',0,0))+end(),
            header()+record(2,bytes(1023))+end(),header()+record(6,struct.pack('<2Id',0,3,float('nan')))]
        for offset,value in ((0,0),(4,2),(12,1),(20,121),(24,5),(28,256),(32,16),(36,1)):
            b=bytearray(good);struct.pack_into('<I',b,offset,value);cases.append(bytes(b))
        for b in cases:
            with self.subTest(bytes=len(b)),self.assertRaises(ValueError):J.parse(b)

    def test_stream_controls_require_both_snapshots_and_preserve_absent(self):
        base=dict(zeus_depth_mirror='wide',zeus_depth_first=2,zeus_depth_last=4,zeus_depth_snapshots='2,3',zeus_depth_stream_frame=3,
            candidate='candidate.exe',until_frame=20,headless=False,native_renderer=False)
        settings={'MIDZ_GL':'1'};trial=D.configure(argparse.Namespace(**base),'crusnexo',settings,20)
        self.assertEqual(trial['stream_frame'],3);self.assertEqual(settings['MIDZ_DEPTH_STREAM_FRAME'],'3')
        inherited=D.configure(argparse.Namespace(candidate='candidate.exe'),'crusnexo',settings,20)
        self.assertEqual(inherited['stream_frame'],3)
        for extra in ({'zeus_depth_stream_frame':2},{'zeus_depth_snapshots':'3'},{'zeus_depth_stream_frame':5},{'zeus_depth_mirror':None},{'zeus_depth_mirror':'off'}):
            with self.subTest(extra=extra),self.assertRaises(ValueError):D.configure(argparse.Namespace(**(base|extra)),'crusnexo',{'MIDZ_GL':'1'},20)
        D.configure(argparse.Namespace(zeus_depth_mirror='off',candidate='candidate.exe'),'crusnexo',settings,20)
        self.assertEqual(settings,{'MIDZ_GL':'1'})

if __name__=='__main__':unittest.main()
