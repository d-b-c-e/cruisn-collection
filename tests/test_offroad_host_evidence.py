import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_offroad_host import COUNTERS, PHASES, OBJECT_FIELDS, evidence
from analyze_world_host import HASH_SEED, QUAD_FIELDS, hash_quad


class OffroadHostEvidenceTests(unittest.TestCase):
    def fixture(self):
        record = dict(frame=5500, time='94.945415480000', page=513, mode=2, multiplier=3,
                      future_enabled=1, **dict.fromkeys(COUNTERS, 0), **dict.fromkeys(PHASES, 0), microseconds=0)
        record.update(future=1, future_definitions=2, unsupported=1, decoded=1, quads=1,
                      quads_hash=f'{hash_quad(HASH_SEED, range(16)):016x}')
        quad = dict(frame=record['frame'], time=record['time'], page=record['page'],
                    **dict(zip(OBJECT_FIELDS, (0x80c00100, 0xc00200, 0, 70000, 50000))),
                    **dict(zip(QUAD_FIELDS, range(16))))
        return record, quad

    def write(self, run, records, quads):
        for name, values in [('scenes', records), ('quads', quads)]:
            with (run/f'offroad-host-{name}.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(values[0]))
                writer.writeheader(); writer.writerows(values)

    def test_special_future_sources_and_exact_geometry_clocks(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); record, quad = self.fixture()
            self.write(run, [record], [quad])
            self.assertEqual(evidence(run)[2]['totals']['quads'], 1)
            quad['time'] = '94.945415490000'
            self.write(run, [record], [quad])
            with self.assertRaisesRegex(ValueError, 'orphan'): evidence(run)

    def test_deleted_geometry_and_broken_descriptor_partition_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); record, quad = self.fixture()
            self.write(run, [record], [quad])
            p = run/'offroad-host-quads.csv'; p.write_text(p.read_text().splitlines()[0]+'\n')
            with self.assertRaisesRegex(ValueError, 'fingerprint'): evidence(run)
            record['unsupported'] = 0
            self.write(run, [record], [quad])
            with self.assertRaisesRegex(ValueError, 'partition'): evidence(run)

    def test_duplicate_scene_and_deferred_drawing_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); record, quad = self.fixture()
            self.write(run, [record, record], [quad])
            with self.assertRaisesRegex(ValueError, 'duplicate'): evidence(run)
            record['deferred'] = 1
            self.write(run, [record], [quad])
            with self.assertRaisesRegex(ValueError, 'deferred'): evidence(run)


if __name__ == '__main__':
    unittest.main()
