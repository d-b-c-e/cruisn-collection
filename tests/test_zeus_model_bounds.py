from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from zeus_model_bounds import model_bounds, outside
from verify_zeus_bounds import synthetic, polygon, word, verify, intersects
from zeus_model import decode


class ZeusModelBounds(unittest.TestCase):
    def context(self):
        context = next(synthetic(5))
        context['matrix'] = [1., 0., 0., 0., 1., 0., 0., 0., 1.]
        context['translation'] = [0., 0., 100.]
        context['regs'][0x66] = 0x8e
        return context

    def test_signed_vertices_and_unsupported_model_state(self):
        vertices = [[-32768, 0, 4], [32767, -12, 2], [0, 8, -3], [2, 1, 0]]
        words = polygon(vertices)
        self.assertEqual(model_bounds(words, 10), [(-32768, 32767), (-12, 8), (-3, 4)])
        self.assertIsNone(model_bounds([], 10))
        for bad in (words[:-1], [0x36660000, 0], [0x36200000, 0x08000000], [0xff000000, 0]):
            with self.assertRaises(ValueError):model_bounds(bad, 10)

    def test_near_crossing_and_nonfinite_bounds_fail_open(self):
        context = self.context();bounds = [(-1, 1), (-1, 1), (-2, 2)]
        context['translation'][2] = 1.
        self.assertFalse(outside(bounds, context, 86))
        context['translation'][2] = -10.
        self.assertTrue(outside(bounds, context, 86))
        context['matrix'][0] = float('inf')
        self.assertFalse(outside(bounds, context, 86))
        self.assertFalse(outside(bounds, self.context(), float('nan')))
        with self.assertRaisesRegex(ValueError, 'margin'):
            verify([self.context()], Path('unused'), Path('unused'), float('nan'))

    def test_viewport_edges_include_exact_boundary(self):
        context = self.context();point = [(0, 0)]*3
        for axis, edge, origin in ((0, -86, 256), (0, 598, 256), (1, 0, 200), (1, 400, 200)):
            c = copy.deepcopy(context);c['translation'][2] = 510.
            c['translation'][axis] = float(edge-origin)
            self.assertFalse(outside(point, c, 86))
            c['translation'][axis] += -10. if edge < origin else 10.
            self.assertTrue(outside(point, c, 86))

    def test_rejections_preserve_independently_projected_viewport_geometry(self):
        visible = rejected = 0
        for context in synthetic(500):
            bounds = model_bounds(context['words'], context['quad_size'])
            culled = outside(bounds, context, 86)
            quads, _ = decode(context)
            onscreen = sum(intersects(points, 86) for fields, points in quads)
            self.assertFalse(culled and onscreen)
            visible += onscreen;rejected += culled
        self.assertGreater(visible, 0);self.assertGreater(rejected, 0)
