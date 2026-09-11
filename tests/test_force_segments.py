from pathlib import Path
import json
import math
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import force_segments as f


def motor(t, value=63, enabled=1):
    return dict(t=f.nanoseconds(t), raw=value, adapted=value, request=-value/126, enabled=enabled)


def wheel(t, steer=.1, velocity=0):
    return dict(t=f.nanoseconds(t), frame=1, steer=steer, velocity=velocity)


def speed(t, source=2, sample=None):
    return dict(t=f.nanoseconds(t), sample=f.nanoseconds(t if sample is None else sample),
                value=25, source=source, quality=1 if source else 0)


class ForceSegmentTests(unittest.TestCase):
    def test_duration_weighting_is_independent_of_write_frequency(self):
        source = [motor(0, 0), motor(.25, 126), motor(1, 0)]
        frames = [wheel(0), wheel(1)]
        speeds = [speed(0), speed(1)]
        original, coverage = f.segments(source, frames, speeds, max_motor_age=2, max_speed_age=2)
        repeated, _ = f.segments(source[:2]+[motor(.3,126),motor(.31,126),motor(.8,126)]+source[2:],
                                 frames, speeds, max_motor_age=2, max_speed_age=2)
        self.assertEqual(f.metrics(original), f.metrics(repeated))
        self.assertEqual(f.metrics(original)['requested_abs_p50'], 1)
        self.assertAlmostEqual(f.metrics(original)['requested_rms'], math.sqrt(.75))
        self.assertEqual(f.metrics(original)['adapter_ceiling_fraction'], .75)
        self.assertEqual(f.metrics(original)['adapter_longest_ceiling_seconds'], .75)
        self.assertEqual(coverage['excluded_seconds'], {})

    def test_unknown_ends_and_age_expiry_are_not_extrapolated(self):
        rows, report = f.segments([motor(.1),motor(1)], [wheel(0),wheel(2)],
                                  [speed(0),speed(2)], max_speed_age=3)
        self.assertAlmostEqual(f.metrics(rows)['seconds'], .5)
        self.assertAlmostEqual(report['excluded_seconds']['motor_age_exceeds_selection_limit'], .4)
        self.assertEqual(report['start_seconds'], .1)
        self.assertEqual(report['end_seconds'], 1)

    def test_speed_uses_its_original_sample_age_and_retains_ocr_provenance(self):
        source, frames = [motor(0),motor(.2)], [wheel(0),wheel(.2)]
        speeds = [speed(0), speed(.05,sample=0), speed(.2)]
        rows, report = f.segments(source,frames,speeds)
        self.assertEqual(f.metrics(rows)['seconds'], .1)
        self.assertEqual(report['excluded_seconds']['speed_stale'], .1)
        rows, report = f.segments(source,frames,[speed(0,1),speed(.2,1)])
        self.assertEqual(rows, [])
        self.assertEqual(report['excluded_seconds']['speed_provenance_excluded'], .2)
        rows, _ = f.segments(source,frames,[speed(0,1),speed(.2,1)],allow_ocr=True)
        self.assertEqual(f.metrics(rows)['seconds'], .1)
        self.assertEqual({r['speed_source'] for r in rows}, {1})

    def test_simultaneous_last_write_wins_without_future_lookahead(self):
        rows, _ = f.segments([motor(0,0),motor(.1,126),motor(.1,63),motor(.2)],
                             [wheel(0),wheel(.2)], [speed(0),speed(.2)], max_speed_age=1)
        self.assertEqual([(r['start_ns'],r['end_ns'],r['adapted']) for r in rows],
                         [(0,100_000_000,0),(100_000_000,200_000_000,63)])

    def test_gate_and_no_velocity_are_excluded(self):
        rows, report = f.segments([motor(0,63,0),motor(.1),motor(.2)],
                                  [wheel(0,velocity=None),wheel(.2)], [speed(0),speed(.2)],max_speed_age=1)
        self.assertEqual(rows, [])
        self.assertEqual(report['excluded_seconds'], {'gate_disabled_at_last_motor_write':.1,
                                                       'steering_velocity_unavailable':.1})

    def test_bins_keep_direction_speed_and_steering_motion_separate(self):
        self.assertEqual(f.condition(20,.05,.25),'20-30mps/positive-small/steady')
        self.assertEqual(f.condition(30,-.2,.251),'30-40mps/negative-medium/slow')
        self.assertEqual(f.condition(60,.5,1.001),'60-90mps/positive-large/fast')
        self.assertIsNone(f.condition(9.99,.1,0))
        self.assertIsNone(f.condition(90,.1,0))

    def test_disconnected_intervals_do_not_count_as_contiguous(self):
        rows = [dict(start_ns=0,end_ns=100,raw=0,adapted=0,request=0),
                dict(start_ns=200,end_ns=250,raw=0,adapted=0,request=0)]
        self.assertEqual(f.metrics(rows)['longest_contiguous_seconds'], 100/f.NS)

    def test_clocks_and_malformed_csv_are_rejected(self):
        for value in ('nan','inf','-1','86401'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                f.nanoseconds(value)
        self.assertEqual(f.nanoseconds('1.0000000005'),1_000_000_001)
        with self.assertRaises(ValueError):
            f.ordered([dict(t=2),dict(t=1)])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.csv'
            for text in ('a,b\n1\n','a,b\n1,2,3\n','a,a\n1,2\n','a,b\n'):
                path.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValueError):
                    f.read_csv(path)

    def fixture(self, root, game):
        path=root/game/'run';path.mkdir(parents=True)
        (path.parent/'report.json').write_text(json.dumps({'passed':True}))
        invocation={'command':['vunit.exe',f.GAMES[game]],'environment':{'MIDV_FFB':'0'},
                    'executable_sha256':'a'*64}
        (path/'invocation.json').write_text(json.dumps(invocation))
        (path/'force-source.csv').write_text(
            f'# schema=1 game={f.GAMES[game]} units=signed_motor_byte clock=emulated\n'+
            ','.join(f.SOURCE)+'\n0.01,0,63,63\n0.03,2,0,0\n')
        (path/'force-gate.csv').write_text(','.join(f.GATE)+'\n0.01,0,1,63,-16384,0,0\n0.03,2,1,0,0,0,0\n')
        key=':ANALOG3' if game=='exotica' else ':WHEEL'
        (path/'frames.csv').write_text(f'frame,emulated_seconds,{key}\n1,0.01,128\n2,0.02,128\n3,0.03,128\n')
        (path/'signals.csv').write_text('# schema=1 clock=emulated signal=speed unit=metres_per_second\n'+
            ','.join(f.SIGNAL)+'\n0.01,0,2,1,0.01,0,25\n0.02,1,2,1,0.02,1,25\n0.03,2,2,1,0.03,2,25\n')
        return path

    def test_four_game_report_has_explicit_acceptance_limits_and_build_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs={game:self.fixture(Path(tmp),game) for game in f.GAMES}
            result=f.compare(runs,minimum_seconds=.005)
            self.assertTrue(result['passed'])
            self.assertTrue(result['shared_condition_coverage'])
            self.assertFalse(result['normalization_accepted'])
            self.assertFalse(result['contacts_reviewed'])
            path=runs['exotica']/'invocation.json'
            invocation=json.loads(path.read_text());invocation['executable_sha256']='b'*64
            path.write_text(json.dumps(invocation))
            with self.assertRaisesRegex(ValueError,'same native'):
                f.compare(runs)

    def test_invalid_pair_polarity_frame_provenance_and_replay_are_rejected(self):
        changes=[('force-gate.csv','0.01,0,1,63','0.01,0,1,62'),
                 ('force-gate.csv','-16384','16384'),
                 ('signals.csv','0.02,1,2,1,0.02','0.021,1,2,1,0.02'),
                 ('signals.csv','0.02,1,2,1,0.02','0.02,1,2,1,0.025'),
                 ('force-source.csv','clock=emulated','clock=host'),
                 ('frames.csv','2,0.02','4,0.02'),
                 ('invocation.json','"MIDV_FFB": "0"','"MIDV_FFB": "1"')]
        for filename, old, new in changes:
            with self.subTest(filename=filename,old=old), tempfile.TemporaryDirectory() as tmp:
                run=self.fixture(Path(tmp),'usa');path=run/filename
                text=path.read_text();self.assertIn(old,text);path.write_text(text.replace(old,new))
                with self.assertRaises(ValueError):f.parse_run(run,'usa')

    def test_world_memory_opt_in_requires_the_actual_collector_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs={game:self.fixture(Path(tmp),game) for game in f.GAMES}
            with self.assertRaises((ValueError,OSError)):
                f.compare(runs,world_speed_probe=True)


if __name__=='__main__':unittest.main()
