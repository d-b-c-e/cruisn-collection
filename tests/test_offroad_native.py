from pathlib import Path
from types import SimpleNamespace
import csv,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from offroad_distance import configure
from analyze_offroad_native import FIELDS,TABLE_FIELDS,summarize
from run_offroad_native_trials import motion_script


class OffroadNativeTests(unittest.TestCase):
    def test_motion_probe_is_read_only_and_bounded(self):
        source=motion_script(1800,5990)
        self.assertNotIn('os.getenv(',source);self.assertNotIn('write_u32',source)
        self.assertNotIn('offroad_virtual_tail',source)
        with self.assertRaises(ValueError):motion_script(0,5990)
        with self.assertRaises(ValueError):motion_script(1800,16000)

    def test_game_guard_explicit_override_and_no_patch_mutation(self):
        settings={'MIDV_PATCH':'frozen.txt'}
        self.assertIsNone(configure(SimpleNamespace(),'offroadc',settings))
        trial=configure(SimpleNamespace(offroad_distance=3),'offroadc',settings)
        self.assertEqual(trial['far'],141888);self.assertEqual(trial['maximum_index'],191039)
        self.assertEqual(settings,{'MIDV_PATCH':'frozen.txt','MIDV_OFFROAD_DISTANCE':'3'})
        configure(SimpleNamespace(offroad_distance=0),'offroadc',settings)
        self.assertEqual(settings['MIDV_OFFROAD_DISTANCE'],'0')
        for rom,extra in [('offroadc1',{}),('crusnwld',{}),('offroadc',{'MIDV_USA_FAR':'80000'})]:
            with self.assertRaises(ValueError):configure(SimpleNamespace(offroad_distance=2),rom,extra)
        with self.assertRaises(ValueError):configure(SimpleNamespace(offroad_distance=4),'offroadc',{})

    def test_trace_requires_complete_coverage_and_consistent_counters(self):
        row=dict(zip(FIELDS,[0,2,1,10,3,1,2,3,4]))
        table=dict(zip(TABLE_FIELDS,[0,'1c45','0a414000',5,2,100,70000,0]))
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            def write(r=row,t=table):
                for name,fields,records in [('offroad-native.csv',FIELDS,[r]),('offroad-native-projection.csv',TABLE_FIELDS,[t])]:
                    with (d/name).open('w',newline='') as f:
                        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
            write();self.assertEqual(summarize(d,1)['extended_reads'],2)
            for changes in ({'frame':1},{'profile_ok':0},{'extra_admissions':0},{'multiplier':0},{'clip_reads':0}):
                write(dict(row,**changes))
                with self.assertRaises(ValueError):summarize(d,1)
            for changes in ({'maximum_index':127360},{'opcode':'0a414001'},{'pc':'1ea8'},
                            {'extended_reads':0},{'upper_clamps':1},{'frame':1}):
                write(t=dict(table,**changes))
                with self.assertRaises(ValueError):summarize(d,1)
            write()
            with self.assertRaises(ValueError):summarize(d,2)
