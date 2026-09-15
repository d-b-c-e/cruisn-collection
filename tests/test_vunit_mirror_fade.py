"""Actual MRT routing fixture: original/auxiliary draws and sparse CPU writes."""
from pathlib import Path
import sys
import unittest

import moderngl
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gpu'))
import renderer
from vunit_distance_fade import indexed_fragment_shader, mirror_fragment_shader


class MirrorFadeTests(unittest.TestCase):
    def setUp(self):
        self.ctx = moderngl.create_standalone_context(require=430)
        self.objects = []

    def tearDown(self):
        for obj in reversed(self.objects):
            obj.release()
        self.ctx.release()

    def keep(self, obj):
        self.objects.append(obj)
        return obj

    def page(self):
        textures = []
        for dtype, value in [('u2', 0), ('u1', 0), ('f4', 1), ('u2', 0), ('u1', 0)]:
            data = np.full((32, 32), value, dtype='<'+dtype)
            textures.append(self.keep(self.ctx.texture((32, 32), 1, data.tobytes(), dtype=dtype)))
        full = self.keep(self.ctx.framebuffer(textures))
        auxiliary = self.keep(self.ctx.framebuffer(textures[:3]))
        return textures, full, auxiliary

    def read(self, textures):
        return [np.frombuffer(t.read(), dtype='<'+dt).reshape(32, 32).copy()
                for t, dt in zip(textures, ['u2', 'u1', 'f4', 'u2', 'u1'])]

    def draw(self, target, *, pen, rect, auxiliary=False, dither=False, mirror=True):
        source = indexed_fragment_shader(renderer.FS) if auxiliary else renderer.FS
        program = self.keep(self.ctx.program(vertex_shader=renderer.VS,
                                            fragment_shader=mirror_fragment_shader(source) if mirror else source))
        q = np.zeros((1, 16), dtype='<u2')
        x0, y0, x1, y1 = rect
        q[0, :10] = [0x2000 if dither else 0, pen, x0, y0, x1, y0, x1, y1, x0, y1]
        f, u = renderer.build_vertices(q, 0)
        if auxiliary:
            u[:, 2] |= 8
        vf = self.keep(self.ctx.buffer(f.tobytes()))
        vu = self.keep(self.ctx.buffer(u.tobytes()))
        vao = self.keep(self.ctx.vertex_array(program, [
            (vf, '2f 2f 2f 2f 2f 4f 4f 4f', 'in_corner', 'in_v0', 'in_v1',
             'in_v2', 'in_v3', 'in_uv01', 'in_uv23', 'in_uvBounds'),
            (vu, '4u', 'in_meta')]))
        self.keep(self.ctx.buffer(bytes(64))).bind_to_storage_buffer(3)
        if auxiliary:
            self.keep(self.ctx.buffer(np.array([-1], '<f4').tobytes())).bind_to_storage_buffer(4)
            self.keep(self.ctx.buffer(np.full(4, 90, '<f4').tobytes())).bind_to_storage_buffer(5)
        texture = self.keep(self.ctx.texture((4096, 1), 1, bytes(4096), dtype='u1'))
        values = dict(uCanvas=(32., 32.), uScale=1, uClipRight=31, texram=0,
                      texMask=4095, uDbgQuadId=0, uBgMargin=0, uClipW=32, uFarCoverage=0)
        if auxiliary:
            values.update(fadePlane=100., fadeWidth=20.)
        for key, value in values.items():
            program[key].value = value
        target.use(); texture.use(0); self.ctx.viewport = (0, 0, 32, 32)
        vao.render(moderngl.TRIANGLES)

    def test_ordinary_auxiliary_cpu_and_page_isolation(self):
        textures, full, auxiliary = self.page()
        other_textures, _, _ = self.page()
        other_before = self.read(other_textures)
        control_textures, _, _ = self.page()
        control = self.keep(self.ctx.framebuffer(control_textures[:2]))
        self.draw(full, pen=2, rect=(2, 2, 29, 29))
        self.draw(control, pen=2, rect=(2, 2, 29, 29), mirror=False)
        initial = self.read(textures)
        np.testing.assert_array_equal(initial[0], initial[3])
        np.testing.assert_array_equal(initial[1], initial[4])
        for actual, expected in zip(initial[3:], self.read(control_textures)[:2]):
            np.testing.assert_array_equal(actual, expected)
        self.assertGreater(np.count_nonzero(initial[0]), 500)
        self.assertTrue(np.all(initial[2] == 1))

        self.draw(auxiliary, pen=3, rect=(4, 4, 25, 25), auxiliary=True, dither=True)
        extended = self.read(textures)
        np.testing.assert_array_equal(extended[3], initial[3])
        np.testing.assert_array_equal(extended[4], initial[4])
        written = extended[0] == 3
        self.assertGreater(np.count_nonzero(written), 100)
        self.assertTrue(np.all(extended[1][written] == 5))
        np.testing.assert_allclose(extended[2][written], .5, rtol=0, atol=2e-6)
        np.testing.assert_array_equal(extended[2][~written], initial[2][~written])

        # A later ordinary foreground replaces opacity and both views only where drawn.
        self.draw(full, pen=4, rect=(10, 10, 18, 18))
        self.draw(control, pen=4, rect=(10, 10, 18, 18), mirror=False)
        foreground = self.read(textures)
        written = foreground[0] == 4
        self.assertGreater(np.count_nonzero(written), 30)
        self.assertTrue(np.all(foreground[3][written] == 4))
        self.assertTrue(np.all(foreground[2][written] == 1))
        for actual, expected in zip(foreground[3:], self.read(control_textures)[:2]):
            np.testing.assert_array_equal(actual, expected)

        # CPU dirty coordinates are native top-down, while GL texture rows are bottom-up.
        cpu = np.full((32, 512), 9, dtype='<u2')
        dirty = np.zeros((32, 512), dtype='u1')
        dirty[6, 6] = 1; dirty[15, 15] = 1; dirty[30, 30] = 1
        program = self.keep(self.ctx.program(vertex_shader=renderer.PAL_VS,
                                            fragment_shader=mirror_fragment_shader(renderer.CPU_FS)))
        cpu_texture = self.keep(self.ctx.texture((512, 32), 1, cpu.tobytes(), dtype='u2'))
        dirty_texture = self.keep(self.ctx.texture((512, 32), 1, dirty.tobytes(), dtype='u1'))
        vao = self.keep(self.ctx.vertex_array(program, []))
        for key, value in dict(cpuIndex=0, cpuDirty=1, uScale=1, uMargin=0, uHeight=32).items():
            program[key].value = value
        full.use(); cpu_texture.use(0); dirty_texture.use(1)
        vao.render(moderngl.TRIANGLES, vertices=3)
        after = self.read(textures)
        selected = np.flipud(dirty[:, :32].astype(bool))
        for i, expected in enumerate([9, 1, 1, 9, 1]):
            self.assertTrue(np.all(after[i][selected] == expected))
            np.testing.assert_array_equal(after[i][~selected], foreground[i][~selected])
        for actual, expected in zip(self.read(other_textures), other_before):
            np.testing.assert_array_equal(actual, expected)

    def test_wrapper_rejects_unsupported_or_already_wrapped_shader(self):
        for source in ['void main() {}', mirror_fragment_shader(renderer.FS)]:
            with self.assertRaises(ValueError):
                mirror_fragment_shader(source)


if __name__ == '__main__':
    unittest.main()
