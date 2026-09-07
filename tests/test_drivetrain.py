import csv
import json
from pathlib import Path
import socket
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_drivetrain import analyze
from telemetry_loopback import TelemetryLoopback


class DrivetrainTests(unittest.TestCase):
    def test_wire_capture_uses_private_ports_and_reports_invalid_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={};receiver=TelemetryLoopback(tmp);receiver.start(env)
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
                sock.sendto(b'bad',('127.0.0.1',int(env['MIDV_TELEM_FORZA'].split(':')[1])))
                sock.sendto(b'{"out":"gear","value":2}',('127.0.0.1',int(env['MIDV_TELEM_UDP'].split(':')[1])))
            report=receiver.close()
            self.assertFalse(report['passed'])
            self.assertTrue(any('length 3' in s for s in report['errors']))
            self.assertEqual(report['packets'],{'forza':1,'json':1})

    def test_missing_wire_samples_and_stale_unavailable_rpm_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);path=directory/'drivetrain.csv'
            header='seconds,frame,player,gear,gear_source,rev_value,tach_fraction,rpm,rpm_estimated\n'
            path.write_text(header+'0,0,56950,1,3,30,0.625,5337.5,1\n')
            self.assertTrue(analyze(directory)['passed'])
            with self.assertRaisesRegex(ValueError,'all four gears'):analyze(directory,require_drive=True)
            (directory/'forza.csv').write_text('timestamp_ms,race_on,max_rpm,idle_rpm,rpm,speed_ms,gear\n')
            with self.assertRaisesRegex(ValueError,'missing/extra'):analyze(directory)
            path.write_text(header+'0,0,0,0,0,0,0,5337.5,0\n')
            with self.assertRaisesRegex(ValueError,'must clear'):analyze(directory)
