import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from diagnostic_runtime import execution_failure


class ExecutionFailure(unittest.TestCase):
    def test_emulator_cause_precedes_shutdown_counters(self):
        text='initialization\nFatal error: Exotica lifetime unmapped head PC85b4\ncomplete=0\n'
        self.assertEqual(execution_failure(dict(error=None,returncode=3),text),
                         'emulator exit code 3: Exotica lifetime unmapped head PC85b4')
        self.assertIsNone(execution_failure(dict(error=None,returncode=0),text))
        self.assertEqual(execution_failure(dict(error='timed out',returncode=None),text),'timed out')
        self.assertEqual(execution_failure(dict(error=None,returncode=7),'incomplete capture'),
                         'emulator exit code 7')


if __name__=='__main__':unittest.main()
