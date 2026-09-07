from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from launch_history import archive_previous, write_receipt


class LaunchHistoryTests(unittest.TestCase):
    def test_retry_keeps_prior_receipts_bounded_logs_and_unowned_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); rig=root/'rig'; binary=root/'bin'
            rig.mkdir(); binary.mkdir()
            unrelated=rig/'launch-history'/'user-notes'
            unrelated.mkdir(parents=True); (unrelated/'keep.txt').write_text('keep')
            (binary/'midv_gl.log').write_bytes(b'0123456789')
            (binary/'midv_ffb.log').write_bytes(b'force log')
            for i in range(4):
                (rig/'launch.log').write_text(f'launch {i}')
                write_receipt(rig,['vunit','crusnwld24','-view','Screen 0'],
                              {'MIDV_GL_SCALE':str(i+1),'UNRELATED_SECRET':'private'})
                archive_previous(rig,binary,keep=2,limit=8)
            owned=sorted(p for p in (rig/'launch-history').iterdir() if p.name!='user-notes')
            self.assertEqual(len(owned),2)
            self.assertEqual([p.joinpath('launch.log').read_text() for p in owned],['launch 2','launch 3'])
            self.assertEqual((owned[-1]/'midv_gl.log').read_bytes(),b'23456789')
            self.assertEqual((owned[-1]/'midv_ffb.log').read_bytes(),b'orce log')
            metadata=json.loads((owned[-1]/'archive.json').read_text())
            self.assertTrue(metadata['midv_gl.log']['tail_only'])
            self.assertEqual((unrelated/'keep.txt').read_text(),'keep')
            receipt=json.loads((rig/'launch.json').read_text())
            self.assertEqual(receipt['environment'],{'MIDV_GL_SCALE':'4'})
            self.assertEqual(receipt['command'][-2:],['-view','Screen 0'])

    def test_force_csv_tail_keeps_header_and_complete_final_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'launch.log').write_text('launch')
            header=b'ms,output,value\n'
            rows=b''.join(f'{n},shaped,{n}\n'.encode() for n in range(30))
            (root/'ffb_trace.csv').write_bytes(header+rows)
            archive_previous(root,root,limit=100)
            archive=next((root/'launch-history').iterdir())
            data=(archive/'ffb_trace.csv').read_bytes()
            self.assertLessEqual(len(data),100)
            self.assertTrue(data.startswith(header))
            self.assertTrue(data.endswith(b'29,shaped,29\n'))
            self.assertTrue(all(line in rows.splitlines() for line in data.splitlines()[1:]))
            self.assertTrue(json.loads((archive/'archive.json').read_text())['ffb_trace.csv']['tail_only'])
