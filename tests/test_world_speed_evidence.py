from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import world_speed_evidence as w
from force_segments import nanoseconds, segments


class WorldSpeedEvidenceTests(unittest.TestCase):
    def fixture(self):
        inputs = [dict(t=nanoseconds(t), frame=n, steer=0, velocity=0)
                  for n,t in enumerate([0,.05,.1,.15,.2,.25,.3,.35],1)]
        writes = [dict(sequence='1',seconds='.01',native_frame='1',frame='1',pc='1901',mask='ffffffff',
                       state='4',flags='4',player='2000',actor='2000',raw='06500000',display='50')]
        reads = [dict(sequence='1',seconds='.02',native_frame='1',frame='1',pc='9a5d',state='4',player='2000',display='50')]
        snapshots = [dict(frame=str(n),seconds=str(t/1e9),state='4',flags='4',player='2000',raw='06500000',display='50')
                     for n,t in ((i['frame'],i['t']) for i in inputs)]
        return writes,reads,snapshots,inputs

    def test_c31_conversion_uses_game_units_not_ieee(self):
        self.assertEqual(w.speed_word('80000000'),0)
        self.assertEqual(w.speed_word('0'),1)
        self.assertEqual(w.speed_word('06500000'),104)
        for value in ['nan','100000000','-1','00ffffff','7f000000']:
            with self.subTest(value=value), self.assertRaises(ValueError):w.speed_word(value)

    def test_valid_producer_and_hud_preserve_age_and_unknown_start(self):
        samples, report = w.verify_rows(*self.fixture())
        self.assertEqual(report['matched_hud_reads'],1)
        self.assertEqual(samples[0]['quality'],0)
        self.assertEqual(samples[1]['source'],3)
        self.assertAlmostEqual(samples[1]['value'],50*.44704)
        self.assertEqual(samples[1]['sample'],nanoseconds('.01'))
        self.assertEqual(samples[-1]['sample'],nanoseconds('.01'))
        # New snapshot does not refresh the producer's original timestamp.
        inputs=self.fixture()[-1]
        motor=[dict(t=0,enabled=1,raw=63,adapted=63,request=-.5),
               dict(t=nanoseconds('.35'),enabled=1,raw=63,adapted=63,request=-.5)]
        rows, _=segments(motor,inputs,samples)
        self.assertAlmostEqual(sum(r['end_ns']-r['start_ns'] for r in rows)/1e9,.06)

    def test_lifetime_and_player_change_clear_samples(self):
        args=self.fixture()
        args[2][2]['state']='5'
        args[2][3]['player']='3000'
        args[2][4]['flags']='0'
        samples,_=w.verify_rows(*args)
        self.assertEqual([s['quality'] for s in samples[1:5]],[1,0,0,0])
        self.assertTrue(all(s['quality']==0 for s in samples[5:]))

    def test_unobserved_writer_is_excluded_and_cannot_establish_hud_proof(self):
        args=self.fixture()
        args[1][0]['seconds']='.005'
        with self.assertRaisesRegex(ValueError,'no HUD read'):w.verify_rows(*args)
        after=deepcopy(args[1][0]);after.update(sequence='2',seconds='.02')
        args[1].append(after)
        _,report=w.verify_rows(*args)
        self.assertEqual(report['uncaptured_writer_reads'],1)
        self.assertEqual(report['matched_hud_reads'],1)

    def test_wrong_conversion_owner_pc_mask_and_lifetime_are_rejected(self):
        for field,value in [('display','51'),('actor','3000'),('player','0'),('pc','1900'),
                            ('mask','ffff'),('state','5'),('sequence','2'),('seconds','.06')]:
            args=self.fixture();args[0][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):w.verify_rows(*args)

    def test_hud_branch_clock_and_held_value_must_be_observed(self):
        for field,value in [('pc','9a59'),('display','49'),('player','3000'),('state','3'),
                            ('seconds','.06'),('sequence','2')]:
            args=self.fixture();args[1][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):w.verify_rows(*args)

    def test_snapshot_clock_and_coverage_are_not_inferred(self):
        for field,value in [('frame','4'),('seconds','.2'),('display','49')]:
            args=self.fixture();args[2][1][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):w.verify_rows(*args)
        args=self.fixture();args[0].append(deepcopy(args[0][0]));args[0][1]['sequence']='2'
        with self.assertRaisesRegex(ValueError,'nonmonotonic'):w.verify_rows(*args)


if __name__=='__main__':unittest.main()
