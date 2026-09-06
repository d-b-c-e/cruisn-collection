from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import json
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from run_regressions import validate,visual_content
import run_regressions


class RegressionSuiteTests(unittest.TestCase):
    def test_blank_framebuffer_is_not_a_visual_oracle(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            Image.new('RGB',(16,16),'black').save(path/'last.png')
            with self.assertRaises(ValueError):visual_content(path)
            image=Image.new('RGB',(16,16),'black');image.putpixel((1,1),(255,255,255));image.save(path/'last.png')
            self.assertEqual(visual_content(path)['files'],1)

    def test_incomplete_or_impossible_suites_are_rejected(self):
        for plan in ({'schema':1,'cases':[]},{'schema':1,'cases':[{'id':'../out'}]},
                     {'schema':1,'cases':[{'id':'x'},{'id':'x'}]},
                     {'schema':1,'cases':[{'id':'x','compare_gl':True,'presentation':'headless'}]}):
            with self.assertRaises(ValueError):validate(plan)

    def test_missing_timing_evidence_cannot_preserve_a_passing_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            case=root/'case'
            (case/'record/snap').mkdir(parents=True)
            image=Image.new('RGB',(16,16),'black')
            image.putpixel((1,1),(255,255,255))
            image.save(case/'record/snap/last.png')
            candidate=root/'candidate.exe';candidate.write_bytes(b'test candidate')
            plan=root/'suite.json'
            plan.write_text(json.dumps({'schema':1,'cases':[{'id':'test','path':str(case),
                'coverage':'test','timings':[{'first':1,'last':1000}]}]}))
            with mock.patch.object(run_regressions.replay,'main',return_value=0), \
                 mock.patch.object(run_regressions,'summarize',side_effect=ValueError('missing timing window')):
                code=run_regressions.main(['--suite',str(plan),'--candidate',str(candidate),
                                          '--output',str(root/'run')])
            report=json.loads((root/'run/report.json').read_text())
            self.assertEqual(code,1)
            self.assertFalse(report['passed'])
            self.assertFalse(report['cases'][0]['passed'])
            self.assertIn('missing timing',report['cases'][0]['error'])
