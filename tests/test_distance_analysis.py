from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_distance import summarize


class DistanceAnalysisTests(unittest.TestCase):
    def test_far_extension_counts_candidates_without_counting_sentinels(self):
        def row(obj,z,model='near',base='near'):
            return dict(object=obj,frame='1',depth_minus_radius=str(z),far_limit='80000',model=model,base_model=base)
        rows=[row('a',75000),row('a',81000,'middle'),row('b',159999),row('c',160001),row('sentinel',2147483551)]
        report=summarize(rows)
        self.assertEqual(report['samples_newly_admitted_by_doubling_far_limit'],2)
        self.assertEqual(report['objects_newly_admitted_by_doubling_far_limit'],['a','b'])
        self.assertEqual(report['samples_still_beyond_doubled_far_limit'],2)
        self.assertEqual(len(report['model_transitions']),1)
        with self.assertRaises(ValueError):summarize([])
