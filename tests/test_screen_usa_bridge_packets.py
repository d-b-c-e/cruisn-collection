import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from analyze_world_host import HASH_SEED, QUAD_FIELDS, hash_quad
from screen_usa_bridge_packets import traced_scene


class UsaBridgeSceneClockTests(unittest.TestCase):
    def test_same_frame_different_time_selects_exact_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / 'usa-host-scenes.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=['frame', 'time', 'page',
                                                             'quads', 'quads_hash'])
                writer.writeheader()
                for time, page in [('1.0', 513), ('2.0', 516)]:
                    writer.writerow(dict(frame=10, time=time, page=page, quads=1,
                                         quads_hash=f'{hash_quad(HASH_SEED, [0] * 16):016x}'))
            with (root / 'usa-host-quads.csv').open('w', newline='') as stream:
                fields = ['frame', 'time', 'page', 'object', 'model', 'depth', *QUAD_FIELDS]
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for time, page, obj in [('1.0', 513, 1), ('2.0', 516, 2)]:
                    writer.writerow(dict(frame=10, time=time, page=page,
                                         object=obj, model=3, depth=4,
                                         **{field: 0 for field in QUAD_FIELDS}))
            selected = dict(ordinal=1, frame=10, page_control=516,
                            prepared_quads_hash=f'{hash_quad(HASH_SEED, [0] * 16):016x}',
                            consumed_quads=1)
            rows, receipt = traced_scene(root, selected)
            self.assertEqual(rows[0]['object'], 2)
            self.assertEqual(receipt['clock'], ['10', '2.0', '516'])


if __name__ == '__main__':
    unittest.main()
