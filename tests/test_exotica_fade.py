import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from verify_exotica_fade import step,verify

class ExoticaFade(unittest.TestCase):
    def test_known_render_steps_and_completion_preserve_low_words(self):
        self.assertEqual(step(0x78081234,0x04000130,8),(0x78101234,0x04000130,False))
        self.assertEqual(step(0x10f01234,0x04000130,8),(0x04f81234,0x30,True))
        self.assertEqual(step(0x05f61234,0x04008130,1),(0x04f71234,0x8030,True))
        for values in [(0,0,8),(0x00fa0000,0x04000100,8),(0,0x04000100,0),(-1,0x04000100,8),(True,0x04000100,8)]:
            with self.assertRaises(ValueError):step(*values)

    def test_capture_rejects_incomplete_corrupt_or_unbounded_evidence(self):
        row=dict(id=1,frame=3500,native_frame=3499,time=61.2,object=0x2000,
            before=0x78081234,flags_before=0x04000130,increment=8,actual=0x78101234,flags_after=0x04000130)
        receipt=dict(complete=True,events=1,error=None,windows=[[3500,3510]])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            def write(r,e):
                (p/'exotica-fade-capture.json').write_text(json.dumps(r),encoding='utf-8')
                (p/'exotica-fade-events.jsonl').write_text(json.dumps(e)+'\n',encoding='utf-8')
            write(receipt,row);self.assertEqual(verify(p)['counts'],dict(continuing=1,increment_8=1))
            for change in [dict(actual=0),dict(flags_after=0),dict(id=2),dict(time=float('nan')),dict(native_frame=3498),dict(object=0x40000),dict(frame=3511,native_frame=3511)]:
                write(receipt,dict(row,**change))
                with self.assertRaises(ValueError):verify(p)
            for change in [dict(complete=False),dict(events=0),dict(error='unfinished'),dict(windows=[]),dict(windows=[[3500,3740]]),dict(windows=[[3500,3510],[3505,3515]])]:
                write(dict(receipt,**change),row)
                with self.assertRaises(ValueError):verify(p)

if __name__=='__main__':unittest.main()
