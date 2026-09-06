import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from rasterize import render_quad


class CpuRasterTests(unittest.TestCase):
    def test_unsigned_dma_sign_extension_address_and_palette_arithmetic(self):
        dma = np.array([0x100, 0x4600, 0xffff, 1, 2, 1, 2, 3, 0xffff, 3,
                        0, 0, 0, 0, 0x1001, 0], dtype=np.uint16)
        texture = np.zeros(2048, dtype=np.uint8)
        texture[256] = 201  # 0x1001 * 256 wraps to byte 256
        for words in (dma, dma.tolist()):
            pixels = np.zeros(0x80000, dtype=np.uint16)
            render_quad(words, 0, pixels, texture, 511, 399)
            self.assertTrue(np.all(pixels.reshape(1024, 512)[1:4, :3] == 0x46c9))
            self.assertEqual(np.count_nonzero(pixels), 9)
