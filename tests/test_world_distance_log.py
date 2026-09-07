import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_world_distance import FIELDS, summarize


class DistanceLogTests(unittest.TestCase):
    def test_three_times_bounds(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'world-distance.csv'
            rows = [[0,240000,12,100,1,20,3,42,15000,1]]
            self.write(path, rows)
            self.assertEqual(summarize(path)['maximum_index'], 15000)
            for column, value in ((2,13), (8,15001)):
                invalid = [rows[0].copy()]
                invalid[0][column] = value
                self.write(path, invalid)
                with self.assertRaises(ValueError): summarize(path)

    def write(self, path, rows):
        with path.open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(FIELDS)
            writer.writerows(rows)

    def test_counters_require_complete_consistent_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'world-distance.csv'
            rows = [[0,100000,4,100,1,20,3,42,6000,1],
                    [1,100000,4,100,1,10,2,20,6250,0]]
            self.write(path, rows)
            result = summarize(path)
            self.assertEqual(result['totals']['extended_reads'], 62)
            self.assertEqual(result['maximum_index'], 6250)
            for field, value in [(0,3),(1,160000),(4,0),(5,-1),(6,11),(7,0),(8,6251)]:
                changed = [row.copy() for row in rows]
                changed[1][field] = value
                self.write(path, changed)
                with self.assertRaises(ValueError): summarize(path)
            self.write(path, [rows[0],rows[1][:-1]])
            with self.assertRaises(ValueError): summarize(path)
