import json
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from verify_exotica_future import check, check_section_matrix
from exotica_sections import yaw_matrix
from scenery_c31 import F


class ExoticaFutureEvidence(unittest.TestCase):
    def test_unrounded_reverse_section_matrix_and_stored_angle(self):
        # Synthetic angle words: integer17+one mantissa unit and integer5+seven.
        # This intentionally loses a low bit when the final sum is stored.
        trig = [4263704963, 4118653474, 3979254875, 4088417758,
                4178085694, 4258616668, 4788187]
        heading, header = F.integer(17).store()+1, F.integer(5).store()+7
        scalars = [0]*16;scalars[14:16] = [heading, 57820158]
        matrix = [4289198317, 2147483648, 4294353810, 2147483648, 0,
                  2147483648, 4278803566, 2147483648, 4289198317]
        row = dict(section=0xa00000, flags=1, scalars=scalars,
                   list_header=[0, 0, 0, header, 0], matrix=matrix, trig=trig)
        read = lambda p: 1 if p == row['section']+3 else self.fail('unexpected read')
        self.assertNotEqual(yaw_matrix(F.load(scalars[15]), trig), matrix)
        check_section_matrix(row, read)
        # Direction for object placement may clear on the third list while the
        # already-computed section matrix retains its original direction.
        row['flags'] = 0
        check_section_matrix(row, read)
        bad = copy.deepcopy(row);bad['scalars'][15] += 1
        with self.assertRaisesRegex(ValueError, 'stored section angle'):
            check_section_matrix(bad, read)
        bad = copy.deepcopy(row);bad['matrix'][0] += 1
        with self.assertRaisesRegex(ValueError, 'unrounded section matrix'):
            check_section_matrix(bad, read)
        bad = copy.deepcopy(row);bad['flags'] = 2
        with self.assertRaisesRegex(ValueError, 'section direction'):
            check_section_matrix(bad, read)

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
