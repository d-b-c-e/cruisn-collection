from pathlib import Path
import struct,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_exotica_frustum import c31,evaluate,planes


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
