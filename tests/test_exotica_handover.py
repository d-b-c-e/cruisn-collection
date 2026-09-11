from pathlib import Path
import csv
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import exotica_handover as h
import exotica_waiting as w


def write_csv(path,fields,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)


class ExoticaHandoverTests(unittest.TestCase):
    def test_explicit_mode_requires_candidate_waiting_and_real_fence(self):
        args=SimpleNamespace(exotica_host_handover='observe',candidate=Path('candidate.exe'))
        waiting=dict(mode='observe',snapshots=[3900])
        settings={};trial=h.configure(args,'crusnexo',settings,dict(fence=True),waiting)
        self.assertEqual(settings,{'MIDZ_HOST_HANDOVER':'1'});self.assertEqual(trial['waiting'],waiting)
        for rom,scene,wait in [('crusnusa',dict(fence=True),waiting),('crusnexo',dict(fence=False),waiting),
                               ('crusnexo',dict(fence=True),None)]:
            with self.assertRaises(ValueError):h.configure(args,rom,{},scene,wait)
        args.candidate=None
        with self.assertRaises(ValueError):h.configure(args,'crusnexo',{},dict(fence=True),waiting)
        args.exotica_host_handover=None
        self.assertIsNone(h.configure(args,'crusnexo',{},None,None))

    def fixture(self,root):
        first=(0x100a01000,0xa02000,0xa03000,4096,1,1)
        second=(0x100a01000,0xa02000,0xa03006,4127,1,2)
        owners=[first,second];owner_bytes=b''.join(struct.pack('<6Q',*v) for v in owners)
        kept=struct.pack('<6Q',*second)
        old_quads=b'a'*260+b'b'*260;filtered=b'b'*260
        instances=[(x[1],x[2],0,0,0,1,0,0,0,n,1) for n,x in enumerate(owners)]
        proposal={key:0 for key in w.FIELDS}
        proposal.update(scene=1,frame=3900,device_time='2.000000000000',epoch=1,sequence=2,
                        records=5,historical=2,candidates=2,instances=2,quads=2,hash=w.fingerprint(old_quads))
        write_csv(root/'exotica-waiting-scenes.csv',w.FIELDS,[proposal])
        write_csv(root/'exotica-host-fences.csv',('scene','ready_frame','ready_time','end_time'),
                  [dict(scene=1,ready_frame=3901,ready_time='2.200000000000',end_time='2.100000000000')])
        events=[]
        for op,time,owner,sequence in [('L',1,None,0),('A',1.1,first,1),('B',1.15,first,1),
                                       ('A',1.2,second,2),('B',1.25,second,2),('D',2.05,first,2)]:
            row={k:0 for k in w.exotica_lifetimes.FIELDS};row.update(event=op,frame=3899,time=f'{time:.12f}',epoch=1,sequence=sequence)
            if owner:
                realm,section,source,slot,epoch,generation=owner
                row.update(realm=realm,section=section,source=source,slot=slot,epoch=epoch,generation=generation)
            events.append(row)
        write_csv(root/'exotica-lifetime-events.csv',w.exotica_lifetimes.FIELDS,events)
        (root/'exotica-handover-cohorts.bin').write_bytes(struct.pack('<5Q',0x31484357,1,5,1,2)+owner_bytes)
        row=dict(scene=1,proposal_frame=3900,proposal_time='2.000000000000',proposal_records=5,end_records=6,
                 ready_frame=3901,ready_time='2.200000000000',ready_records=6,epoch=1,captured=2,submitted=1,
                 retired=0,retained=1,owners_hash=w.fingerprint(kept),instances=1,quads=1,
                 geometry_hash=w.fingerprint(filtered),guest_cycles=0)
        write_csv(root/'exotica-handover-scenes.csv',h.FIELDS,[row])
        for prefix,ob,ins,q in [('waiting',owner_bytes,instances,old_quads),
                              ('handover',kept,[instances[1][:9]+(0,1)],filtered)]:
            (root/f'exotica-{prefix}-3900-owners.bin').write_bytes(ob)
            (root/f'exotica-{prefix}-3900-instances.bin').write_bytes(b''.join(struct.pack('<11I',*v) for v in ins))
            (root/f'exotica-{prefix}-3900-quads.bin').write_bytes(q)
        trial=dict(mode='observe',waiting={'mode':'observe'},snapshots=[3900])
        text='MIDZ_HOST_HANDOVER=1\nMIDZ_HOST_HANDOVER_RESULT complete=1 scenes=1 captured=2 submitted=1 retired=0 bytes=136 snapshots=1 remaining=0\n'
        return trial,text

    def check(self,root,trial,text):
        # The parent observer/lifetime verifier has its own malformed-input
        # tests. Isolate the new completion contract here, assert it is called.
        with patch.object(w,'verify_receipt',return_value={'passed':True}) as verify:
            result=h.verify_receipt(trial,text,root)
            verify.assert_called_once_with(trial['waiting'],text,root)
            return result

    def test_actual_prefixes_retire_original_submission_and_preserve_subset_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);trial,text=self.fixture(root);result=self.check(root,trial,text)
            self.assertTrue(result['passed']);self.assertEqual(result['captured'],2)
            self.assertEqual(result['submitted'],1);self.assertEqual(result['owners_changed_after_cpu_end'],0)

    def test_wrong_completion_count_prefix_or_identity_is_rejected(self):
        for key,value in [('submitted',0),('ready_records',5),('end_records',7),('epoch',2),
                          ('owners_hash','0'*16),('geometry_hash','0'*16),('guest_cycles',1),('ready_time','2.3')]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);trial,text=self.fixture(root)
                rows=w.bounded_rows(root/'exotica-handover-scenes.csv',h.FIELDS);rows[0][key]=value
                write_csv(root/'exotica-handover-scenes.csv',h.FIELDS,rows)
                with self.assertRaises(ValueError):self.check(root,trial,text)

    def test_retirement_between_cpu_end_and_device_ready_is_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);trial,text=self.fixture(root)
            path=root/'exotica-lifetime-events.csv';events=w.bounded_rows(path,w.exotica_lifetimes.FIELDS)
            event=dict(events[-1]);event.update(event='F',slot=4127,time='2.150000000000',sequence=3)
            events.append(event);write_csv(path,w.exotica_lifetimes.FIELDS,events)
            path=root/'exotica-handover-scenes.csv';rows=w.bounded_rows(path,h.FIELDS)
            rows[0].update(ready_records=7,retired=1,retained=0,instances=0,quads=0,
                           owners_hash=w.fingerprint(b''),geometry_hash=w.fingerprint(b''))
            write_csv(path,h.FIELDS,rows)
            for name in ('owners','instances','quads'):(root/f'exotica-handover-3900-{name}.bin').write_bytes(b'')
            result=self.check(root,trial,text.replace('retired=0','retired=1'))
            self.assertEqual(result['owners_changed_after_cpu_end'],1)
            self.assertEqual(result['retired'],1)

    def test_truncated_trailing_duplicate_or_stale_cohort_is_rejected(self):
        for mutation in ('truncated','trailing','duplicate','stale','wrong_magic','oversize_count'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);trial,text=self.fixture(root);p=root/'exotica-handover-cohorts.bin';data=bytearray(p.read_bytes())
                if mutation=='truncated':data=data[:-1]
                elif mutation=='trailing':data+=b'x'
                elif mutation=='duplicate':data[88:136]=data[40:88]
                elif mutation=='stale':struct.pack_into('<Q',data,40+40,99)
                elif mutation=='wrong_magic':data[0]^=1
                else:struct.pack_into('<Q',data,32,2**63)
                p.write_bytes(data)
                with self.assertRaises(ValueError):self.check(root,trial,text)

    def test_geometry_and_unknown_artifacts_cannot_satisfy_receipt(self):
        for name in ('exotica-handover-3900-quads.bin','exotica-handover-3900-instances.bin','exotica-handover-9999-extra.bin'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);trial,text=self.fixture(root);(root/name).write_bytes(b'bad')
                with self.assertRaises(ValueError):self.check(root,trial,text)

    def test_disabled_missing_ack_and_incomplete_observer_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.assertIsNone(h.verify_receipt(None,'',root))
            trial,text=self.fixture(root)
            with self.assertRaises(ValueError):h.verify_receipt(None,'',root)
            for bad in ('',text.replace('complete=1','complete=0'),text+text):
                with self.assertRaises(ValueError):self.check(root,trial,bad)


if __name__=='__main__':unittest.main()
