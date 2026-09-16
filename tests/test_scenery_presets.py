from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
import scenery_presets as presets
import replay


class SceneryPresetTests(unittest.TestCase):
    def test_every_profile_parses_through_real_replay_before_any_run(self):
        class Parsed(Exception):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for rom in presets.PROFILES:
                (root/'case.json').write_text(json.dumps(dict(rom=rom)),encoding='utf-8')
                with self.subTest(rom=rom),patch.object(replay,'new_run',side_effect=Parsed) as start:
                    with self.assertRaises(Parsed):
                        replay.main([str(root),'--candidate','candidate.exe','--scenery-preset',presets.NAME])
                    start.assert_called_once()

    def test_all_supported_profiles_preserve_callers_capture_and_candidate(self):
        for rom in ('crusnusa','crusnwld24','crusnwld','offroadc','crusnexo'):
            with self.subTest(rom=rom):
                base=['case','--candidate','candidate.exe','--gl-capture','9000:9300','--scenery-preset',presets.NAME]
                expanded,proof=presets.expand(base,rom)
                self.assertEqual(expanded[:5],base[:5]);self.assertEqual(proof['rom'],rom)
                self.assertNotIn('--scenery-preset',expanded)
                controls=proof['controls'];keys=[x for x in controls if x.startswith('--')]
                self.assertEqual(len(keys),len(set(keys)))
                def value(key):return controls[controls.index(key)+1]
                self.assertEqual(value('--gl-crt'),'on');self.assertEqual(value('--gl-scale'),'4')
                if rom=='crusnexo':
                    self.assertEqual(value('--exotica-runtime'),'continuous')
                    self.assertEqual(value('--exotica-endpoint-snapshot'),'0')
                    self.assertEqual(value('--exotica-host-multiplier'),'3')
                    self.assertEqual(value('--exotica-host-failure'),'original')
                    self.assertNotIn('--gl-height',keys)
                else:
                    self.assertEqual(value('--vunit-runtime'),'continuous')
                    self.assertEqual(value('--vunit-journals'),'quiet')
                    self.assertEqual(value('--gl-height'),'400')
                expanded.clear();self.assertTrue(presets.PROFILES[rom])

    def test_explicit_conflicts_wrong_rom_and_ambiguous_selection_reject(self):
        base=['case','--scenery-preset='+presets.NAME]
        for option in presets.MANAGED:
            with self.subTest(option=option),self.assertRaises(ValueError):
                presets.expand(base+[option+'=value'],'crusnusa')
        for args,rom in ((base,'unknown'),(['case'],'crusnusa'),
                         (base+base[1:],'crusnusa'),(['case','--scenery-preset'],'crusnusa')):
            with self.assertRaises(ValueError):presets.expand(args,rom)
        a,_=presets.expand(base,'crusnwld24');b,_=presets.expand(base,'crusnwld')
        self.assertEqual(a,b)


if __name__=='__main__':unittest.main()
