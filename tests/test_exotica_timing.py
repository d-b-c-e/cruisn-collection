import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_timing import configure,verify

class Timing(unittest.TestCase):
    def test_explicit_bounds_and_game(self):
        args=SimpleNamespace(exotica_timing='7800:7830',candidate='test.exe',headless=False,native_renderer=False)
        settings=dict(MIDZ_HOST_SCENE='1',MIDZ_GL='1',MIDV_FFB='0')
        trial=configure(args,'crusnexo',settings,8209)
        self.assertEqual(trial['last'],7830)
        for value in ('1:2001','0:1','2:1','1:8208','1:2x'):
            args.exotica_timing=value
            with self.assertRaises(ValueError):configure(args,'crusnexo',settings,8209)
        args.exotica_timing=None
        with self.assertRaisesRegex(ValueError,'inherited'):configure(args,'crusnexo',settings,8209)
        args.exotica_timing='1:2'
        with self.assertRaises(ValueError):configure(args,'offroadc',settings,8209)

    def test_receipt_and_missing_duplicate_measurements(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);trial=dict(first=10,last=12,scope='CPU only')
            log='MIDZ_HOST_TIMING first=10 last=12\nMIDZ_HOST_TIMING_RESULT complete=1 rows=1 final_frame=14\n'
            (root/'stderr.log').write_text(log,encoding='utf-8')
            with self.assertRaises(ValueError):verify(trial,root)
            data='frame,scene,phase,microseconds,units\n10,1,source,2.5,5\n'
            (root/'exotica-host-timing.csv').write_text(data,encoding='utf-8')
            self.assertTrue(verify(trial,root)['passed'])
            with self.assertRaises(ValueError):verify(None,root)
            (root/'exotica-host-timing.csv').write_text(data+'11,1,source,2.5,5\n',encoding='utf-8')
            (root/'stderr.log').write_text(log.replace('rows=1','rows=2'),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'duplicate'):verify(trial,root)
            (root/'stderr.log').write_text(log.replace('complete=1','complete=0'),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'incomplete'):verify(trial,root)

if __name__=='__main__':unittest.main()
