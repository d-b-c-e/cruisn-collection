from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from zeus_stream import configure_stall, verify_stall, parse_timings, analyze


ACK = ('MIDZ_GL_STALL frame=5400 milliseconds=100\n'
       'MIDZ_GL_STALL_APPLIED frame=5400 milliseconds=100 elapsed_ms=103\n')
TIMINGS = ('MIDZ_GL_TIMING phase=readback calls=2 total_ms=15 max_ms=10\n'
           'MIDZ_GL_TIMING phase=file calls=2 total_ms=80 max_ms=60\n'
           'MIDZ_GL_TIMING phase=swap calls=3 total_ms=0 max_ms=0\n'
           'MIDZ_GL_TIMING phase=stall calls=0 total_ms=0 max_ms=0\n')


class ZeusStreamTests(unittest.TestCase):
    def test_absent_controls_preserve_old_recordings(self):
        settings = {'MIDZ_GL': '1'}
        self.assertIsNone(configure_stall(SimpleNamespace(), 'crusnexo', settings, 6000))
        self.assertEqual(settings, {'MIDZ_GL': '1'})
        self.assertIsNone(verify_stall(None, ''))

    def test_stall_requires_candidate_and_valid_live_interval(self):
        settings = dict(MIDZ_GL='1', MIDZ_GL_STALL_FRAME='5400', MIDZ_GL_STALL_MS='100')
        args = SimpleNamespace(gl_stall='5400:100', candidate=Path('test.exe'))
        trial = configure_stall(args, 'crusnexo', settings, 6000)
        self.assertEqual(trial, dict(frame=5400, milliseconds=100, explicit=True))
        self.assertEqual(settings['MIDZ_GL_LOG'], '1')
        self.assertFalse(configure_stall(SimpleNamespace(), 'crusnexo', settings, 6000)['explicit'])
        for extra in ({'candidate': None}, {'headless': True}, {'native_renderer': True}, {'zeus_stop_frame': 5500}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                configure_stall(SimpleNamespace(**(vars(args) | extra)), 'crusnexo', settings.copy(), 6000)
        for key, value in [('MIDZ_GL', '0'), ('MIDZ_GL_STALL_FRAME', '0'),
                           ('MIDZ_GL_STALL_FRAME', '6000'), ('MIDZ_GL_STALL_FRAME', ' 5400'),
                           ('MIDZ_GL_STALL_MS', '5001'), ('MIDZ_GL_STALL_MS', None)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                configure_stall(args, 'crusnexo', settings | {key:value}, 6000)
        with self.assertRaises(ValueError):
            configure_stall(SimpleNamespace(), 'crusnwld', settings, 6000)

    def test_old_or_ignoring_binary_cannot_pass_stall_test(self):
        trial = dict(frame=5400, milliseconds=100)
        self.assertEqual(verify_stall(trial, ACK)['elapsed_ms'], 103)
        for text in ('', ACK.splitlines()[0], ACK + ACK,
                     ACK.replace('APPLIED frame=5400', 'APPLIED frame=5401'),
                     ACK.replace('milliseconds=100', 'milliseconds=0')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                verify_stall(trial, text)

    def test_incomplete_or_impossible_timing_receipts_fail(self):
        self.assertEqual(parse_timings(TIMINGS)['readback']['mean_ms'], 7.5)
        for text in ('', TIMINGS + TIMINGS.splitlines()[0],
                     TIMINGS.replace('phase=file', 'phase=readback'),
                     TIMINGS.replace('total_ms=15', 'total_ms=25'),
                     TIMINGS.replace('calls=0 total_ms=0', 'calls=0 total_ms=1')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_timings(text)

    def test_timeout_requires_explicit_expectation_and_measured_phase(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'invocation.json').write_text(json.dumps(dict(
                executable_sha256='fixture', environment={'MIDZ_GL_LOG':'1'})))
            (root / 'stderr.log').write_text(TIMINGS)
            (root / 'stdout.log').write_text('')
            (root / 'midz_gl.log').write_text('slow phase: completed_frame=5400 phase=file elapsed_ms=60\n')
            self.assertTrue(analyze(root)['passed'])
            with self.assertRaises(ValueError):
                analyze(root, True)
            failure = ('MIDZ render stream failed: consumer timeout; native presentation fallback; '
                       'presented=5400 phase=file phase_ms=650\n')
            (root / 'stderr.log').write_text(TIMINGS + failure)
            with self.assertRaises(ValueError):
                analyze(root)
            with self.assertRaises(ValueError):
                analyze(root, True)
            (root / 'stdout.log').write_text(
                'MIDZ stream wait: presented=5400 type=2 need=1000 queued=67108800 '
                'consumer_bytes=0 wait_ms=550 phase=file phase_ms=650\n')
            self.assertTrue(analyze(root, True)['expected_timeout'])
            (root / 'midz_gl.log').write_text('slow phase: completed_frame=5400 phase=file elapsed_ms=61\n')
            with self.assertRaises(ValueError):
                analyze(root, True)


if __name__ == '__main__':
    unittest.main()
