from pathlib import Path
import sys
import unittest

import moderngl
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gpu'))
import renderer
from vunit_distance_fade import fragment_shader, validate_parameters


class DistanceFadeTests(unittest.TestCase):
    def test_parameter_and_shader_contracts(self):
        self.assertEqual(validate_parameters(240000, 20000), (240000., 20000.))
        for pair in [(0, 1), (100, 0), (100, 100), (100, -1), (float('inf'), 20),
                     (100, float('nan')), (True, 1), (1000001, 20)]:
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                validate_parameters(*pair)
        with self.assertRaises(ValueError):
            fragment_shader('void main() {}')

    def render(self, depth, *, fade=True, dither=False, foreground=False):
        ctx = moderngl.create_standalone_context(require=430)
        objects = []
        try:
            program = ctx.program(vertex_shader=renderer.VS,
                                  fragment_shader=fragment_shader(renderer.FS))
            objects.append(program)
            q = np.zeros((2 if foreground else 1, 16), dtype='<u2')
            q[0, :10] = [0x2000 if dither else 0, 1, 4, 4, 24, 4, 24, 24, 4, 24]
            if foreground:
                q[1, :10] = [0, 2, 10, 10, 18, 10, 18, 18, 10, 18]
            f, u = renderer.build_vertices(q, 0)
            texture = ctx.texture((4096, 1), 1, bytes(4096), dtype='u1')
            palette = np.zeros(32768, dtype='<u4'); palette[1] = 32767; palette[2] = 31 << 10
            colors = ctx.texture((256, 128), 1, palette.tobytes(), dtype='u4')
            image = ctx.texture((32, 32), 4); target = ctx.framebuffer([image])
            vf, vu = ctx.buffer(f.tobytes()), ctx.buffer(u.tobytes())
            masks = ctx.buffer(bytes(64 * len(q)))
            selectors = np.ones(len(q), dtype='<f4'); selectors[0] = -1 if fade else 1
            selection = ctx.buffer(selectors.tobytes())
            z = np.full((len(q), 4), depth, dtype='<f4'); depths = ctx.buffer(z.tobytes())
            objects.extend([texture, colors, image, target, vf, vu, masks, selection, depths])
            masks.bind_to_storage_buffer(3); selection.bind_to_storage_buffer(4); depths.bind_to_storage_buffer(5)
            vao = ctx.vertex_array(program, [
                (vf, '2f 2f 2f 2f 2f 4f 4f 4f', 'in_corner', 'in_v0', 'in_v1',
                 'in_v2', 'in_v3', 'in_uv01', 'in_uv23', 'in_uvBounds'),
                (vu, '4u', 'in_meta')])
            objects.append(vao)
            plane, width = validate_parameters(100, 20)
            for key, value in dict(uCanvas=(32., 32.), uScale=1, uClipRight=31,
                                   texram=0, texMask=4095, uDbgQuadId=0, uBgMargin=0,
                                   uClipW=32, uFarCoverage=0, colors=1,
                                   fadePlane=plane, fadeWidth=width).items():
                program[key].value = value
            target.use(); target.clear(0, 0, 1, 1); ctx.viewport = (0, 0, 32, 32)
            texture.use(0); colors.use(1)
            ctx.enable(moderngl.BLEND)
            ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA,
                              moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA)
            vao.render(moderngl.TRIANGLES)
            return np.flipud(np.frombuffer(image.read(), 'u1').reshape(32, 32, 4)).copy()
        finally:
            for obj in reversed(objects):
                obj.release()
            ctx.release()

    def test_actual_gpu_endpoints_and_protected_foreground(self):
        near = self.render(75)
        opaque = self.render(100, fade=False)
        np.testing.assert_array_equal(near, opaque)
        middle = self.render(90, foreground=True)
        far = self.render(100, foreground=True)
        # Reciprocal depth can put alpha one float ULP either side of0.5.
        # Either adjacent UNORM8 code is valid; untouched blue stays exact.
        self.assertTrue(np.all(np.isin(middle[8, 8, :2], [127, 128])))
        self.assertEqual(int(middle[8, 8, 2]), 255)
        np.testing.assert_array_equal(far[8, 8, :3], [0, 0, 255])
        for image in (middle, far):
            np.testing.assert_array_equal(image[12, 12, :3], [255, 0, 0])

    def test_actual_gpu_intrinsic_transparency_is_multiplied(self):
        opaque = self.render(90, fade=False, dither=True)[6:10, 6:10, :3]
        faded = self.render(90, dither=True)[6:10, 6:10, :3]
        written = np.all(opaque == [255, 255, 255], axis=2)
        self.assertEqual(int(written.sum()), 8)
        self.assertTrue(np.all(np.isin(faded[written, :2], [127, 128])))
        self.assertTrue(np.all(faded[written, 2] == 255))
        self.assertTrue(np.all(faded[~written] == [0, 0, 255]))

    def test_actual_gpu_planar_depth_has_no_fan_diagonal_seam(self):
        image = self.render([80, 100, 100, 80])
        top = image[8, 6:23, :3].astype(int)
        bottom = image[20, 6:23, :3].astype(int)
        self.assertLessEqual(int(np.abs(top - bottom).max()), 1)
        self.assertTrue(np.all(np.diff(top[:, 0]) <= 0))
        self.assertGreater(int(top[0, 0] - top[-1, 0]), 180)
        self.assertTrue(np.all(top[:, 0] == top[:, 1]))
        self.assertTrue(np.all(top[:, 2] == 255))


if __name__ == '__main__':
    unittest.main()
