from pathlib import Path
from types import SimpleNamespace
import csv,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from exotica_visibility import configure
from analyze_exotica_visibility import FIELDS,summarize
from derive_case import inherited_settings


class ExoticaVisibilityTests(unittest.TestCase):
    def test_derivation_preserves_and_rebinds_frozen_external_inputs(self):
        source={'MIDZ_GL':'1','MIDZ_VISIBILITY':'both','MIDV_PATCH':'@initial/game-patch.txt','MIDV_CHEATS':'@initial/cheats'}
        result=inherited_settings(Path('parent'),source)
        self.assertEqual(result['MIDV_PATCH'],str(Path('parent/initial/game-patch.txt')))
        self.assertEqual(result['MIDV_CHEATS'],str(Path('parent/initial/cheats')))
        self.assertEqual(result['MIDZ_VISIBILITY'],'both');self.assertEqual(source['MIDV_PATCH'],'@initial/game-patch.txt')
        self.assertEqual(inherited_settings('parent',{}),{})
        with self.assertRaises(ValueError):inherited_settings('parent',{'MIDV_PATCH':'../../mutable.txt'})

    def test_explicit_config_and_cross_game_rejection(self):
        settings={};self.assertIsNone(configure(SimpleNamespace(),'crusnexo',settings));self.assertEqual(settings,{})
        self.assertEqual(configure(SimpleNamespace(exotica_visibility='both'),'crusnexo',settings)['margin'],88)
        self.assertEqual(settings,{'MIDZ_VISIBILITY':'both'})
        for rom,settings in [('crusnusa',{}),('crusnexoa',{}),('crusnexo',{'MIDV_WORLD_FAR':'160000'})]:
            with self.assertRaises(ValueError):configure(SimpleNamespace(exotica_visibility='both'),rom,settings)

    def test_native_log_requires_complete_consistent_coverage(self):
        row=dict(zip(FIELDS,[0,'both',1,10,0,2,6000,9,8,7]))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'visibility.csv'
            def write(rows):
                with path.open('w',newline='') as f:
                    writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
            write([row,dict(row,frame=1)]);self.assertEqual(summarize(path,2)['totals']['accepted'],14)
            for changes in ({'frame':2},{'mode':'margins'},{'profile_ok':0},{'maximum_index':12801},{'extended_reads':0}):
                write([row,dict(row,frame=1,**{k:v for k,v in changes.items() if k!='frame'}) if 'frame' not in changes else dict(row,**changes)])
                with self.assertRaises(ValueError):summarize(path,2)
            write([row])
            with self.assertRaises(ValueError):summarize(path,2)
