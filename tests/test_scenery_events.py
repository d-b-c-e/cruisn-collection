from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_scenery_events import rank


class SceneryEventTests(unittest.TestCase):
    def test_initial_and_offscreen_bounds_do_not_outrank_measured_mountain(self):
        mountain=dict(scene=15,first_frame=2027,last_frame=2027,object=0x13e40,
                      model=0xcb1a8b,previous_model=0,object_flags=0x1000,
                      event='first_submission',x0=167,y0=95,x1=274,y1=198,
                      depth_minus_radius=79839,first_far_observation=1999)
        initial=dict(mountain,event='initial_observation',x0=0,x1=511,y0=0,y1=399)
        offscreen=dict(mountain,x0=-10000,x1=-1000)
        close=dict(mountain,model=0xca57f3,depth_minus_radius=2000)
        result=rank([initial,offscreen,mountain,close])
        self.assertEqual(result['candidate_events'],2)
        self.assertEqual(len(result['near_far_gate']),1)
        self.assertEqual(result['near_far_gate'][0]['model'],'cb1a8b')
        self.assertEqual(result['near_far_gate'][0]['suggested_capture_frames'],[2015,2051])
