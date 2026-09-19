"""Reject false stop acceptance: missing families, later output, stale receipts."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import verify_ffb_stop as stop
from ffb_worker import SOURCE_FIELDS


class StopTests(unittest.TestCase):
    def fixture(self, root, mutate=None):
        outputs = [(1, .01, 'condition', 0, 1, 0), (2, .02, 'condition', 1, 1, 0),
                   (3, .03, 'condition', 2, 1, 0), (4, .04, 'constant', 0, 12000, 0),
                   (5, .05, 'rumble', 0, .3, 0), (6, .10, 'latch', 0, 1, 1),
                   (7, .11, 'constant', 0, 0, 1), (8, .12, 'stop_all', 0, 0, 1),
                   (9, .13, 'rumble', 0, 0, 1), (10, .14, 'ack', 0, 0, 1)]
        outputs = [list(row) for row in outputs]
        if mutate:
            mutate(outputs)
        ticks = [[i+1, .15+i*.02, 1, 0, 0, 0, 0, 0, 0, 0, 0] for i in range(10)]
        sources = [[1, .04, .01, 1, 100, 100, 1, 0, 0], [2, .33, .30, 18, 100, 100, 1, 0, 0]]
        for name, fields, rows in (
                ('outputs', stop.FIELDS, outputs), ('sources', SOURCE_FIELDS, sources),
                ('ticks', 'sequence,host_seconds,cancel,active,before,candidate,event,shaped,mixed,out,rumble_request'.split(','), ticks)):
            with (root/f'ffb-worker-{name}.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(fields)
                writer.writerows(rows)
        marker = root/'ffb-user-stopped'
        marker.touch()
        invocation = dict(returncode=0, error=None, environment=dict(
            MIDV_FFB='0', MIDV_FFB_OBSERVE_WORKER='1', MIDV_FFB_STOP_FILE=str(marker)))
        (root/'invocation.json').write_text(json.dumps(invocation), encoding='utf-8')
        receipt = dict(complete=True, device_free=True, physical_output=False, user_stopped=True,
                       sink_final_level=0, sink_final_conditions=0, sink_final_rumble=0,
                       user_stop_ack_seconds=.135, outputs=len(outputs), sources=2, ticks=10)
        for singular, plural in (('output', 'outputs'), ('source', 'sources'), ('tick', 'ticks')):
            receipt[singular+'_bytes'] = (root/f'ffb-worker-{plural}.csv').stat().st_size
        (root/'ffb-worker-receipt.json').write_text(json.dumps(receipt), encoding='utf-8')

    def test_all_families_and_later_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            result = stop.verify(root)
            self.assertTrue(result['passed'])
            self.assertFalse(result['physical_acceptance'])
            self.assertEqual(result['nonzero_source_writes_after_stop'], 1)
            self.assertEqual(result['stopped_ticks'], 10)

    def test_missing_coverage_and_restarted_effects(self):
        for index, column, value in ((0, 4, 0), (3, 4, 0), (4, 4, 0),
                (6, 4, 12), (8, 4, .2), (7, 2, 'condition'), (9, 5, 0),
                (1, 1, float('nan')), (1, 0, 1), (1, 3, 5), (5, 1, .2)):
            with self.subTest(index=index, column=column, value=value), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.fixture(root, lambda rows: rows[index].__setitem__(column, value))
                with self.assertRaises(ValueError):
                    stop.verify(root)

    def test_stale_or_nonzero_receipt_and_missing_marker(self):
        for key, value in (('output_bytes', 1), ('outputs', 1), ('sink_final_conditions', 1),
                           ('user_stop_ack_seconds', .09), ('physical_output', True)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.fixture(root)
                path = root/'ffb-worker-receipt.json'
                data = json.loads(path.read_text(encoding='utf-8'))
                data[key] = value
                path.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(ValueError):
                    stop.verify(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            (root/'ffb-user-stopped').unlink()
            with self.assertRaisesRegex(ValueError, 'persisted'):
                stop.verify(root)

    def test_writes_and_worker_must_continue(self):
        for kind, column, value, expected in (('sources', 'raw', '0', 'no nonzero'),
                ('ticks', 'out', '1', 'regenerated'), ('ticks', 'host_seconds', 'nan', 'clock')):
            with self.subTest(kind=kind, column=column), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.fixture(root)
                path = root/f'ffb-worker-{kind}.csv'
                with path.open(encoding='utf-8', newline='') as stream:
                    reader = csv.DictReader(stream)
                    fields, rows = reader.fieldnames, list(reader)
                rows[-1][column] = value
                with path.open('w', encoding='utf-8', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                receipt_path = root/'ffb-worker-receipt.json'
                receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
                receipt[('source' if kind == 'sources' else 'tick')+'_bytes'] = path.stat().st_size
                receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, expected):
                    stop.verify(root)


if __name__ == '__main__':
    unittest.main()
