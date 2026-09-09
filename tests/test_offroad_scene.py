from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from scenery_c31 import F
from offroad_scene import scene, position_and_order, host_project
from test_offroad_sections import fixture


class OffroadSceneTests(unittest.TestCase):
    def test_guest_material_queue_defers_host_source(self):
        m = fixture()
        m.update({0x11141: 0x9e0000, 0x11142: 0x10390, 0x19e29: 0xa00000,
                  0x11145: 1, 0x11144: 1})
        counts, rows = scene(lambda p: m.get(p, 0), 3, True)
        self.assertEqual((counts['deferred'], rows), (1, []))
        m[0x11144] = 0
        with self.assertRaisesRegex(ValueError, 'upload state'):
            scene(lambda p: m.get(p, 0), 3, True)
        self.assertEqual(scene(lambda p: 0, 1, True)[0]['pretrack'], 1)

    def test_radial_order_and_host_projection_limits(self):
        obj = [0]*22; obj[11:14] = [F.integer(v).store() for v in (3000, 4000, 12000)]
        view = [F.integer(int(i in (0, 5, 10))).store() for i in range(12)]
        pos, order = position_and_order(obj, view, F.integer(1))
        self.assertEqual(order, 169000000)
        obj[13] = F.integer(-12000).store()
        self.assertEqual(position_and_order(obj, view, F.integer(1))[1], -169000000)
        vertices = [F.integer(0).store()]*3
        view[11] = F.integer(70000).store()
        self.assertIsNone(host_project(vertices, view, F.integer(256).store(), lambda p: 0, 1))
        self.assertEqual(host_project(vertices, view, F.integer(256).store(), lambda p: 0, 2), [256, 200])
        view[11] = F.integer(502).store()
        self.assertIsNone(host_project(vertices, view, 0, lambda p: 0, 2))


if __name__ == '__main__':
    unittest.main()
