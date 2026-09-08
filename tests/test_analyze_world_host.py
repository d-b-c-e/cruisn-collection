import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_world_host import compare


class HostEvidenceTests(unittest.TestCase):
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
