import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from verify_exotica_future import check


class ExoticaFutureEvidence(unittest.TestCase):
    def test_incomplete_receipt_and_excessive_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp);path = directory/'exotica-section-capture.json'
            path.write_text(json.dumps(dict(schema=1, complete=False)))
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                check(directory)
            path.write_text(json.dumps(dict(schema=1, complete=True, first=1800, last=1000000,
                                            allocations=1, sections=1, snapshots=1)))
            with self.assertRaisesRegex(ValueError, 'budget'):
                check(directory)

    def test_duplicate_allocation_identity_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory/'exotica-section-capture.json').write_text(json.dumps(dict(schema=1, complete=True,
                first=1800, last=1800, allocations=2, sections=1, snapshots=1)))
            (directory/'exotica-section-allocations.jsonl').write_text('{"id":1}\n{"id":1}\n')
            (directory/'exotica-section-progress.csv').write_text('frame\n1800\n')
            with self.assertRaisesRegex(ValueError, 'sequence'):
                check(directory)
