import argparse
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import zeus_depth_mirror as D


class DepthMirrorTests(unittest.TestCase):
    def args(self,**kwargs):
        values=dict(zeus_depth_mirror=None,zeus_depth_first=None,zeus_depth_last=None,
            zeus_depth_snapshots=None,candidate='candidate.exe',headless=False,native_renderer=False,until_frame=20)
        values.update(kwargs);return argparse.Namespace(**values)

    def test_old_recording_and_explicit_roundtrip(self):
        settings={'MIDZ_GL':'1','MIDV_GL_CRT':'1'};before=copy.deepcopy(settings)
        self.assertIsNone(D.configure(self.args(),'crusnexo',settings,30));self.assertEqual(settings,before)
        trial=D.configure(self.args(zeus_depth_mirror='observe',zeus_depth_first=2,zeus_depth_last=4,zeus_depth_snapshots='4,2'),'crusnexo',settings,30)
        inherited=D.configure(self.args(),'crusnexo',settings,30)
        self.assertEqual(trial['snapshots'],[2,4]);self.assertFalse(inherited['explicit'])
        self.assertEqual(trial['first'],inherited['first'])
        D.configure(self.args(zeus_depth_mirror='off'),'crusnexo',settings,30);self.assertEqual(settings,before)

    def test_bounds_and_incompatible_paths(self):
        base=dict(zeus_depth_mirror='observe',zeus_depth_first=2,zeus_depth_last=4)
        for changes in (dict(candidate=None),dict(zeus_depth_first=0),dict(zeus_depth_last=20),dict(headless=True),
                dict(zeus_depth_snapshots='2,2'),dict(zeus_depth_snapshots='5'),dict(zeus_depth_snapshots='2,')):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                D.configure(self.args(**(base|changes)),'crusnexo',{'MIDZ_GL':'1'},30)
        for rom,settings in [('crusnwld',{'MIDZ_GL':'1'}),('crusnexo',{'MIDZ_GL':'1','MIDZ_HOST_ACTIVE':'2'})]:
            with self.assertRaises(ValueError):D.configure(self.args(**base),rom,settings,30)

    def test_independent_depth_and_color_mismatches(self):
        color=bytes(range(16));original=struct.pack('<4I',0,0x12345612,0xfffffeff,0xffffffff)
        mapped=struct.pack('<4f',0,0x123456/67108864,0xfffffe/67108864,1)
        self.assertTrue(D.compare_buffers(color,color,original,mapped)['passed'])
        self.assertEqual(D.compare_buffers(color,b'\xff'+color[1:],original,mapped)['color_differences'],1)
        wrong=struct.pack('<f',float('nan'))+mapped[4:]
        self.assertEqual(D.compare_buffers(color,color,original,wrong)['depth_differences'],1)
        with self.assertRaises(ValueError):D.compare_buffers(b'',b'',b'',b'')
        with self.assertRaises(ValueError):D.compare_buffers(color,color,original,mapped[:-1])

    def test_completion_and_frame_coverage(self):
        trial=dict(enabled=True,first=2,last=4,snapshots=[])
        text=('MIDZ_DEPTH_MIRROR=1 first=2 last=4 snapshots=0\n'
            'MIDZ_DEPTH_MIRROR_RESULT complete=1 frames=3 batches=6 vertices=36 clears=1 snapshots=0 remaining=0\n'
            'MIDZ_DEPTH_MIRROR_WRITER submitted=0 written=0 failed=0 rejected=0 peak_bytes=0 write_total_us=0 write_max_us=0 drain_us=0 waits=0 wait_us=0\n')
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'zeus-depth-mirror.csv'
            fields='frame,width,height,batches,vertices,clears,snapshot,color_differences,depth_differences,mirror_us,snapshot_us'
            valid=fields+'\n'+''.join(f'{frame},512,1024,6,36,1,0,0,0,1,0\n' for frame in (2,3,4))
            path.write_text(valid,encoding='utf-8')
            self.assertTrue(D.verify_receipt(trial,text,temp)['passed'])
            for bad in (text.replace('complete=1','complete=0'),text.replace('written=0','written=1'),text.replace('frames=3','frames=2'),text+text):
                with self.assertRaises(ValueError):D.verify_receipt(trial,bad,temp)
            path.write_text(valid.replace('3,512,1024,6,36,1,0,0,0,1,0\n',''),encoding='utf-8')
            with self.assertRaises(ValueError):D.verify_receipt(trial,text,temp)
            with self.assertRaises(ValueError):D.verify_receipt(None,text,temp)


if __name__=='__main__':unittest.main()
