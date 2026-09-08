import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from analyze_distance_capability import summarize


class DistanceCapabilityTests(unittest.TestCase):
    def run_rows(self, rom, rows):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'trace.csv'
            with path.open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow('frame,kind,pc,object,flags,depth_minus_radius,radius,limit,index,raw'.split(','))
                writer.writerows(rows)
            return summarize(path, rom)

    def test_exotica_uses_sphere_far_edge(self):
        result = self.run_rows('crusnexo', [
            [1, 'far', '6888', '1234', '0', 190000, 10000, 204800, 0, '32000'],
            [1, 'far', '6888', '1234', '0', 184800, 10000, 204800, 0, '32000'],
            [1, 'table', '688c', '1234', '0', 0, 0, 0, 4999, 'f851bf7b']])
        self.assertEqual(result['far_rejected'], 1)
        self.assertEqual(result['clamped_reads'], 1)

    def test_offroad_inclusive_float_limit_and_signed_index(self):
        result = self.run_rows('offroadc', [
            [1, 'far', '1c36', '1234', '0', 47296, 100, 47296, 0, 'f38c000'],
            [1, 'table', '1c45', '1234', '0', 0, 0, 0, -4096, '0']])
        self.assertEqual(result['far_rejected'], 1)
        self.assertEqual(result['table_indices'], [-4096, -4096])

    def test_rejects_empty_partial_or_misbound_evidence(self):
        for rows in ([], [[1, 'far', 'cc', '1234', '0', 90000, 100, 80000, 0, '13880']],
                     [[1, 'far', 'cc', '1234', '0', 'nan', 100, 80000, 0, '13880']],
                     [[1, 'far', 'cc', '1234', '0', 90000, 100, 160000, 0, '27100']],
                     [[1, 'table', 'd6', '1234', '0', 0, 0, 0, 5000, '0']]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.run_rows('crusnusa', rows)
