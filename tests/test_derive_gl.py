from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from derive_case import configure_gl


class DeriveGlTests(unittest.TestCase):
    def test_capture_is_explicit_bounded_and_uses_the_games_renderer(self):
        settings={'MIDV_GL':'1','MIDZ_GL':'0'}
        self.assertIsNone(configure_gl(settings,'crusnusa',None,60,6000))
        self.assertNotIn('MIDV_GL_SNAP',settings)
        self.assertEqual(configure_gl(settings,'crusnusa','2500:4300',100,5012),list(range(2500,4301,100)))
        self.assertEqual(settings['MIDV_GL_SNAP_MAX'],'19')
        for interval,every in (('1:5011',60),('20:10',60),('1:100',0)):
            with self.assertRaises(ValueError):configure_gl(settings,'crusnusa',interval,every,5012)
        with self.assertRaises(ValueError):configure_gl(settings,'crusnexo','1:100',60,5012)
        settings={'MIDZ_GL':'1'}
        self.assertEqual(configure_gl(settings,'crusnexo','60:180',60,6000),[60,120,180])
        self.assertEqual(settings['MIDZ_GL_SNAP_LAST'],'180')
