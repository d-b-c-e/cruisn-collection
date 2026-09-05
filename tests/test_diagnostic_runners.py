import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from diagnostic_runtime import diagnostic_env, execute, new_run
import run_capture
import run_oracle


class RunnerTests(unittest.TestCase):
    def test_inherited_actuation_and_diagnostics_are_removed(self):
        with patch.dict(os.environ, {"MIDV_FFB": "1", "MIDV_FFB_TEST": "70",
                                     "MIDV_GL": "1", "MIDV_QUADLOG": "old-file",
                                     "MIDV_TELEM_FORZA": "on", "SNAP_FRAMES": "1"}):
            env = diagnostic_env({"MIDV_FFB": "1", "MIDV_TELEM_FORZA": "on"})
        self.assertEqual(env["MIDV_FFB"], "0")
        for key in ("MIDV_FFB_TEST", "MIDV_GL", "MIDV_QUADLOG", "MIDV_TELEM_FORZA", "SNAP_FRAMES"):
            self.assertNotIn(key, env)

    def test_existing_evidence_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            proof = Path(td) / "keep.txt"
            proof.write_text("approved")
            with self.assertRaises(FileExistsError):
                new_run("test", td)
            self.assertEqual(proof.read_text(), "approved")

    def test_timeout_preserves_partial_output_and_reports_error(self):
        with tempfile.TemporaryDirectory() as td:
            result = execute([sys.executable, "-c",
                "import time; print('checkpoint', flush=True); time.sleep(10)"],
                td, diagnostic_env(), 1)
            self.assertIsNotNone(result["error"])
            self.assertIn("checkpoint", (Path(td) / "stdout.log").read_text())
            self.assertIsNone(json.loads((Path(td) / "invocation.json").read_text())["returncode"])

    def test_capture_cli_fails_when_emulator_omits_ram_dump(self):
        with tempfile.TemporaryDirectory() as td, patch.object(run_capture, "capture_run", return_value={}):
            out = Path(td) / "capture"
            rc = run_capture.main(["unused.exe", "600", "crusnusa", "--output", str(out)])
            self.assertEqual(rc, 1)
            report = json.loads((out / "capture-report.json").read_text())
            self.assertIn("missing or empty", report["error"])

    def test_oracle_cli_mismatch_cannot_publish_reference(self):
        with tempfile.TemporaryDirectory() as td, patch.object(run_oracle, "capture_run",
                 side_effect=[{"60": {"sha256": "a"}}, {"60": {"sha256": "b"}}]):
            out, reference = Path(td) / "run", Path(td) / "reference"
            rc = run_oracle.main(["--frames", "60", "--output", str(out),
                                  "--reference-dir", str(reference)])
            self.assertEqual(rc, 1)
            self.assertFalse(reference.exists())
