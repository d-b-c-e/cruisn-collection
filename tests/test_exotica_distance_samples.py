import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from exotica_distance_samples import bands


def row(source, band, first, count):
    return struct.pack('<11I', 1, source, 3, 4, 5, band, 7, 8, 9, first, count)


class DistanceSamplesTests(unittest.TestCase):
    def test_presence_requires_polygons(self):
        result = bands(row(1, 3, 0, 0) + row(2, 2, 0, 4) + row(3, 3, 4, 7))
        self.assertEqual(result['3'], dict(instances=2, quads=7))
        self.assertEqual(result['2'], dict(instances=1, quads=4))
        self.assertEqual(bands(b'')['3']['quads'], 0)

    def test_bad_streams_fail(self):
        for raw in (b'x', row(1, 4, 0, 1), row(1, 3, 1, 1),
                    row(1, 3, 0, 131073), row(1, 3, 0, 2) + row(1, 2, 2, 1),
                    row(1, 3, 0, 2) + row(2, 2, 1, 1)):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    bands(raw)


if __name__ == '__main__':
    unittest.main()
