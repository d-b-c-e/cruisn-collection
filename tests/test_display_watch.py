from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from display_watch import DisplayWatch


def display(name, width, primary=True):
    return dict(device=name, primary=primary, size=[width, 1440])


class DisplayWatchTests(unittest.TestCase):
    def test_order_changes_do_not_fail_but_transient_topology_does(self):
        original = [display('main', 2560), display('side', 2560, False)]
        views = [original, original[::-1], [display('merged', 5120)], original]
        watch = DisplayWatch(poll=lambda: views.pop(0), interval=3600, clock=lambda: 12.0)
        watch.start()
        watch.sample()
        watch.sample()
        watch.sample()
        report = watch.close()
        self.assertFalse(report['passed'])
        self.assertEqual(report['changes'], 2)
        self.assertEqual([row['monitors'][0]['device'] for row in report['samples']],
                         ['main', 'merged', 'main'])

    def test_stable_layout_and_enumeration_failure(self):
        watch = DisplayWatch(poll=lambda: [display('main', 2560)], interval=3600)
        watch.start()
        watch.sample()
        self.assertTrue(watch.close()['passed'])

        views = [[display('main', 2560)], []]
        watch = DisplayWatch(poll=lambda: views.pop(0), interval=3600)
        watch.start()
        watch.sample()
        report = watch.close()
        self.assertFalse(report['passed'])
        self.assertIn('no monitors', report['error'])


if __name__ == '__main__':
    unittest.main()
