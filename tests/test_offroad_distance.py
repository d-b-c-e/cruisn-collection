from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from analyze_offroad_distance import summarize
from game_patch import read_patch,combine_patches
from run_offroad_distance_trials import trial_script


class OffroadDistanceTests(unittest.TestCase):
    def test_mutating_probe_freezes_scope_in_archived_source(self):
        script=trial_script(1800,5990,2)
        self.assertNotIn('os.getenv(',script)
        self.assertIn('local multiplier=tonumber(2)',script)
        self.assertIn("assert(cache[o-base]",script)
        for values in ((0,5990,2),(1800,5990,4),(1800,15000,2)):
            with self.assertRaises(ValueError):trial_script(*values)

    def test_far_patch_preserves_clipping_and_composes_with_widescreen(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'patch.txt'
            combine_patches([root/'patch/game/offroadc-widescreen.txt',root/'patch/game/offroadc-far125-experiment.txt'],path)
            patch=read_patch(path)
            self.assertEqual(patch[0x11221],(0x0f38c000,0x0f66f000))
            self.assertEqual(patch[0x11223],(0x0f78c000,0x0f78c000))
            self.assertEqual(patch[0x111a8],(63679,63679))
            self.assertEqual(patch[0x11235],(511,597))

    def test_culler_counts_and_all_table_paths_remain_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            far='frame,far,far_tests,stock_rejects,far_rejects,extra_admissions\n1,59120,100,10,2,8\n'
            table='frame,pc,opcode,reads,minimum_index,maximum_index,upper_clamps\n1,1c45,0a414000,3,184,63679,1\n'
            (root/'offroad-distance.csv').write_text(far)
            (root/'offroad-projection.csv').write_text(table)
            self.assertEqual(summarize(root)['totals']['extra_admissions'],8)
            for invalid in (table.replace('63679','63680'),table+'1,1c45,0a414000,3,184,63679,1\n',table.replace(',3,184',',0,184')):
                (root/'offroad-projection.csv').write_text(invalid)
                with self.assertRaises(ValueError):summarize(root)
            (root/'offroad-projection.csv').write_text(table)
            for invalid in (far.replace('59120','47296'),far.replace(',2,8',',2,9'),far+'3,59120,100,10,2,8\n',far+'2,59120\n'):
                (root/'offroad-distance.csv').write_text(invalid)
                with self.assertRaises(ValueError):summarize(root)
