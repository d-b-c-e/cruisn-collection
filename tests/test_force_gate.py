import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_force_gate import analyze


class ForceGateTests(unittest.TestCase):
    def test_exotica_cabinet_polarity_composes_with_device_direction(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);memory=p/'memory.csv';trace=p/'force-gate.csv'
            memory.write_text('frame,state,flags\n1,1,0\n2,1,1\n3,1,1\n4,1,1\n')
            (p/'frames.csv').write_text('frame,:DIPS\n1,0\n2,0\n3,0\n4,2048\n')
            (p/'force-source.csv').write_text('seconds,frame,raw,adapted\n0,0,8,63\n1,1,8,63\n2,2,8,63\n3,3,8,63\n')
            data='seconds,frame,enabled,raw,requested_level,game_invert,device_invert\n0,0,0,8,0,1,0\n1,1,1,8,16384,1,0\n2,2,1,8,-16384,1,1\n3,3,1,8,-16384,0,0\n'
            trace.write_text(data)
            self.assertEqual(analyze(p,memory,'crusnexo',verify_polarity=True)['polarity']['corrected_nonzero_requests'],2)
            trace.write_text(data.replace('8,16384,1,0','8,-16384,1,0'))
            with self.assertRaisesRegex(ValueError,'requested force'): analyze(p,memory,'crusnexo',verify_polarity=True)
            trace.write_text(data)
            (p/'frames.csv').write_text('frame,:DIPS\n1,0\n2,2048\n3,0\n4,2048\n')
            with self.assertRaisesRegex(ValueError,'cabinet switch'): analyze(p,memory,'crusnexo',verify_polarity=True)

    def test_world_menu_force_passes_through_without_driving_gate(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);memory=p/'memory.csv';trace=p/'force-gate.csv'
            memory.write_text('frame,state,flags\n8853,4,26\n8854,5,2\n')
            trace.write_text('seconds,frame,enabled,raw,requested_level\n153,8852,1,25,-6501\n153.017,8853,1,20,-5201\n')
            result=analyze(p,memory,'crusnwld24','passthrough')
            self.assertEqual(result['non_driving_nonzero_requests'],1)
            self.assertEqual(result['disabled_writes'],0)
            trace.write_text(trace.read_text().replace(',1,20,-5201',',0,20,0'))
            with self.assertRaisesRegex(ValueError,'game-state'): analyze(p,memory,'crusnwld24','passthrough')

    def test_world_finish_releases_even_when_motor_commands_continue(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);memory=p/'memory.csv';trace=p/'force-gate.csv'
            memory.write_text('frame,state,flags\n8853,4,26\n8854,5,2\n')
            trace.write_text('seconds,frame,enabled,raw,requested_level\n153,8852,1,25,-6501\n153.017,8853,0,20,0\n')
            result=analyze(p,memory,'crusnwld24')
            self.assertEqual(result['nonzero_raw_suppressed'],1)
            trace.write_text(trace.read_text().replace(',0,20,0',',0,20,-5201'))
            with self.assertRaisesRegex(ValueError,'inactive game'): analyze(p,memory,'crusnwld24')

    def test_exotica_hud_before_go_does_not_enable_force(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);memory=p/'memory.csv';trace=p/'force-gate.csv'
            memory.write_text('frame,state,flags\n3317,1,0\n3635,1,1\n')
            trace.write_text('seconds,frame,enabled,raw,requested_level\n58,3316,0,-8,0\n64,3634,1,8,-16644\n')
            self.assertTrue(analyze(p,memory,'crusnexo')['passed'])
            memory.write_text(memory.read_text().replace('3635,1,1','3635,0,1'))
            with self.assertRaisesRegex(ValueError,'game-state'): analyze(p,memory,'crusnexo')
