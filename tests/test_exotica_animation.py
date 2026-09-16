import sys
import unittest
import json
import tempfile
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_animation import decode, step, initial_fields
from verify_exotica_animation import verify


class AnimationTests(unittest.TestCase):
    def test_countdown_and_wrapping(self):
        s=decode(0x03010002,[0xa00100,0xa00200,0xfffffffe])
        state=(3,2,0x12a00300)
        expected=[(2,2,0x12a00300),(1,2,0x12a00300),(3,1,0xa00100),
                  (2,1,0xa00100),(1,1,0xa00100),(3,2,0xa00200)]
        for actual in expected:
            state=step(s,state)
            self.assertEqual(state,actual)
        self.assertEqual(step(s,(0,2,0xa00300)),(3,1,0xa00100))

    def test_rejections(self):
        words=[0xa00100,0xa00200,0xfffffffe]
        for header in (2,0x03000003,0x03030002,-1,0x100000000):
            with self.assertRaises(ValueError):decode(header,words)
        for values in ([],words[:-1],[0xa00100,0xa00200,0xffffffff],
                       [0x1a00100,0xa00200,0xfffffffe]):
            with self.assertRaises(ValueError):decode(0x03010002,values)
        s=decode(0x03010002,words)
        for state in ((4,0,0xa00100),(1,3,0xa00100),(1,0,0),(1,-1,0xa00100)):
            with self.assertRaises(ValueError):step(s,state)

    def test_capture_requires_original_and_compiled_agreement(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);native=root/'native';native.write_bytes(b'fixture')
            summary=dict(complete=True,error=None,first=7160,last=7200,events=1,tables=1)
            table=dict(kind=0,start=0xb00000,header=0x03000001,values=[0xa00100,0xffffffff])
            event=dict(kind=1,id=1,frame=7160,node=0xfe33,owner=0x12345,start=table['start'],header=table['header'],
                       before_remaining=1,before_cursor=table['start']+1,before_model=0xa00200,
                       after_remaining=3,after_cursor=table['start']+1,after_model=0xa00100)
            def save():
                (root/'exotica-animation-capture.json').write_text(json.dumps(summary),encoding='utf-8')
                (root/'exotica-animation-events.jsonl').write_text('\n'.join(map(json.dumps,[table,event]))+'\n',encoding='utf-8')
            save()
            with patch('verify_exotica_animation.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=f'3 1 {0xa00100}\n')) as run:
                self.assertTrue(verify(root,native)['passed'])
                self.assertIn('E 11534336 1 1 10486272',run.call_args.kwargs['input'])
            event['after_model']=0xa00300;save()
            with patch('verify_exotica_animation.subprocess.run') as run:
                with self.assertRaisesRegex(ValueError,'original animation mismatch'):verify(root,native)
                run.assert_not_called()
            event['after_model']=0xa00100;summary['complete']=False;save()
            with self.assertRaisesRegex(ValueError,'incomplete'):verify(root,native)

    def test_initializer_rejects_other_handlers_and_invalid_nodes(self):
        d=[0x01a00100,0,0,0,0,0]
        for node in (0,0xfff,0x2fffb,0x30000,0x31fff,0x3fffb,0xffffffff):
            with self.assertRaisesRegex(ValueError,'unsupported'):
                initial_fields(d,[],{},[],[],[],[],node)
        for kind in (0xa00,0xb00,0xc00,0xf00):
            d[5]=kind
            with self.assertRaisesRegex(ValueError,'unsupported'):
                initial_fields(d,[],{},[],[],[],[],0xfe33)


if __name__=='__main__':unittest.main()
