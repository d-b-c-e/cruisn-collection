import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from stage_native_receipts import stage
from control_launch import FEATURES


class StagingTests(unittest.TestCase):
    def test_selects_exact_export_and_preserves_optional_capabilities(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); binary = root/'candidate.exe'; binary.write_bytes(b'fixture')
            target = root/'package'; (target/'patch').mkdir(parents=True)
            (target/'vunit.exe').write_bytes(binary.read_bytes())
            (root/'patch/ux').mkdir(parents=True)
            (root/'patch/vunit-poc-patches.patch').write_bytes(b'unrelated renderer series')
            patch = root/'patch/ux/selected.patch'; patch.write_bytes(b'exact ux series')
            receipt = dict(schema=1, executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                           native_commit='a'*40, native_tree='b'*40,
                           patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(), build_log_sha256='c'*64)
            Path(str(binary)+'.build.json').write_text(json.dumps(receipt), encoding='utf-8')
            features = dict(version=1, sha256=receipt['executable_sha256'], native_commit='a'*40,
                            features=sorted(FEATURES))
            Path(str(binary)+'.features.json').write_text(json.dumps(features), encoding='utf-8')
            stage(binary, target, root)
            self.assertEqual((target/'patch/vunit-poc-patches.patch').read_bytes(), patch.read_bytes())
            self.assertEqual((target/'vunit.exe.features.json').read_bytes(), Path(str(binary)+'.features.json').read_bytes())
            patch.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'exact corresponding'):
                stage(binary, target, root)
            patch.write_bytes(b'exact ux series')
            features['native_commit'] = 'd'*40
            Path(str(binary)+'.features.json').write_text(json.dumps(features), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'sources differ'):
                stage(binary, target, root)
