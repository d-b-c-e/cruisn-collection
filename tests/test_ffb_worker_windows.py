import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import ffb_worker_windows as w
from verification import sha256_file,write_json

N=w.NS


class WorkerWindowTests(unittest.TestCase):
    def test_clock_interior_excludes_unobserved_edges(self):
        clock=w.ClockMap([(i*N,(10+i)*N) for i in range(1,7)])
        r=clock.interior(1500000000,4500000000)
        self.assertEqual((r['start_ns'],r['end_ns']),(12*N+1,14*N-1))
        self.assertEqual(r['start_bounds_ns'],[11*N-1,12*N+1])
        self.assertEqual(r['end_bounds_ns'],[14*N-1,15*N+1])
        self.assertEqual(r['boundary_uncertainty_ns'],2*N+4)

    def test_exact_and_duplicate_emulated_times_are_not_exact_host_boundaries(self):
        clock=w.ClockMap([(N,10*N),(2*N,11*N),(2*N,12*N),(3*N,13*N),(4*N,14*N),(5*N,15*N)])
        r=clock.interior(2*N,4*N)
        self.assertFalse(r['usable'])  # Only one strictly interior timestamp.
        r=clock.interior(1500000000,4500000000)
        self.assertEqual((r['start_ns'],r['end_ns']),(11*N+1,14*N-1))

    def test_unbracketed_or_tiny_windows_are_excluded(self):
        c=w.ClockMap([(i*N,i*N) for i in range(1,8)])
        for a,b in ((0,3*N),(2*N,9*N),(2100000000,2900000000)):
            self.assertFalse(c.interior(a,b)['usable'])
        for pair in ((-1,1),(1,1),(2,1)):
            with self.assertRaises(ValueError):c.interior(*pair)

    def test_clock_reversal_rejected(self):
        for anchors in ([(1,2),(0,3)],[(1,2),(2,1)],[(1,2)],[(1,2),(2,float('nan'))]):
            with self.assertRaises(ValueError):w.ClockMap(anchors)

    def test_sink_only_changes_after_acceptance_and_clears_at_stop(self):
        ticks=[dict(sequence='1',host_seconds='1',out='100',sink_host_seconds='1.2'),
               dict(sequence='2',host_seconds='2',out='100',sink_host_seconds='-1'),
               dict(sequence='3',host_seconds='3',out='-100',sink_host_seconds='3.2')]
        self.assertEqual(w.held_output(ticks,4*N),[(N,1200000000,0),(1200000000,3200000000,100),(3200000000,4*N,-100)])
        ticks[1]['sink_host_seconds']='2'
        with self.assertRaises(ValueError):w.held_output(ticks,4*N)

    def test_equal_sink_times_keep_last_output_without_fictitious_duration(self):
        ticks=[dict(sequence=str(i),host_seconds='1',out=str(value),sink_host_seconds='1') for i,value in ((1,100),(2,-100))]
        self.assertEqual(w.held_output(ticks,2*N),[(N,2*N,-100)])

    def test_time_weights_do_not_count_repeated_output_records(self):
        rows=[(0,N,0),(N,3*N,100),(3*N,4*N,-200)]
        split=[(0,N,0),(N,2*N,100),(2*N,3*N,100),(3*N,4*N,-200)]
        a=w.measure(rows,[(0,4*N)],200)
        self.assertEqual(a,w.measure(split,[(0,4*N)],200))
        self.assertEqual(a['seconds'],4);self.assertEqual(a['absolute_p50'],100/32767)
        self.assertEqual(a['absolute_p90'],200/32767);self.assertEqual(a['requested_ceiling_fraction'],.25)
        self.assertEqual(a['signed_impulse_normalized_seconds'],0)

    def test_window_holes_do_not_add_mass_or_accept_missing_output(self):
        rows=[(0,4*N,100)]
        self.assertEqual(w.measure(rows,[(0,N),(3*N,4*N)],200)['seconds'],2)
        with self.assertRaises(ValueError):w.measure(rows,[(0,2*N),(N,3*N)],200)
        with self.assertRaises(ValueError):w.measure(rows,[(3*N,5*N)],200)
        with self.assertRaises(ValueError):w.measure([(0,N,100),(2*N,3*N,0)],[(0,N)],200)

    def test_near_ceiling_is_reported_separately_from_exact_saturation(self):
        r=w.measure([(0,N,990),(N,2*N,999),(2*N,3*N,1000),(3*N,4*N,989)],[(0,4*N)],1000)
        self.assertEqual(r['requested_ceiling_fraction'],.25)
        self.assertEqual(r['within_one_percent_of_ceiling_fraction'],.75)
        zero=w.measure([(0,N,0)],[(0,N)],0)
        self.assertEqual(zero['within_one_percent_of_ceiling_fraction'],0)

    def fixture(self,root):
        run=root/'run';run.mkdir()
        def csvfile(name,fields,rows):
            with (run/name).open('w',newline='') as stream:
                writer=csv.writer(stream);writer.writerow(fields);writer.writerows(rows)
        csvfile('ffb-worker-sources.csv',w.ffb_worker.SOURCE_FIELDS,
                [[i,10+i,i,i,0,0,1,0,0] for i in range(1,7)])
        csvfile('force-source.csv',w.SOURCE,[[i,i,0,0] for i in range(1,7)])
        csvfile('ffb-worker-ticks.csv',['sequence','host_seconds','out','sink_host_seconds'],
                [[1,10,100,10],[2,16,100,-1]])
        (run/'frames.csv').write_text('recorded input identity')
        receipt=dict(complete=True,sink_final_level=0,stop_host_seconds=17,strength=50,impact_axis=False)
        write_json(run/'ffb-worker-receipt.json',receipt)
        verified=dict(passed=True,physical_acceptance=False,receipt=receipt,source_join_rows=6,
                      hashes={name:sha256_file(run/name) for name in w.ffb_worker.FILES})
        write_json(root/'report.json',dict(passed=True,evidence=dict(trace_sha256=sha256_file(run/'frames.csv')),
                ffb_worker=dict(mode='observe',nominal_strength=50,result=verified)))
        write_json(run/'invocation.json',dict(environment=dict(MIDV_FFB='0'),executable_sha256='a'*64))
        spec=dict(schema=1,clock='emulated_nanoseconds',reviewed=False,
                  force_source_sha256=sha256_file(run/'force-source.csv'),frames_sha256=sha256_file(run/'frames.csv'),
                  windows=[dict(id='one',kind='unreviewed-turn',start_ns=1500000000,end_ns=4500000000)])
        return run,spec

    def test_analysis_preserves_unreviewed_status_and_measures_interior(self):
        with tempfile.TemporaryDirectory() as tmp:
            run,spec=self.fixture(Path(tmp));r=w.analyze(run,spec)
            self.assertTrue(r['passed']);self.assertFalse(r['windows_reviewed'])
            self.assertFalse(r['normalization_accepted']);self.assertFalse(r['physical_acceptance'])
            self.assertAlmostEqual(r['groups']['unreviewed-turn']['seconds'],2-2/N)

    def test_rejection_of_changed_journal_and_game_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            run,spec=self.fixture(Path(tmp))
            spec['frames_sha256']='wrong'
            with self.assertRaises(ValueError):w.analyze(run,spec)
            spec['frames_sha256']=sha256_file(run/'frames.csv')
            with (run/'ffb-worker-ticks.csv').open('a') as stream:stream.write('junk')
            with self.assertRaises(ValueError):w.analyze(run,spec)

    def test_changed_original_source_cannot_be_rebound_without_rejoining_anchors(self):
        with tempfile.TemporaryDirectory() as tmp:
            run,spec=self.fixture(Path(tmp));p=run/'force-source.csv'
            p.write_text(p.read_text().replace('1,1,0,0','1,1,1,0'))
            spec['force_source_sha256']=sha256_file(p)
            with self.assertRaises(ValueError):w.analyze(run,spec)

    def test_overlapping_windows_and_unsubstantiated_review_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run,spec=self.fixture(Path(tmp));spec['reviewed']=True
            with self.assertRaises(ValueError):w.analyze(run,spec)
            spec['reviewed']=False;spec['windows'].append(dict(spec['windows'][0],id='two'))
            with self.assertRaises(ValueError):w.analyze(run,spec)


if __name__=='__main__':unittest.main()
