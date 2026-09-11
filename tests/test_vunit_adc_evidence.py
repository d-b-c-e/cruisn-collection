from pathlib import Path
import csv
import json
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vunit_adc_evidence as a
from test_steering_reconstruction import inp


class VunitAdcTests(unittest.TestCase):
    def recording(self, rom='crusnusa'):
        return a.steering.SteeringRecording(inp(rom=rom), rom)

    def transactions(self, rom='crusnusa'):
        rec = self.recording(rom)
        shift = a.GAMES[rom]
        value = rec.sample_csv('0.025040000000')
        events = [('C', '0.020100000000', 0), ('W', '0.025000000000', 4 << shift),
                  ('R', '0.026000000000', value << shift)]
        return rec, self.rows(events)

    def rows(self, events):
        return [dict(sequence=str(n), kind=kind, frame='1', seconds=time, pc='123',
                     data=f'{data:x}', mask='ffffffff')
                for n, (kind, time, data) in enumerate(events, 1)]

    def test_all_three_games_use_conversion_time_not_cpu_read_time(self):
        for rom in a.GAMES:
            rec, rows = self.transactions(rom)
            result = a.reconcile(rows, rec, rom, 1, 2)
            self.assertEqual(result['counts']['steering_reads'], 1)
            self.assertEqual(result['steering_reads'][0]['value'], 156)
            self.assertNotEqual(rec.sample_csv(rows[-1]['seconds']), 156)
            self.assertEqual(result['steering_reads'][0]['sample_seconds'], '0.025040000000')
            self.assertEqual(result['steering_conversions_read'], 1)

    def test_latching_restart_permissions_and_commuting_control_deadline(self):
        rec = self.recording()
        earlier = rec.sample_csv('0.025040000000') << 24
        later = rec.sample_csv('0.027060000000') << 24
        events = [('C', '0.020100000000', 0), ('W', '0.025000000000', 4 << 24),
                  ('R', '0.026000000000', earlier), ('W', '0.026010000000', 5 << 24),
                  ('R', '0.026020000000', earlier), ('R', '0.026070000000', 45 << 24),
                  ('C', '0.026080000000', 0x40), ('R', '0.026090000000', 0xffffffff),
                  ('C', '0.026100000000', 0x20), ('W', '0.026110000000', 4 << 24),
                  ('C', '0.026120000000', 0), ('W', '0.027000000000', 4 << 24),
                  ('W', '0.027020000000', 4 << 24), ('C', '0.027060000000', 0),
                  ('R', '0.027065000000', later)]
        result = a.reconcile(self.rows(events), rec, 'crusnusa', 1, 2)
        for name in ('reads_during_conversion', 'disabled_W', 'disabled_R',
                     'superseded_commands', 'nonsteering_latched_reads'):
            self.assertEqual(result['counts'][name], 1)
        self.assertEqual(result['counts']['steering_reads'], 3)
        self.assertEqual(result['steering_conversions_read'], 2)

    def test_unknown_initial_control_and_latch_are_explicitly_excluded(self):
        rec, rows = self.transactions()
        before = [('R', '0.020000100000', 0x80000000),
                  ('W', '0.020000200000', 4 << 24),
                  ('C', '0.020000300000', 0), ('R', '0.020000400000', 0x80000000)]
        events = before + [(r['kind'], r['seconds'], int(r['data'], 16)) for r in rows]
        result = a.reconcile(self.rows(events), rec, 'crusnusa', 1, 2)
        for name in ('unknown_control_R', 'unknown_control_W', 'unknown_initial_latch_reads'):
            self.assertEqual(result['counts'][name], 1)
        self.assertEqual(result['counts']['steering_reads'], 1)

    def test_ambiguous_access_at_deadline_is_rejected_without_guessing(self):
        for kind in ('R', 'W'):
            rec, rows = self.transactions()
            rows[-1].update(kind=kind, seconds='0.025040000000')
            with self.assertRaisesRegex(ValueError, 'ambiguous ADC'):
                a.reconcile(rows, rec, 'crusnusa', 1, 2)

    def test_malformed_order_channel_mask_and_wrong_latched_value_rejected(self):
        mutations = [(0, 'sequence', '2'), (1, 'kind', 'X'), (1, 'mask', 'ffffff'),
                     (1, 'data', '3000000'), (1, 'pc', 'nothex'), (2, 'data', '9d000000'),
                     (2, 'data', '9c000001'), (2, 'seconds', '0.041000000000'),
                     (2, 'seconds', '0.021000000000'), (2, 'seconds', 'nan'),
                     (2, 'frame', '0')]
        for index, key, value in mutations:
            with self.subTest(key=key, value=value):
                rec, rows = self.transactions(); rows[index][key] = value
                with self.assertRaises(ValueError): a.reconcile(rows, rec, 'crusnusa', 1, 2)

    def fixture(self, root):
        run = root / 'run'; (run / 'input').mkdir(parents=True)
        (root / 'report.json').write_text(json.dumps(dict(passed=True,
            comparison=dict(passed=True,input_or_time_mismatches=0,pixel_mismatches=0))))
        (run / 'invocation.json').write_text(json.dumps(dict(command=['mame', 'crusnusa'],
            executable_sha256=a.NATIVE, environment={'MIDV_FFB': '0'})))
        (run / 'input/session.inp').write_bytes(inp(rom='crusnusa'))
        (run / 'frames.csv').write_text('frame,emulated_seconds,:WHEEL\n'
                                      '1,0.020000000000,128\n2,0.040000000000,240\n')
        _, rows = self.transactions()
        with (run / 'vunit-adc.csv').open('w', newline='') as f:
            writer=csv.DictWriter(f,fieldnames=a.FIELDS);writer.writeheader();writer.writerows(rows)
        shutil.copyfile(Path(a.__file__).parent / 'probes/vunit_adc.lua', run / 'probe.lua')
        receipt=dict(schema=1,game='crusnusa',first=1,last=2,first_seconds=.020,
                     last_seconds=.040,complete=True,rows=3,control=1,writes=1,reads=1,error=None)
        (run/'vunit-adc-receipt.json').write_text(json.dumps(receipt))
        return run

    def test_full_verifier_binds_input_build_probe_and_observation_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=self.fixture(Path(tmp)); report=a.verify(run,'crusnusa')
            self.assertTrue(report['passed'])
            self.assertTrue(report['conversion_schedule_reconstructed'])
            self.assertFalse(report['conversion_callback_observed'])
            self.assertFalse(report['normalization_accepted'])
            self.assertFalse(report['physical_angle_verified'])
            self.assertIn('probe.lua', report['evidence_sha256'])

    def test_only_exact_older_bounded_collector_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=self.fixture(Path(tmp));p=run/'probe.lua'
            p.write_text(p.read_text().replace('rows<=196608', 'rows<=131072'))
            self.assertEqual(a.verify(run,'crusnusa')['collector_event_limit'],131072)
            p.write_text(p.read_text().replace('rows<=131072', 'rows<=262144'))
            with self.assertRaises(ValueError):a.verify(run,'crusnusa')

    def test_incomplete_forged_or_different_source_evidence_fails(self):
        mutations=[('vunit-adc-receipt.json','"complete": true','"complete": false'),
                   ('../report.json','"pixel_mismatches": 0','"pixel_mismatches": 1'),
                   ('../report.json','"input_or_time_mismatches": 0','"input_or_time_mismatches": 1'),
                   ('vunit-adc-receipt.json','"rows": 3','"rows": 4'),
                   ('vunit-adc-receipt.json','"last_seconds": 0.04','"last_seconds": 0.041'),
                   ('invocation.json',a.NATIVE,'a'*64),
                   ('invocation.json','"MIDV_FFB": "0"','"MIDV_FFB": "1"'),
                   ('probe.lua','Read-only','Unverified'),
                   ('vunit-adc.csv','sequence,kind','kind,sequence')]
        for file, old, new in mutations:
            with self.subTest(file=file), tempfile.TemporaryDirectory() as tmp:
                run=self.fixture(Path(tmp));p=run/file
                original=p.read_text();self.assertIn(old,original);p.write_text(original.replace(old,new))
                with self.assertRaises(ValueError):a.verify(run,'crusnusa')


if __name__ == '__main__':
    unittest.main()
