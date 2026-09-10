"""A hidden framebuffer page must fail validation even when the display matches."""
from pathlib import Path
import json
import struct
import subprocess
import sys
import tempfile
import unittest

import numpy as np


class ZeusRasterizeVerdictTests(unittest.TestCase):
    def test_cli_checks_full_color_and_depth_and_ignores_unused_alpha(self):
        checker = Path(__file__).resolve().parents[1] / 'harness/zeus_rasterize.py'
        with tempfile.TemporaryDirectory(prefix='cruisn-cpu-verdict-') as tmp:
            cap = Path(tmp)
            color = np.zeros(512 * 2048, '<u4')
            depth = np.zeros(color.size, '<i4')
            color.tofile(cap / 'pre_color.bin')
            depth.tofile(cap / 'pre_depth.bin')
            (cap / 'waveram.bin').write_bytes(bytes(16 * 1024 * 1024))
            (cap / 'pal_table.bin').write_bytes(bytes(1024))
            (cap / 'regs.txt').write_text('yScale 0\nzb38 00000000\n')
            (cap / 'records.bin').write_bytes(struct.pack('<6I', 3, 16, 0, 4, 0x123456, 99))
            color[:4] = 0x123456
            depth[:4] = 99
            for name, code in [('exact', 0), ('alpha-only', 0), ('hidden-color', 1), ('hidden-depth', 1)]:
                with self.subTest(name=name):
                    candidate_color, candidate_depth = color.copy(), depth.copy()
                    if name == 'alpha-only':
                        candidate_color |= 0xaa000000
                    if name == 'hidden-color':
                        candidate_color[800000] = 1
                    if name == 'hidden-depth':
                        candidate_depth[800000] = 1
                    candidate_color.tofile(cap / 'post_color.bin')
                    candidate_depth.tofile(cap / 'post_depth.bin')
                    report = cap / 'report.json'
                    result = subprocess.run([sys.executable, str(checker), str(cap), '--report', str(report)],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                    verdict = json.loads(report.read_text())
                    self.assertEqual(verdict['passed'], code == 0)
                    self.assertTrue(verdict['display']['passed'])
                    self.assertEqual(verdict['color']['differing_pixels'], int(name == 'hidden-color'))
                    self.assertEqual(verdict['depth']['differing_pixels'], int(name == 'hidden-depth'))
                    self.assertEqual(verdict['color']['pixels'], color.size)
                    self.assertEqual(len(verdict['sources']), 8)
