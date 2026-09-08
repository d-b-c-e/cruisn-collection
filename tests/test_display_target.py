import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from display_target import choose


class CaptureDisplayTests(unittest.TestCase):
    def test_4k_reference_cannot_silently_choose_a_1080p_monitor(self):
        reference={5400:{'size':[3840,2160]},5401:{'size':[3840,2160]}}
        available=[{'device':'secondary','primary':False,'size':[1920,1080]},
                   {'device':'primary','primary':True,'size':[3840,2160]}]
        self.assertEqual(choose(reference,available)['selected']['device'],'primary')
        with self.assertRaisesRegex(ValueError,'No display matches'):choose(reference,available[:1])

    def test_variable_reference_size_fails_before_launch(self):
        with self.assertRaisesRegex(ValueError,'fixed presentation size'):
            choose({1:{'size':[1920,1080]},2:{'size':[3840,2160]}},[])
