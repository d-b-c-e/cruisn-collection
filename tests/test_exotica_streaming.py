import csv,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_exotica_streaming import TRIAL_FIELDS,summarize
from run_exotica_admission_trials import admission_probe_source


class ExoticaStreamingTests(unittest.TestCase):
    def test_actual_second_comparison_is_required(self):
        row=dict(frame=4500,sequence=1,kind='admission',pc='b773',object='12000',model='da1234',flags='0',
            depth=100000,threshold=90000,cursor=0,pointer='0',section=5,lead=45,tail=6,upper=50,effective_threshold=160000)
        check={**row,'sequence':2,'kind':'admission_check','pc':'b776'}
        look={**row,'sequence':3,'kind':'lookahead','pc':'b7bc','object':'0','model':'0','depth':0,'threshold':62,'effective_threshold':62,'cursor':120}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'trace.csv'
            def save(rows):
                with p.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=TRIAL_FIELDS);w.writeheader();w.writerows(rows)
            save([row,check,look]);r=summarize(p)
            self.assertEqual(r['admitted'],1);self.assertEqual(r['admission_override'],160000)
            self.assertEqual(json.loads(json.dumps(r)),r)
            save([row,{**look,'sequence':2}])
            with self.assertRaises(ValueError):summarize(p)
            save([{**row,'effective_threshold':90000},check,look])
            with self.assertRaises(ValueError):summarize(p)
            save([row,check,{**look,'cursor':-1}])
            with self.assertRaises(ValueError):summarize(p)

    def test_trial_factory_freezes_both_probes_and_preserves_far(self):
        source=admission_probe_source(4500,5990,160000)
        self.assertNotIn('os.getenv(',source)
        self.assertIn('local admission=tonumber(160000)',source)
        self.assertIn('local far=tonumber(204800)',source)
        self.assertIn('visibility(n);streaming(n)',source)
        for args in ((0,5990,160000),(4500,5990,204800),(4500,5990,2)):
            with self.assertRaises(ValueError):admission_probe_source(*args)
