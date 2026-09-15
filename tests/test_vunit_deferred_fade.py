from pathlib import Path
import sys
import unittest

import moderngl
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gpu'))
import renderer
from vunit_distance_fade import palette_shader


def resolve(indices, masks, base, base_masks, alpha, palettes, *, crt=0, legacy=False, enabled=True):
    """Upload indices once, then change the palette without redrawing geometry."""
    h, w = indices.shape
    ctx = moderngl.create_standalone_context(require=430)
    objects = []
    try:
        program = ctx.program(vertex_shader=renderer.PAL_VS,
                              fragment_shader=renderer.PAL_FS if legacy else palette_shader(renderer.PAL_FS))
        objects.append(program)
        data = [(indices, 'u2'), (palettes[0], 'u4'), (masks, 'u1')]
        if not legacy:
            data += [(base, 'u2'), (base_masks, 'u1'), (alpha, 'f4')]
        textures = []
        for i, (array, dtype) in enumerate(data):
            shape = (256, 128) if i == 1 else (w, h)
            texture = ctx.texture(shape, 1, np.asarray(array, dtype='<'+dtype).tobytes(), dtype=dtype)
            objects.append(texture); textures.append(texture); texture.use(i)
        target_image = ctx.texture((w, h), 4)
        target = ctx.framebuffer([target_image]); vao = ctx.vertex_array(program, [])
        objects += [target_image, target, vao]
        values = dict(idxTex=0, palTex=1, maskTex=2, uCrop=0, uCrt=crt,
                      uSrcH=float(h), uFillR=1, uMargin=0, uHostLayers=1)
        if not legacy:
            values.update(uDistanceFade=int(enabled), originalIdxTex=3, originalMaskTex=4, fadeAlphaTex=5)
        for key, value in values.items():
            program[key].value = value
        ctx.viewport = (0, 0, w, h); target.use()
        images = []
        for palette in palettes:
            textures[1].write(np.asarray(palette, dtype='<u4').tobytes())
            # Rebind after framebuffer allocation; no index/mask/alpha uploads.
            for i, texture in enumerate(textures):
                texture.use(i)
            vao.render(moderngl.TRIANGLES, vertices=3)
            images.append(np.frombuffer(target_image.read(), 'u1').reshape(h, w, 4).copy())
        return images
    finally:
        for obj in reversed(objects):
            obj.release()
        ctx.release()


class DeferredFadeTests(unittest.TestCase):
    def fixture(self):
        y, x = np.indices((16, 16))
        base = (x % 3).astype('<u2'); extended = ((x+y) % 3).astype('<u2')
        mask = np.ones((16, 16), dtype='u1'); base_mask = mask.copy()
        mask[8, 8] = 0; base_mask[5, 5] = 0
        palette = np.zeros(32768, dtype='<u4'); palette[:3] = [31, 32767, 31 << 5]
        return extended, mask, base, base_mask, palette

    def test_late_palette_updates_recolor_both_views(self):
        ext, mask, base, base_mask, palette = self.fixture()
        ext.fill(1); base.fill(0); mask.fill(1); base_mask.fill(1)
        after = palette.copy(); after[0] = 31 << 5; after[1] = 31 << 10
        images = resolve(ext, mask, base, base_mask, np.full(ext.shape, .5), [palette, after])
        for image in images:
            self.assertTrue(np.all(np.isin(image[8, 8, :2], [127, 128])))
        self.assertEqual(int(images[0][8, 8, 2]), 255)
        self.assertEqual(int(images[1][8, 8, 2]), 0)

    def test_endpoints_preserve_separate_seam_masks_and_crt(self):
        ext, mask, base, base_mask, palette = self.fixture()
        for crt in (0, 1):
            with self.subTest(crt=crt):
                expected_ext = resolve(ext, mask, base, base_mask, None, [palette], crt=crt, legacy=True)[0]
                expected_base = resolve(base, base_mask, base, base_mask, None, [palette], crt=crt, legacy=True)[0]
                for amount, expected in [(0, expected_base), (1, expected_ext)]:
                    actual = resolve(ext, mask, base, base_mask, np.full(ext.shape, amount), [palette], crt=crt)[0]
                    np.testing.assert_array_equal(actual, expected)
                disabled = resolve(ext, mask, base, base_mask, np.zeros(ext.shape), [palette], crt=crt, enabled=False)[0]
                np.testing.assert_array_equal(disabled, expected_ext)

    def test_dither_uses_surface_opacity_without_checkerboard_reintroduction(self):
        ext, mask, base, base_mask, palette = self.fixture()
        y, x = np.indices(ext.shape); written = ((x ^ y) & 1) == 0
        ext = np.where(written, 1, base).astype('<u2')
        mask = np.where(written, 7, 1).astype('u1'); base_mask.fill(1)
        alpha = np.where(written, .5, 1)
        opaque = resolve(ext, mask, base, base_mask, None, [palette], legacy=True)[0]
        original = resolve(base, base_mask, base, base_mask, None, [palette], legacy=True)[0]
        actual = resolve(ext, mask, base, base_mask, alpha, [palette])[0]
        expected = (opaque.astype(float) + original.astype(float)) / 2
        self.assertLessEqual(float(np.abs(actual-expected).max()), 1)


if __name__ == '__main__':
    unittest.main()
