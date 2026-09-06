import configparser
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import force_options as F


class ForceOptionsTests(unittest.TestCase):
    def test_default_off_and_explicit_revision_off_beats_family_and_global_on(self):
        self.assertFalse(any(F.load({}).values()))
        section = {"ffb_impact": "1", "ffb_impact_crusnwld": "1", "ffb_impact_crusnwld24": "0"}
        self.assertFalse(F.impact_enabled(section.get, "crusnwld24"))
        self.assertTrue(F.impact_enabled(section.get, "crusnwld"))
        self.assertTrue(F.impact_enabled(section.get, "crusnwld23"))

    def test_world_toggle_roundtrips_to_the_launched_revision_without_changing_other_games(self):
        for revision in ("crusnwld24", "crusnwld"):
            with self.subTest(revision=revision):
                cp = configparser.ConfigParser()
                cp["collection"] = {"ffb_impact_crusnwld23": "1"}
                state = F.load(cp["collection"], revision)
                state["crusnwld"] = True
                cp["collection"].update(F.serialize(state, revision))
                self.assertEqual(F.load(cp["collection"], revision), state)
                self.assertTrue(F.impact_enabled(cp["collection"].get, revision))
                for rom in ("crusnusa", "offroadc", "crusnexo"):
                    self.assertFalse(F.impact_enabled(cp["collection"].get, rom))
                self.assertEqual(cp["collection"]["ffb_impact_crusnwld23"], "1")
