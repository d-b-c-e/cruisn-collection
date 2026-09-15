from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from vunit_host_failure import configure, verify_receipt


class HostFailureTests(unittest.TestCase):
    def test_selection_gates_and_inherited_injection(self):
        args = SimpleNamespace(candidate='candidate.exe', vunit_host_failure='original',
                               vunit_host_inject_failure_frame=100)
        for rom, game in [('crusnwld', 'WORLD'), ('crusnwld24', 'WORLD'),
                          ('crusnusa', 'USA'), ('offroadc', 'OFFROAD')]:
            settings = {'MIDV_GL': '1', 'MIDV_FFB': '0', f'MIDV_{game}_HOST_SCENERY': '2',
                        f'MIDV_{game}_HOST_FIRST': '50', f'MIDV_{game}_HOST_LAST': '150'}
            self.assertEqual(configure(args, rom, settings, 200)['inject'], 100)
            self.assertEqual(settings['MIDV_HOST_FAILURE_FRAME'], '100')
            with self.assertRaises(ValueError):
                configure(SimpleNamespace(), rom, settings, 200)
            for updates in ({'candidate': None}, {'headless': True}, {'native_renderer': True},
                            {'vunit_host_inject_failure_frame': 49},
                            {'vunit_host_inject_failure_frame': 151}):
                with self.subTest(updates=updates), self.assertRaises(ValueError):
                    configure(SimpleNamespace(**(vars(args) | updates)), rom, settings.copy(), 200)
            with self.assertRaises(ValueError):
                configure(args, rom, dict(settings, MIDV_FFB='1'), 200)
            with self.assertRaises(ValueError):
                configure(args, rom, settings, 151)
            # An explicit non-injection run clears a prior saved injected frame.
            trial = configure(SimpleNamespace(candidate='x', vunit_host_failure='strict'), rom, settings, 200)
            self.assertEqual(trial['inject'], 0)
            self.assertNotIn('MIDV_HOST_FAILURE_FRAME', settings)
        self.assertIsNone(configure(SimpleNamespace(), 'crusnusa', {}, 200))
        with self.assertRaises(ValueError):
            configure(args, 'crusnexo', {}, 200)

    def test_receipts_and_degraded_scope(self):
        trial = dict(policy='original', inject=100, first=50, last=150)
        ack = 'VUNIT_HOST_FAILURE_POLICY original=1 inject=100\n'
        event = 'VUNIT_HOST_PREP_FAILURE frame=101 stage=4 fallback=1\n'
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            def write(a, b):
                (root/'stdout.log').write_text(a, encoding='utf-8')
                (root/'stderr.log').write_text(b, encoding='utf-8')
            write(ack, event)
            result = verify_receipt(trial, root)
            self.assertTrue(result['degraded'])
            self.assertEqual(result['event']['frame'], 101)
            for a, b in [('', event), (ack, ''), (ack+ack, event), (ack, event+event),
                         (ack, event.replace('101', '99')), (ack, event.replace('101', '151')),
                         (ack, event.replace('stage=4', 'stage=2')),
                         (ack, event.replace('fallback=1', 'fallback=0')),
                         (ack, event.replace('stage=4', 'stage=5'))]:
                write(a, b)
                with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                    verify_receipt(trial, root)
            write(ack, event)
            with self.assertRaises(ValueError):
                verify_receipt(None, root)
            write('', '')
            self.assertIsNone(verify_receipt(None, root))
            write(ack.replace('100', '0'), '')
            self.assertFalse(verify_receipt(dict(trial, inject=0), root)['degraded'])
            write(ack.replace('100', '0'), event.replace('stage=4', 'stage=3'))
            self.assertTrue(verify_receipt(dict(trial, inject=0), root)['degraded'])
            write(ack.replace('100', '0'), event)
            with self.assertRaises(ValueError):
                verify_receipt(dict(trial, inject=0), root)


if __name__ == '__main__':
    unittest.main()
