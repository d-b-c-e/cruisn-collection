from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from offroad_billboard import prepare, project
from scenery_c31 import F


class BillboardTests(unittest.TestCase):
    def fixture(self):
        f = lambda n: F.integer(n).store()
        obj = [0]*22; obj[5] = 4; obj[11:14] = list(map(f, (10, 20, 1000)))
        view = [f(0)]*12
        for i in (0, 5, 10): view[i] = f(1)
        return f, obj, view

    def test_billboard_basis_translation_and_unused_object_angles(self):
        f, obj, view = self.fixture(); basis = view.copy()
        basis[0] = f(-1)
        for i in (3, 7, 11): basis[i] = f(9999)
        matrix = prepare(obj, view, basis)
        self.assertEqual(matrix[3::4], list(map(f, (10, 20, 1000))))
        obj[14:17] = [0xffffffff, 12345, 67890]
        self.assertEqual(prepare(obj, view, basis), matrix)
        vertices = [f(0)]*12; vertices[:3] = list(map(f, (3, 4, 5)))
        self.assertEqual(project(vertices, matrix, f(256), lambda z: f(1))[:3], [263, 176, 1005])

    def test_wrong_branch_extent_and_original_depth_reject(self):
        f, obj, view = self.fixture()
        for flags in (0, 2, 6):
            obj[5] = flags
            with self.assertRaises(ValueError): prepare(obj, view, view)
        obj[5] = 4
        with self.assertRaises(ValueError): prepare(obj, view[:-1], view)
        bad = view.copy(); bad[0] = True
        with self.assertRaises(ValueError): prepare(obj, bad, view)
        matrix = prepare(obj, view, view); vertices = [f(0)]*12; vertices[11] = f(63680)
        with self.assertRaises(ValueError): project(vertices, matrix, f(256), lambda z: f(1))


if __name__ == '__main__': unittest.main()
