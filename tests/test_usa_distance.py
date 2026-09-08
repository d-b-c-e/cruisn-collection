import argparse
import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
from game_patch import read_patch
from usa_distance import add_arguments, configure, compose
from analyze_usa_distance import summarize, FIELDS
from run_usa_distance_trials import motion_script


class UsaDistanceTests(unittest.TestCase):
    def test_probe_interval_is_frozen_in_the_trial(self):
        script=motion_script(1500,5000)
        self.assertIn('tonumber(5000)',script)
        self.assertNotIn('CRUISN_MOTION_LAST',script)
        self.assertIn('p==0x809800 and m==0x809809',script)
        with self.assertRaises(ValueError):motion_script(1500,15000)

    def args(self, *words):
        parser=argparse.ArgumentParser();add_arguments(parser)
        return parser.parse_args(words)

    def test_revision_and_independent_residency_control(self):
        settings={}
        self.assertIsNone(configure(self.args(),'crusnusa',settings))
        self.assertFalse(settings)
        self.assertEqual(configure(self.args('--usa-far','160000'),'crusnusa',settings),dict(far=160000,residency=1))
        self.assertEqual(configure(self.args('--usa-far','160000','--usa-residency','0'),'crusnusa',settings),dict(far=160000,residency=0))
        for rom in ('crusnusa40','crusnwld24','offroadc','crusnexo'):
            with self.assertRaises(ValueError):configure(self.args('--usa-far','160000'),rom,{})
        with self.assertRaises(ValueError):configure(self.args('--usa-residency','0'),'crusnusa',{})
        with self.assertRaises(ValueError):configure(self.args('--usa-far','160000'),'crusnusa',{'MIDV_WORLD_FAR':'160000'})

    def test_dynamic_model_clamp_and_patch_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);base=root/'base.txt'
            base.write_text('C8 0C800000 08620056\n',encoding='utf-8')
            patch=read_patch(compose(base,root/'wide.txt',160000))
            self.assertEqual(patch[0xc8],(0x0c800000,0x08620056))
            self.assertEqual(patch[0x277],(0x04e01387,0x04e02710))
            self.assertEqual(patch[0x55],(80000,160000))
            self.assertNotIn(0x727d,patch)  # residency is a guarded read, not guest RAM editing
            base.write_text('55 00013880 00027100\n',encoding='utf-8')
            with self.assertRaises(ValueError):compose(base,root/'conflict.txt',240000)
            with self.assertRaises(FileExistsError):compose(base,root/'wide.txt',160000)

    def test_analyzer_rejects_missing_profile_and_out_of_range_reads(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'distance.csv'
            row=dict(zip(FIELDS,[1,160000,0,1,5,3,10,0,8000,2,3]))
            def save(rows):
                with path.open('w',newline='',encoding='utf-8') as f:
                    writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
            save([row]);self.assertEqual(summarize(path)['totals']['pending_comparisons'],2)
            for changes in ({'maximum_index':10001},{'effect_reads':11},{'profile_ok':0},{'far':80000},{'removal_comparisons':0}):
                save([{**row,**changes}])
                with self.assertRaises(ValueError):summarize(path)
            save([row,{**row,'frame':3}])
            with self.assertRaises(ValueError):summarize(path)
