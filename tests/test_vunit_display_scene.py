from pathlib import Path
import json,sys,tempfile,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from vunit_display_scene import RECORD,select,load


class DisplaySceneTests(unittest.TestCase):
    def fixture(self):
        data=np.zeros(10,dtype=RECORD)
        data['frame']=[10,11,12,13,14,15,16,17,18,19]
        data['page']=[513,513,516,516,513,513,516,516,513,513]
        data['dma'][:,0]=np.arange(10)
        return data,dict(frame=18,ordinary_quads=8,visible_page=0)

    def test_consumed_prefix_selects_visible_not_latest_draw_or_later_producer(self):
        data,receipt=self.fixture();scene=select(data,receipt)
        self.assertEqual(scene.current[:,0].tolist(),[4,5])
        self.assertEqual(scene.history[:,0].tolist(),[0,1])
        self.assertEqual(scene.report['excluded_unconsumed_commands'],2)
        self.assertFalse(scene.report['pixel_reproduction_verified'])
        receipt['visible_page']=1;scene=select(data,receipt)
        self.assertEqual(scene.current[:,0].tolist(),[6,7])
        self.assertEqual(scene.history[:,0].tolist(),[2,3])

    def test_count_can_fence_a_partially_consumed_group(self):
        data,receipt=self.fixture();receipt.update(ordinary_quads=5,frame=14)
        scene=select(data,receipt);self.assertEqual(scene.current[:,0].tolist(),[4])
        self.assertEqual(scene.report['current']['end_record_exclusive'],5)

    def test_physical_page_comes_from_draw_bit_not_display_control_bit(self):
        data,receipt=self.fixture();data['page'][4:6]=512
        scene=select(data,receipt);self.assertEqual(scene.current[:,0].tolist(),[4,5])
        self.assertEqual(scene.history[:,0].tolist(),[0,1])

    def test_bad_receipts_and_nonmonotonic_journal_reject(self):
        data,receipt=self.fixture()
        for change in [dict(frame=16),dict(ordinary_quads=11),dict(ordinary_quads=0),
                       dict(ordinary_quads=True),dict(visible_page=2),dict(frame=-1)]:
            with self.subTest(change=change),self.assertRaises(ValueError):select(data,dict(receipt,**change))
        data['frame'][2]=9
        with self.assertRaisesRegex(ValueError,'frame order'):select(data,receipt)

    def test_file_magic_and_partial_record_reject_without_silent_truncation(self):
        data,receipt=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'capture').mkdir()
            (root/'vunit-mirror.json').write_text(json.dumps(receipt))
            path=root/'capture/quads.bin';path.write_bytes(b'MVQ1'+data.tobytes())
            scene=load(root);self.assertEqual(scene.current[:,0].tolist(),[4,5])
            # Release mapped views before modifying this Windows file.
            del scene
            path.write_bytes(b'BAD!'+data.tobytes())
            with self.assertRaisesRegex(ValueError,'magic'):load(root)
            path.write_bytes(b'MVQ1'+data.tobytes()+b'\0')
            with self.assertRaisesRegex(ValueError,'incomplete'):load(root)


if __name__=='__main__':unittest.main()
