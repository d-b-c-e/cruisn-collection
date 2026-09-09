import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_world_host import compare, scene_summary, hash_quad, HASH_SEED, QUAD_FIELDS


class HostEvidenceTests(unittest.TestCase):
    def test_summary_cost_and_fingerprint_are_checked_against_detailed_trace(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/'a',Path(td)/'b'
            for p in (a,b):self.fixture(p,'black')
            words=[256,512,246,189,266,189,266,210,246,210,0,16,4112,4096,96,0]
            digest=f'{hash_quad(HASH_SEED,words):016x}'
            header='frame,page,mode,pending,unsupported,distance,decoded,quads,microseconds,quad_trace,quads_hash,guard_us,prepare_us,pack_us,quad_log_us,submit_us,previous_scene_log_us\n'
            detailed=header+f'1,513,2,1,0,0,1,1,100,1,{digest},1,10,2,80,7,0\n'
            summary=header+f'1,513,2,1,0,0,1,1,20,0,{digest},1,10,2,0,7,0\n'
            (a/'run/world-host-scenes.csv').write_text(detailed)
            (b/'run/world-host-scenes.csv').write_text(summary)
            (a/'run/world-host-quads.csv').write_text('frame,page,'+','.join(QUAD_FIELDS)+'\n1,513,'+','.join(map(str,words))+'\n')
            (b/'run/world-host-quads.csv').unlink()
            result=compare(a,b,expect_gl='equal',require_host_equal=True)
            self.assertTrue(result['passed']);self.assertTrue(result['host_scene_fingerprints_equal'])
            self.assertEqual(result['scenes'][1]['geometry_evidence'],'ordered fingerprint only')
            self.assertEqual(result['scenes'][0]['phases']['quad_log_us']['p99'],80)
            (b/'run/world-host-scenes.csv').write_text(summary.replace(digest,'0'*16))
            self.assertFalse(compare(a,b,expect_gl='equal',require_host_equal=True)['passed'])
            (a/'run/world-host-scenes.csv').write_text(detailed.replace(digest,'0'*16))
            with self.assertRaisesRegex(ValueError,'fingerprint'):scene_summary(a/'run')
            (b/'run/world-host-scenes.csv').write_text(summary.replace(',20,0,',',21,0,'))
            with self.assertRaisesRegex(ValueError,'sum'):scene_summary(b/'run')
            (b/'run/world-host-scenes.csv').write_text(summary.replace(',10,2,',',nan,2,'))
            with self.assertRaisesRegex(ValueError,'cost'):scene_summary(b/'run')

    def fixture(self, root, color):
        run=root/'run'; (run/'gl-snap').mkdir(parents=True)
        (root/'report.json').write_text(json.dumps({'passed': True, 'comparison': {'passed': True}}))
        (run/'world-host-scenes.csv').write_text('frame,page,mode,pending,unsupported,distance,decoded,quads,microseconds\n1,513,2,1,0,0,1,1,100\n')
        (run/'world-host-quads.csv').write_text('frame,page,object\n1,513,123\n')
        (run/'world-camera.csv').write_text('frame,x,y,z\n1,1,2,3\n')
        (run/'world-adc.csv').write_text('frame,time,pc,value\n1,0.1,123,45\n')
        (run/'frames.csv').write_text('frame,emulated_seconds,host_seconds,speed_percent,:WHEEL\n1,0.1,0.2,100,128\n')
        (run/'gl-snap/captures.csv').write_text('file,last_received_frame,width,height,dropped_messages,completed_frame\nframe.png,1,2,2,0,1\n')
        Image.new('RGB',(2,2),color).save(run/'gl-snap/frame.png')

    def test_changed_pixels_require_original_motion_and_adc_times(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/'a',Path(td)/'b'
            self.fixture(a,'black');self.fixture(b,'white')
            result=compare(a,b,expect_gl='changed')
            self.assertTrue(result['passed']);self.assertFalse(result['gl']['passed'])
            self.assertFalse(compare(a,b,expect_gl='equal')['passed'])
            adc=b/'run/world-adc.csv';adc.write_text(adc.read_text().replace('0.1','0.2'))
            self.assertFalse(compare(a,b,expect_gl='changed')['passed'])

    def test_geometry_receipts_cannot_disagree_or_lose_stream_messages(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/'a',Path(td)/'b'
            self.fixture(a,'black');self.fixture(b,'black')
            self.assertTrue(compare(a,b,expect_gl='equal')['passed'])
            scenes=b/'run/world-host-scenes.csv';original=scenes.read_text()
            scenes.write_text(original.replace('1,100','2,100'))
            with self.assertRaisesRegex(ValueError,'counts'):compare(a,b,expect_gl='equal')
            scenes.write_text(original)
            receipt=b/'run/gl-snap/captures.csv'
            receipt.write_text(receipt.read_text().replace('2,2,0,1','2,2,1,1'))
            with self.assertRaisesRegex(ValueError,'lost'):compare(a,b,expect_gl='equal')


if __name__=='__main__':unittest.main()
