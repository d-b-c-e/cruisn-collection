from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from run_regressions import validate,visual_content


class RegressionSuiteTests(unittest.TestCase):
    def test_blank_framebuffer_is_not_a_visual_oracle(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            Image.new('RGB',(16,16),'black').save(path/'last.png')
            with self.assertRaises(ValueError):visual_content(path)
            image=Image.new('RGB',(16,16),'black');image.putpixel((1,1),(255,255,255));image.save(path/'last.png')
            self.assertEqual(visual_content(path)['files'],1)

    def test_incomplete_or_impossible_suites_are_rejected(self):
        for plan in ({'schema':1,'cases':[]},{'schema':1,'cases':[{'id':'../out'}]},
                     {'schema':1,'cases':[{'id':'x'},{'id':'x'}]},
                     {'schema':1,'cases':[{'id':'x','compare_gl':True,'presentation':'headless'}]}):
            with self.assertRaises(ValueError):validate(plan)
