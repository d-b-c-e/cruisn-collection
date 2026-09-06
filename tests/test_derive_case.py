from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from derive_case import validate_parent
from session_case import tree_hashes
from verification import sha256_file


class DerivationTests(unittest.TestCase):
    def test_parent_input_state_and_evidence_cannot_be_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            (case / 'initial').mkdir()
            (case / 'initial/state').write_bytes(b'starting state')
            (case / 'record/input').mkdir(parents=True)
            inp = case / 'record/input/session.inp'; inp.write_bytes(b'original inputs')
            manifest = dict(schema=1, status='recorded', initial_hashes=tree_hashes(case/'initial'),
                            inp_sha256=sha256_file(inp), rom_containers={}, every=60,
                            returncode=0, evidence={'frames': 60})
            with patch('derive_case.session_evidence', return_value={'frames':60}):
                validate_parent(case, manifest)
                inp.write_bytes(b'changed inputs')
                with self.assertRaisesRegex(ValueError, 'INP changed'): validate_parent(case, manifest)
                inp.write_bytes(b'original inputs')
                (case / 'initial/state').write_bytes(b'changed state')
                with self.assertRaisesRegex(ValueError, 'initial state changed'): validate_parent(case, manifest)
                (case / 'initial/state').write_bytes(b'starting state')
            with patch('derive_case.session_evidence', return_value={'frames':59}):
                with self.assertRaisesRegex(ValueError, 'evidence changed'): validate_parent(case, manifest)
