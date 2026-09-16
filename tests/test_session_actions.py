import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from session_actions import normalize,write_schedule,configure,verify,PLAN,EVENTS
from session_case import compare_evidence


class SessionActionTests(unittest.TestCase):
    def test_schedule_bounds_and_frozen_identity(self):
        row=dict(frame=90,action='soft_reset')
        for actions in ([],[row]*2,[dict(row,frame=True)],[dict(row,frame=179)],
                        [dict(row,action='shell')],[dict(row,extra=1)],
                        [row,dict(row,frame=91)]):
            with self.assertRaises(ValueError):normalize(actions,180)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.assertEqual(configure(root,{},180),{})
            write_schedule(root/PLAN,[row],180)
            (root/'session_actions.lua').write_text('fixture',encoding='utf-8')
            result=configure(root,dict(session_actions=[row]),180)
            self.assertEqual(Path(result['SNAP_ACTIONS']),root/PLAN)
            with self.assertRaisesRegex(ValueError,'unrequested'):configure(root,{},180)
            with self.assertRaisesRegex(ValueError,'differs'):
                configure(root,dict(session_actions=[dict(row,frame=92)]),180)

    def test_actual_request_completion_and_missing_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            write_schedule(root/PLAN,[dict(frame=90,action='soft_reset')],180)
            lines=['id,event,frame,time','1,request,90,1.5','1,complete,90,1.5']
            def write(rows): (root/EVENTS).write_text('\n'.join(rows)+'\n',encoding='utf-8')
            write(lines);result=verify(root,180);self.assertEqual(result['completed'],1)
            variants=[lines[:-1],lines+[lines[-1]],
                      [*lines[:2],'1,complete,92,1.5'],[*lines[:2],'2,complete,90,1.5'],
                      [*lines[:2],'1,complete,90,nan'],[*lines[:2],'1,complete,90,1.7'],
                      [*lines[:2],'1,complete,90,1.4']]
            for rows in variants:
                write(rows)
                with self.assertRaises(ValueError):verify(root,180)
            with self.assertRaisesRegex(ValueError,'actions'):
                compare_evidence(root,root,{'session_actions':result},{})


if __name__=='__main__':unittest.main()
