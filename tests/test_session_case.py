import csv
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from session_case import compare_evidence, read_trace, session_evidence, prepare_run


class SessionTests(unittest.TestCase):
    def test_global_recording_archives_patch_before_temporary_source_disappears(self):
        from session_case import Recording
        from world_distance import compose
        from game_patch import read_patch
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            exe = root/'vunit.exe'; exe.write_bytes(b'fixture executable, never launched')
            roms = root/'roms'; roms.mkdir()
            (roms/'crusnwld24.zip').write_bytes(b'container fingerprint fixture')
            rig = root/'rig'; rig.mkdir()
            base = root/'base.txt'; base.write_text('247 0C800000 08620056\n')
            recording = Recording(root/'case')
            with tempfile.TemporaryDirectory() as patch_directory:
                patch = compose(base,Path(patch_directory)/'global.txt',160000)
                settings = {'MIDV_PATCH':str(patch), 'MIDV_WORLD_FAR':'160000',
                            'MIDV_WORLD_LEAD':'8', 'MIDV_WORLD_CPU_PERCENT':'100', 'MIDV_FFB':'1'}
                with mock.patch('session_case.subprocess.check_output',
                                return_value=b'<mame><machine name="crusnwld24"/></mame>'), \
                     mock.patch('session_case.git_identity', return_value={'commit':'fixture'}):
                    _,env,runtime = recording.prepare(
                        [str(exe),'crusnwld24','-rompath',str(roms)],settings,rig)
            self.assertFalse(patch.exists())
            self.assertEqual(read_patch(env['MIDV_PATCH'])[0x40], (80000,160000))
            self.assertEqual(read_patch(env['MIDV_PATCH'])[0x247], (0x0c800000,0x08620056))
            self.assertEqual(recording.manifest['settings']['MIDV_PATCH'],'@initial/game-patch.txt')
            self.assertEqual(recording.manifest['settings']['MIDV_WORLD_LEAD'],'8')
            self.assertEqual(env['MIDV_FFB'],'0')

    def test_attended_recording_cannot_enable_replay_actuators(self):
        from diagnostic_runtime import execute
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "case"
            (case / "initial").mkdir(parents=True)
            (case / "record" / "input").mkdir(parents=True)
            (case / "record" / "input" / "session.inp").write_bytes(b"fixture")
            manifest = dict(command=["vunit.exe", "crusnusa"], settings={"MIDV_FFB": "1", "MIDV_FFB_TEST": "50"},
                            every=60, stop_frame=120, evidence={"frames":120}, attended_ffb=True, origin="live-input")
            _, replay_env = prepare_run(case, manifest, Path(td) / "replay", playback=True)
            self.assertEqual(replay_env["MIDV_FFB"], "0")
            self.assertNotIn("MIDV_FFB_TEST", replay_env)
            _, record_env = prepare_run(case, manifest, Path(td) / "record", playback=False)
            self.assertEqual(record_env["MIDV_FFB"], "1")
            self.assertNotIn("MIDV_FFB_TEST", record_env)
            with self.assertRaisesRegex(ValueError, "force disabled"):
                execute(["never-launched"], Path(td), record_env, 1)

    def case(self, directory, wheel=128, color="black", count=3):
        directory.mkdir()
        (directory / "snap").mkdir()
        with open(directory / "frames.csv", "w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["frame", "emulated_seconds", "host_seconds", "speed_percent", ":WHEEL"])
            for n in range(1, count + 1):
                writer.writerow([n, n / 60, n / 50, 1, wheel if n == 2 else 128])
                Image.new("RGB", (3, 2), color).save(directory / "snap" / f"frame_{n:08d}.png")
        (directory / "launch.log").write_text("\n".join(
            [f"session.lua: snapshot at frame {n}" for n in range(1, count + 1)] +
            [f"session.lua: stopped at frame {count}"]))
        return session_evidence(directory, 1, 0)

    def test_input_and_pixel_changes_are_independently_reported(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            ea = self.case(a)
            eb = self.case(b, wheel=140, color="red")
            report = compare_evidence(a, b, ea, eb)
            self.assertFalse(report["passed"])
            self.assertEqual(report["first_input_mismatches"], [2])
            self.assertEqual(report["pixel_mismatches"], 3)
            self.assertEqual(eb["input_coverage"][":WHEEL"]["distinct"], 2)

    def test_lua_errors_cannot_pass_with_clean_exit_and_valid_images(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            for marker in ("session.lua: probe failed: bad pointer", "[LUA ERROR] tap failed",
                           "session.lua: snapshot failed: write failed"):
                with self.subTest(marker=marker):
                    (a / "stderr.log").write_text(marker)
                    with self.assertRaisesRegex(ValueError, "Lua diagnostic"):
                        session_evidence(a, 1, 0)

    def test_truncated_replay_does_not_pass_against_longer_recording(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            ea, eb = self.case(a), self.case(b, count=2)
            with self.assertRaisesRegex(ValueError, "frame count"):
                compare_evidence(a, b, ea, eb)

    def test_explicit_prefix_still_checks_inputs_and_pixels(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            ea, eb = self.case(a), self.case(b, wheel=150, count=2)
            prefix = dict(ea, frames=2, snapshots={n: v for n, v in ea["snapshots"].items() if int(n) <= 2})
            self.assertFalse(compare_evidence(a, b, prefix, eb)["passed"])

    def test_raw_snapshot_manifest_cannot_be_truncated(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            (a / "raw-snap").mkdir()
            with self.assertRaisesRegex(ValueError, "raw snapshot manifest"):
                session_evidence(a, 1, 0)

    def test_stop_receipt_and_extra_images_are_required_checks(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            Image.new("RGB", (3, 2)).save(a / "snap" / "extra.png")
            with self.assertRaisesRegex(ValueError, "manifest"):
                session_evidence(a, 1, 0)
            (a / "launch.log").write_text("")
            with self.assertRaisesRegex(ValueError, "receipt"):
                session_evidence(a, 1, 0)

    def test_repeated_emulated_time_is_not_an_emulated_frame(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            p = a / "frames.csv"
            p.write_text(p.read_text().replace("0.03333333333333333", "0.016666666666666666"))
            with self.assertRaisesRegex(ValueError, "strictly increasing"):
                read_trace(p)

    def test_requested_gl_capture_cannot_pass_without_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            self.case(a)
            with self.assertRaises(OSError):
                session_evidence(a, 1, 0, require_gl=True)
            (a / "gl-snap").mkdir()
            (a / "gl-snap" / "captures.csv").write_text("file,dropped_messages\n")
            with self.assertRaisesRegex(ValueError, "empty"):
                session_evidence(a, 1, 0, require_gl=True)
