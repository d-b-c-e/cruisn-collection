from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_fragment_sources as fragments


class FragmentSourceTests(unittest.TestCase):
    def test_source_spans_reject_missing_or_ambiguous_ownership(self):
        row = struct.pack('<11I', 1, 2, 3, 0, 0, 3, 0, 0, 0, 0, 1)
        self.assertEqual(len(fragments.source_spans(row, 1)), 1)
        for raw, count in ((row, 2), (row+row, 2), (row[:-1], 1)):
            with self.subTest(count=count), self.assertRaises(ValueError):
                fragments.source_spans(raw, count)

    def test_changed_control_stops_before_any_visibility_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); run = root/'run'; run.mkdir()
            (run/'exotica-future-5200.xwd').write_bytes(b'packet')
            (run/'exotica-host-5200-quads.bin').write_bytes(bytes(260))
            (run/'exotica-host-5200-instances.bin').write_bytes(
                struct.pack('<11I', 1, 2, 3, 0, 0, 3, 0, 0, 0, 0, 1))
            (run/'exotica-future-5200-after-color.bin').write_bytes(b'color')
            (run/'exotica-future-5200-after-depth.bin').write_bytes(b'depth')
            with patch.object(fragments, 'parse', return_value={'quads':[{}]}), \
                 patch.object(fragments, 'render_owned', return_value=(b'changed', b'depth', b'')) as render:
                self.assertEqual(fragments.main([str(run), '--frame', '5200',
                    '--output', str(root/'out')]), 1)
                self.assertEqual(render.call_count, 1)
            report = json.loads((root/'out/report.json').read_text(encoding='utf-8'))
            self.assertFalse(report['passed'])
            self.assertFalse(report['selection_passed'])
            self.assertNotIn('sources', report)


if __name__ == '__main__':
    unittest.main()
