import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_force_gate import analyze


class ForceGateTests(unittest.TestCase):
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
