import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_world_bindings import check


class BindingEvidenceTests(unittest.TestCase):
    def test_missing_wrong_owner_and_wrong_final_writes_fail(self):
        with tempfile.TemporaryDirectory() as td:
            p,b=Path(td)/'placements.jsonl',Path(td)/'bindings.jsonl'
            before=[0]*28;after=list(before);after[16]=0x4700;after[17]=1234
            obj=dict(serial=1,frame=20,end_frame=20,object=0x12000,initial=before,actual=after)
            p.write_text(json.dumps(obj)+'\n')
            writes=[dict(serial=1,frame=20,object=0x12000,field=f,pc=100+f,value=after[f],
                         mask=0xffffffff,registers=[0]*8,sources=[],code=[0]*6) for f in (16,17)]
            def save():b.write_text(''.join(json.dumps(w)+'\n' for w in writes))
            save();self.assertTrue(check(p,b)['passed'])
            obj.update(binding_scope=3,binding_first_frame=19,binding_resources=[1,2,100,200,after[16],after[17]])
            p.write_text(json.dumps(obj)+'\n')
            # The early scope must fail when only late, already-initialized
            # values were captured, even if its before/after snapshots agree.
            self.assertFalse(check(p,b)['passed'])
            for w in writes:w.update(phase=0,frame=19)
            save();self.assertTrue(check(p,b)['passed'])
            writes[1]['value']+=1;save();self.assertFalse(check(p,b)['passed'])
            writes.pop();save();self.assertEqual(check(p,b)['changed_without_write'],1)
            writes[0]['object']+=28;save()
            with self.assertRaisesRegex(ValueError,'owner'):check(p,b)


if __name__=='__main__':unittest.main()
