import configparser
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
import graphics_options as G
from game_patch import read_patch


def import_shell_module(name):
    # Stub only the missing GL dependency. Restoring all of sys.modules after
    # import unloads NumPy's new entries and breaks isolated Python 3.14 runs.
    missing_gl = importlib.util.find_spec("moderngl") is None
    if missing_gl:
        sys.modules["moderngl"] = types.ModuleType("moderngl")
    try:
        return importlib.import_module(name)
    finally:
        if missing_gl:
            sys.modules.pop("moderngl", None)


class SceneryOptionTests(unittest.TestCase):
    def test_revision_scale_and_widescreen_gates_preserve_saved_preference(self):
        section = {'scenery_distance_crusnwld': '1'}
        state = G.load(section)
        self.assertEqual(G.serialize(state)['scenery_distance_crusnwld'], '1')
        self.assertFalse(G.toggle(state, 'crusnwld', 'scenery_distance', 'crusnwld'))
        for rom, margin, scale in [('crusnwld',86,4), ('crusnwld24',0,4),
                                  ('crusnwld24',86,1), ('crusnusa',86,4),
                                  ('offroadc',86,4), ('crusnexo',86,4), ('crusnwld24',86,4)]:
            with tempfile.TemporaryDirectory() as directory:
                env=G.launch_overrides(ROOT,directory,rom,margin,scale,section,{})
            expected='all' if (rom,margin,scale)==('crusnwld24',86,4) else 'off'
            self.assertEqual(env['MIDV_SCENERY'], expected)
        values={r[0]:r[2] for r in G.rows('crusnwld',state,'crusnwld')}
        self.assertNotIn('scenery_distance', values)
        self.assertTrue(state['crusnwld']['scenery_distance'])


class WorldDistanceMenuTests(unittest.TestCase):
    def test_persistence_reverse_adjustment_and_exclusive_scenery_paths(self):
        state = G.load({})
        self.assertEqual(state['crusnwld']['world_distance'], 0)
        self.assertEqual(state['crusnwld']['world_lookahead'], 8)
        G.toggle(state, 'crusnwld', 'scenery_distance', 'crusnwld24')
        G.toggle(state, 'crusnwld', 'world_distance', 'crusnwld24', direction=-1)
        self.assertEqual(state['crusnwld']['world_distance'], 3)
        self.assertFalse(state['crusnwld']['scenery_distance'])
        G.toggle(state, 'crusnwld', 'world_lookahead', 'crusnwld24')
        self.assertEqual(state['crusnwld']['world_lookahead'], 12)
        self.assertEqual(G.load(G.serialize(state)), state)
        G.toggle(state, 'crusnwld', 'scenery_distance', 'crusnwld24')
        self.assertEqual(state['crusnwld']['world_distance'], 0)
        self.assertTrue(state['crusnwld']['scenery_distance'])
        edited = G.load({'world_distance_crusnwld':'3', 'scenery_distance_crusnwld':'1'})
        self.assertFalse(edited['crusnwld']['scenery_distance'])

    def test_all_presets_compose_checked_widescreen_terrain_and_replace_old_limits(self):
        section = {'world_distance_crusnwld':'3', 'terrain_visibility_crusnwld':'1'}
        base = dict(read_patch(ROOT/'patch/game/crusnwld24-widescreen.txt'))
        base.update(read_patch(ROOT/'patch/game/crusnwld-terrain-visibility-experimental.txt'))
        with tempfile.TemporaryDirectory() as directory:
            for distance in (3, 2):
                for lead in (0, 8, 12):
                    section.update(world_distance_crusnwld=str(distance), world_lookahead_crusnwld=str(lead))
                    env = G.launch_overrides(ROOT, directory, 'crusnwld24', 86, 4, section, {})
                    actual = read_patch(env['MIDV_PATCH'])
                    far = distance * 80000
                    self.assertEqual(actual[0x40], (80000, far))
                    for address, opcode in G.world_distance.CLAMPS.items():
                        self.assertEqual(actual[address], (opcode | 4999, opcode | (far // 16)))
                    self.assertTrue(all(actual[a] == v for a, v in base.items()))
                    self.assertEqual(env['MIDV_WORLD_FAR'], str(far))
                    self.assertEqual(env['MIDV_WORLD_LEAD'], str(lead))
                    self.assertEqual(env['MIDV_WORLD_CPU_PERCENT'], '100')
                    self.assertEqual((env['MIDV_SCENERY'],env['MIDV_SCENERY_LEAD']), ('off','0'))
            section['world_distance_crusnwld'] = '0'
            env = G.launch_overrides(ROOT, directory, 'crusnwld24', 86, 4, section, {})
            self.assertNotIn('MIDV_WORLD_FAR', env)
            self.assertEqual(read_patch(env['MIDV_PATCH']), base)

    def test_unsupported_revisions_and_display_modes_never_enable_native_hooks(self):
        section = {'world_distance_crusnwld':'3', 'world_lookahead_crusnwld':'12'}
        with tempfile.TemporaryDirectory() as directory:
            for rom, margin, scale in [('crusnwld',86,4), ('crusnwld23',86,4),
                    ('crusnusa',86,4), ('offroadc',86,4), ('crusnexo',86,4),
                    ('crusnwld24',0,4), ('crusnwld24',86,1)]:
                env = G.launch_overrides(ROOT, directory, rom, margin, scale, section, {})
                self.assertFalse(any(key.startswith('MIDV_WORLD_') for key in env))
                if 'MIDV_PATCH' in env:
                    self.assertNotIn(0x40, read_patch(env['MIDV_PATCH']))
        self.assertEqual(G.load(section)['crusnwld']['world_distance'], 3)
        for option in ('world_distance', 'world_lookahead'):
            self.assertFalse(G.toggle({}, 'crusnwld', option, 'crusnwld'))

    def test_explicit_patch_and_attended_cli_trial_override_saved_distance(self):
        section = {'world_distance_crusnwld':'3', 'world_lookahead_crusnwld':'12'}
        with tempfile.TemporaryDirectory() as directory:
            env = G.launch_overrides(ROOT, directory, 'crusnwld24', 86, 4, section,
                                     {'MIDV_PATCH':'developer.txt'})
            self.assertNotIn('MIDV_PATCH', env)
            self.assertNotIn('MIDV_WORLD_FAR', env)
            env = G.launch_overrides(ROOT, directory, 'crusnwld24', 86, 4, section, {},
                                     use_saved_distance=False)
            self.assertNotIn('MIDV_WORLD_FAR', env)
            patch = G.world_distance.compose(env['MIDV_PATCH'], Path(directory)/'recording.txt', 160000)
            self.assertEqual(read_patch(patch)[0x40], (80000,160000))


class GraphicsOptionsTests(unittest.TestCase):
    def test_settings_stay_per_game_and_world_revisions_share_seams(self):
        settings = G.load({})
        self.assertTrue(G.toggle(settings, "offroadc", "seam_alignment"))
        self.assertTrue(G.toggle(settings, "crusnwld", "seam_alignment"))
        self.assertTrue(G.toggle(settings, "crusnusa", "detail_distance"))
        cp = configparser.ConfigParser()
        cp["collection"] = G.serialize(settings)
        restored = G.load(cp["collection"])
        self.assertEqual(restored, settings)
        self.assertFalse(restored["crusnusa"]["seam_alignment"])
        self.assertTrue(G.for_game(cp["collection"], "crusnwld24")["seam_alignment"])

    def test_unsupported_options_cannot_be_activated_even_from_edited_ini(self):
        section = {f"{option}_{game}": "1" for game in G.GAMES for option in G.OPTIONS}
        for rom in ("crusnwld", "crusnwld24", "offroadc", "crusnexo", "crusnusa40"):
            with self.subTest(rom=rom), tempfile.TemporaryDirectory() as directory:
                selected = G.for_game(section, rom)
                self.assertFalse(selected["detail_distance"])
                self.assertFalse(selected["far_distance"])
                overrides = G.launch_overrides(ROOT, directory, rom, 0, 4, section, {})
                self.assertNotIn("MIDV_PATCH", overrides)
        self.assertFalse(G.toggle({}, "crusnexo", "seam_alignment"))
        self.assertEqual(G.rows("crusnexo", G.load(section)), [])

    def test_every_distance_combination_preserves_widescreen_and_off_removes_stale_words(self):
        widescreen = read_patch(ROOT / "patch/game/crusnusa-widescreen.txt")
        with tempfile.TemporaryDirectory() as directory:
            for detail, far in ((1, 1), (1, 0), (0, 1), (0, 0)):
                with self.subTest(detail=detail, far=far):
                    section = {"detail_distance_crusnusa": str(detail), "far_distance_crusnusa": str(far)}
                    env = G.launch_overrides(ROOT, directory, "crusnusa", 86, 4, section, {})
                    actual = read_patch(env["MIDV_PATCH"])
                    expected = dict(widescreen)
                    if detail:
                        expected.update(read_patch(ROOT / "patch/game/crusnusa-lod-experiment.txt"))
                    if far:
                        expected.update(read_patch(ROOT / "patch/game/crusnusa-farplane-experiment.txt"))
                    self.assertEqual(actual, expected)

    def test_classic_aspect_does_not_gain_the_widescreen_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            env = G.launch_overrides(ROOT, directory, "crusnusa", 0, 4,
                                     {"detail_distance_crusnusa": "1"}, {})
            self.assertEqual(set(read_patch(env["MIDV_PATCH"])), {0xbf, 0xc3})

    def test_world_terrain_composes_only_for_verified_widescreen_revisions(self):
        section = {"terrain_visibility_crusnwld": "1", "terrain_visibility_crusnusa": "1"}
        with tempfile.TemporaryDirectory() as directory:
            for rom in ("crusnwld", "crusnwld24"):
                env = G.launch_overrides(ROOT, directory, rom, 86, 4, section, {})
                expected = read_patch(ROOT / f"patch/game/{rom}-widescreen.txt")
                expected.update(read_patch(ROOT / "patch/game/crusnwld-terrain-visibility-experimental.txt"))
                self.assertEqual(read_patch(env["MIDV_PATCH"]), expected)
                standard = G.launch_overrides(ROOT, directory, rom, 86, 4, {}, {})
                self.assertNotIn(0xb4, read_patch(standard["MIDV_PATCH"]))
                self.assertNotIn("MIDV_PATCH", G.launch_overrides(ROOT, directory, rom, 0, 4, section, {}))
            for rom in ("crusnusa", "crusnwld23", "offroadc", "crusnexo"):
                self.assertFalse(G.for_game(section, rom)["terrain_visibility"])

    def test_seam_alignment_is_off_at_native_scale_and_marginfill_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            for scale in (1, 2, 4):
                env = G.launch_overrides(ROOT, directory, "offroadc", 0, scale,
                    {"seam_alignment_offroadc": "1", "marginfill": "1"}, {})
                self.assertEqual(env["MIDV_GL_TJUNCTIONS"], "0" if scale == 1 else "1")
                self.assertNotIn("MIDV_GL_MARGINFILL", env)

    def test_explicit_developer_patch_override_still_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            env = G.launch_overrides(ROOT, directory, "crusnusa", 86, 4,
                {"detail_distance_crusnusa": "1"}, {"MIDV_PATCH": "developer.txt"})
            self.assertNotIn("MIDV_PATCH", env)  # existing process environment is preserved

    def test_missing_selected_patch_fails_and_custom_conflicts_leave_old_file_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "Selected graphics experiment"):
                G.launch_overrides(directory, directory, "crusnusa", 86, 4,
                                   {"detail_distance_crusnusa": "1"}, {})
            env = G.launch_overrides(ROOT, directory, "crusnusa", 86, 4,
                                     {"detail_distance_crusnusa": "1"}, {})
            original = Path(env["MIDV_PATCH"]).read_bytes()
            conflict = Path(directory) / "custom.txt"
            conflict.write_text("000BF 04E21F40 00000000\n")
            with self.assertRaisesRegex(ValueError, "conflicting"):
                G.launch_overrides(ROOT, directory, "crusnusa", 86, 4,
                    {"detail_distance_crusnusa": "1", "gamepatch_crusnusa": str(conflict)}, {})
            self.assertEqual(Path(env["MIDV_PATCH"]).read_bytes(), original)


@unittest.skipUnless(sys.platform == "win32", "launcher uses Windows APIs")
class LauncherGraphicsTests(unittest.TestCase):
    def test_attended_recorder_preserves_shell_settings_and_requires_ffb_opt_in(self):
        record_drive = import_shell_module("record_drive")
        state = {"world_rom": "crusnwld24", "scale": 4, "crt": False,
                 "crackfill": True, "margin": 86, "ffb": 80,
                 "steersens": {"crusnwld": 90}, "steercurve": {"crusnwld": 120}}
        recording = types.SimpleNamespace(finish=mock.Mock(), manifest={"status": "recorded"})
        proc = types.SimpleNamespace(poll=lambda: 0, recording=recording)
        with tempfile.TemporaryDirectory() as directory:
            for attended, far in ((False, None), (True, None), (False, 160000)):
                args = ["--game", "world", "--no-clock", "--output", str(Path(directory) / "drive")]
                if attended:
                    args += ["--with-ffb"]
                if far:
                    args += ['--world-far',str(far),'--world-lead','8']
                with mock.patch.object(record_drive.collection, "load_config", return_value=state), \
                        mock.patch.object(record_drive.run_rig, "resolve_world_rom", return_value=("crusnwld24", None)), \
                        mock.patch.object(record_drive.run_rig, "launch_game_async", return_value=(proc, 0)) as launch, \
                        mock.patch.object(record_drive.run_rig, "wait_or_kill", return_value=0):
                    self.assertEqual(record_drive.main(args), 0)
                applied = launch.call_args.kwargs
                self.assertEqual(applied["rom"], "crusnwld24")
                self.assertEqual(applied["steersens"], 90)
                self.assertEqual(applied["steercurve"], 120)
                self.assertEqual(applied["margin"], 86)
                self.assertEqual(applied["ffb"], 80 if attended else 0)
                self.assertEqual(applied["record_with_ffb"], attended)
                self.assertEqual(applied['record_world_trial'],
                                 dict(far=160000,lead=8,cpu=100) if far else None)

    def test_real_shell_save_preserves_bindings_and_retires_marginfill(self):
        # Configuration/UI data needs no OpenGL context in hardware-free CI.
        collection = import_shell_module("collection")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "collection.ini"
            path.write_text("[collection]\nmarginfill=1\ncustom_note=keep\n"
                            "[wheelmap]\nsteer=wheel|axis:0:0:pos\n")
            with mock.patch.object(collection, "CFG", str(path)):
                state = collection.load_config()
                G.toggle(state["graphics"], "offroadc", "seam_alignment")
                G.toggle(state["graphics"], "crusnusa", "far_distance")
                state["ffbimpacts"]["crusnwld"] = True
                collection.save_config(state)
                restored = collection.load_config()
            self.assertEqual(restored["graphics"], state["graphics"])
            self.assertEqual(restored["ffbimpacts"], state["ffbimpacts"])
            cp = configparser.ConfigParser(); cp.read(path)
            self.assertEqual(cp["collection"]["ffb_impact_crusnwld24"], "1")
            self.assertEqual(cp["collection"]["ffb_impact_offroadc"], "0")
            self.assertEqual(cp["collection"]["marginfill"], "0")
            self.assertEqual(cp["collection"]["custom_note"], "keep")
            self.assertEqual(cp["wheelmap"]["steer"], "wheel|axis:0:0:pos")
            rows = collection.settings_rows("display", restored, False, "")
            self.assertNotIn("marginfill", [r[0] for r in rows])
            self.assertNotIn("crackfill", [r[0] for r in rows])
            self.assertIn("graphics", [r[0] for r in rows])
            restored["graphics_rom"] = "offroadc"
            rows = {r[0]: r[2] for r in collection.settings_rows("graphics", restored, False, "")}
            self.assertEqual(rows["seam_alignment"], "ON")
            self.assertEqual(set(rows), {'graphics_game','seam_alignment','back'})
            restored['graphics_rom'] = 'shared'
            shared = {r[0]:r[2] for r in collection.settings_rows('graphics',restored,False,'')}
            self.assertEqual(set(shared), {'graphics_game','crackfill','back'})
            self.assertEqual(shared['crackfill'], 'ON')
            restored['graphics_rom'] = 'crusnwld'
            restored['world_rom'] = 'crusnwld24'
            world = {r[0] for r in collection.settings_rows('graphics',restored,False,'')}
            self.assertIn('world_distance',world)
            self.assertNotIn('far_distance',world)
            restored['world_rom'] = 'crusnwld'
            world25 = {r[0] for r in collection.settings_rows('graphics',restored,False,'')}
            self.assertNotIn('world_distance',world25)
            restored['graphics_rom'] = 'crusnexo'
            exotica = collection.settings_rows('graphics',restored,False,'')
            self.assertEqual([r[0] for r in exotica], ['graphics_game','back'])
            self.assertIn('NO GRAPHICS EXPERIMENTS',exotica[0][3])
            self.assertTrue(restored['crackfill'])
