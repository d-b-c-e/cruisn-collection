from pathlib import Path
import csv,struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_exotica_frustum import c31,evaluate,planes
from run_exotica_visibility_trials import probe_source
from compare_exotica_visibility import compare
from analyze_exotica_frustum import FIELDS,TRIAL_FIELDS


def encoded(value):
    if value==0:return '80000000'
    ieee=struct.unpack('<I',struct.pack('<f',value))[0]
    assert value>0
    return f'{((((ieee>>23)-127)&255)<<24)|(ieee&0x7fffff):08x}'


def sample(x=60000,y=0,depth=160000,radius=1000,accepted=0):
    row=dict(frame='2500',sequence='1',list='bbb5',object='12000',flags='0',model='c01234',
             depth=str(depth),radius=str(radius),index='4999',far='204800',
             x=encoded(x),y=encoded(y),z=encoded(depth),factor=encoded(.0064),accepted=str(accepted))
    for k,v in planes(x,y,radius,c31(int(row['factor'],16))).items():
        row[k]=f'{struct.unpack("<I",struct.pack("<f",v))[0]:08x}'
    return row


class ExoticaFrustumTests(unittest.TestCase):
    def test_bounded_trial_is_explicit_and_frozen_in_the_recorded_probe(self):
        source=probe_source(2500,4300,1,88)
        self.assertNotIn('os.getenv(',source)
        self.assertIn('local reciprocal=tonumber(1)',source)
        self.assertIn('local margin=tonumber(88)',source)
        for values in ((0,4300,1,88),(2500,15000,1,88),(2500,4300,2,88),(2500,4300,1,120)):
            with self.assertRaises(ValueError):probe_source(*values)

    def test_effective_factor_and_shifted_margin_operands_are_checked(self):
        row=sample(accepted=1)
        row.update(original_factor=row['factor'],reciprocal='1',margin='88',factor=encoded(.0032))
        # Match the six-decimal reciprocal for index10000 exactly.
        for k,v in planes(60000,0,1000,c31(int(row['factor'],16))).items():
            row[k]=f'{struct.unpack("<I",struct.pack("<f",v+(88 if k=="xu" else 0)))[0]:08x}'
        result=evaluate(row)
        self.assertEqual(result['reason'],'accepted')
        self.assertEqual(result['margin'],88)
        with self.assertRaises(ValueError):evaluate({**row,'factor':row['original_factor']})
        with self.assertRaises(ValueError):evaluate({**row,'margin':'0'})

    def test_equal_pose_comparison_does_not_hide_route_or_missing_row_differences(self):
        stock=sample(x=45000,depth=80000)
        candidate={**stock,'accepted':'1','reciprocal':'0','margin':'88','original_factor':stock['factor']}
        candidate['xu']=f'{struct.unpack("<I",struct.pack("<f",struct.unpack("<f",struct.pack("<I",int(stock["xu"],16)))[0]+88))[0]:08x}'
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/'stock.csv',Path(td)/'candidate.csv'
            def save(path,fields,rows):
                with path.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
            save(a,FIELDS,[stock]);save(b,TRIAL_FIELDS,[candidate])
            r=compare(a,b);self.assertTrue(r['passed']);self.assertEqual(r['additions_at_equal_pose'],1)
            save(a,FIELDS,[stock,{**stock,'frame':'2501','sequence':'2'}])
            r=compare(a,b);self.assertFalse(r['passed']);self.assertEqual(r['mismatched_poses'],1)

    def test_unclamped_factor_can_admit_a_rejected_distant_sphere(self):
        result=evaluate(sample())
        self.assertEqual(result['reason'],'xu')
        self.assertEqual(result['predicted'],'accepted')
        self.assertEqual(result['unclamped_index'],10000)
        self.assertLess(result['predicted_factor'],result['factor_value'])

    def test_delayed_y_branch_still_observes_x_lower_operand(self):
        row=sample(x=0,y=40000)
        row['xu']=''
        result=evaluate(row)
        self.assertEqual(result['reason'],'yu')
        self.assertEqual(result['predicted'],'accepted')
        with self.assertRaises(ValueError):evaluate({**row,'xl':''})

    def test_far_reject_is_not_a_projection_admission(self):
        row=sample(depth=250000)
        row.update(yl='',yu='',xl='',xu='')
        result=evaluate(row)
        self.assertEqual(result['reason'],'far')
        self.assertEqual(result['predicted'],'far')

    def test_margin_visibility_is_distinct_from_reciprocal_extension(self):
        result=evaluate(sample(x=45000,depth=80000))
        self.assertEqual(result['reason'],'xu')
        self.assertEqual(result['predicted'],'xu')
        self.assertEqual(result['predicted_wide88'],'accepted')

    def test_independent_acceptance_and_pose_are_required(self):
        row=sample()
        for changes in ({'accepted':'1'},{'index':'4000'},{'xu':''},{'x':encoded(20000)}):
            with self.assertRaises(ValueError):evaluate({**row,**changes})
