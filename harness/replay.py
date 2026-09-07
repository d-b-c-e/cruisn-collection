"""Replay a recorded driving case with physical outputs disabled.

Uses the same executable by default. --candidate explicitly permits a changed
binary for experiments; that report is a regression comparison, not an identity
replay. Every run keeps its input/time comparison, frame timings and snapshots.
"""
import argparse
import json
import re
from pathlib import Path
import subprocess
import sys
import shutil

from diagnostic_runtime import execute, new_run, ROOT
from raw_snapshots import convert_raw_snapshots
from game_patch import read_patch, verify_patch_ram, late_patch_lua
from run_capture import ARTIFACTS
from session_case import compare_evidence, prepare_run, session_evidence, tree_hashes, set_option
from verification import sha256_file, write_json, required_files
from session_clock import SessionClock, position


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--output", help="new evidence directory (must not exist)")
    ap.add_argument("--headless", action="store_true", help="native snapshots, no GL presentation")
    ap.add_argument("--small-window", action="store_true", help="disable window maximization for cheaper dense GL captures")
    ap.add_argument("--clock", action="store_true", help="show external emulation time and frame; uses current diagnostic script")
    ap.add_argument("--clock-position", type=position, default=(12, 12), help="X:Y in screen pixels")
    ap.add_argument("--candidate", type=Path, help="explicit candidate executable for regression experiments")
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--gl-capture", help="capture live V-Unit GL backbuffers over FIRST:LAST stream frames")
    ap.add_argument("--gl-every", type=int, default=150, help="present interval between GL captures")
    ap.add_argument("--gl-max", type=int, default=120, help="maximum GL BMPs retained")
    ap.add_argument("--gl-log", action="store_true", help="enable live renderer diagnostic log")
    ap.add_argument("--gl-stall", help="explicit consumer stall FRAME:MILLISECONDS, for recovery tests")
    ap.add_argument("--gl-queue-mb", type=int, help="explicit stream capacity experiment, 16..128 MiB")
    ap.add_argument("--gl-scale", type=int, help="explicit internal-scale experiment, 1..6")
    ap.add_argument("--no-crackfill", action="store_true", help="explicit experiment with crack filling disabled")
    ap.add_argument("--no-marginfill", action="store_true", help="disable backdrop suppression and boundary-column extension")
    ap.add_argument("--no-ui-assets", action="store_true", help="control experiment without enhanced World transmission atlas retention")
    ap.add_argument("--align-tjunctions", action="store_true", help="explicit quality-only geometry join experiment")
    ap.add_argument("--compare-gl", action="store_true", help="require identical completed GL pixels against the recorded case")
    ap.add_argument("--zeus-native", action="store_true", help="explicit Zeus diagnostic: also rasterize native CPU frames")
    ap.add_argument("--zeus-stop-frame", type=int, help="diagnostic Zeus consumer failure at this completed frame")
    ap.add_argument("--video", choices=("gdi", "d3d", "bgfx"), help="explicit underlying MAME video-backend experiment")
    ap.add_argument("--native-renderer", action="store_true", help="windowed control with replacement GL disabled")
    ap.add_argument("--snapshot-mode", choices=("png", "raw"), help="explicit capture experiment; raw defers PNG encoding until exit")
    ap.add_argument("--until-frame", type=int, help="explicit prefix replay ending at this frame")
    ap.add_argument("--capture-state", action="store_true", help="capture quads/RAM two frames before --until-frame")
    ap.add_argument("--patch", type=Path, help="explicit game-code patch experiment; replaces the recorded patch")
    ap.add_argument("--probe-script", type=Path, help="explicit Lua frame callback for a bounded diagnostic experiment")
    ap.add_argument("--numeric-speed", action="store_true", help="explicit USA numeric HUD telemetry experiment")
    ap.add_argument("--scenery", choices=("off", "mountains", "trees", "all"),
                    help="explicit native World 2.4 scenery-distance candidate; logs admissions/projection")
    ap.add_argument("--patch-at-frame", type=int, help="apply the checked patch late, preserving earlier game history")
    args = ap.parse_args(argv)
    if args.timeout <= 0:
        ap.error("timeout must be positive")
    if args.headless and args.small_window:
        ap.error("--small-window requires visible replay")
    if args.gl_every < 1 or args.gl_max < 1 or (args.gl_scale is not None and not 1 <= args.gl_scale <= 6):
        ap.error("GL intervals/budget must be positive and scale must be 1..6")
    gl_experiment = args.gl_capture or args.gl_log or args.gl_scale is not None or args.no_crackfill or args.no_marginfill or args.no_ui_assets or args.align_tjunctions or args.gl_stall or args.gl_queue_mb or args.zeus_native or args.zeus_stop_frame is not None
    if args.headless and args.compare_gl:
        ap.error("GL pixel comparison requires live presentation")
    if args.headless and (gl_experiment or args.video or args.native_renderer):
        ap.error("live GL diagnostics cannot be combined with --headless")
    if args.native_renderer and gl_experiment:
        ap.error("native renderer control cannot enable GL diagnostics")
    if args.capture_state and (args.until_frame is None or args.until_frame < 3):
        ap.error("state capture requires --until-frame of at least 3")
    if args.patch_at_frame is not None and (not args.patch or args.probe_script):
        ap.error("--patch-at-frame requires --patch and cannot combine with --probe-script")
    try:
        work = new_run("replay", args.output)
    except OSError as exc:
        ap.error(str(exc))
    report = {"schema": 1, "kind": "candidate-regression" if args.candidate else "identity-replay",
              "case": str(args.case.resolve()), "passed": False,
              "presentation": "native-headless" if args.headless else "recorded-settings"}
    print(f"replay evidence: {work}")
    try:
        case = args.case.resolve()
        manifest = json.loads((case / "case.json").read_text(encoding="utf-8"))
        gl_key = "MIDZ" if manifest.get('rom') == 'crusnexo' else 'MIDV'
        if gl_key == 'MIDZ' and (args.gl_queue_mb or args.gl_stall or args.no_crackfill or args.no_marginfill or args.no_ui_assets or args.align_tjunctions):
            raise ValueError('requested renderer experiment is V-Unit-only')
        if (args.zeus_native or args.zeus_stop_frame is not None) and gl_key != 'MIDZ':
            raise ValueError('Zeus diagnostics require Exotica')
        if manifest.get("schema") != 1 or manifest.get("status") != "recorded":
            raise ValueError("case is not a completed schema-1 recording")
        if tree_hashes(case / "initial") != manifest["initial_hashes"]:
            raise ValueError("initial configuration has changed since recording")
        if sha256_file(case / "record" / "input" / "session.inp") != manifest["inp_sha256"]:
            raise ValueError("input recording has changed")
        for name, digest in manifest["dependencies"].items():
            if sha256_file(case / "binary" / name) != digest:
                raise ValueError(f"archived binary dependency has changed: {name}")
        for path, digest in manifest["rom_containers"].items():
            if sha256_file(path) != digest:
                raise ValueError(f"recording dependency has changed: {path}")
        reference = session_evidence(case / "record", manifest["every"], manifest["returncode"])
        if reference != manifest["evidence"]:
            raise ValueError("reference evidence has changed")
        if args.until_frame is not None:
            if not manifest["every"] <= args.until_frame <= reference["frames"]:
                raise ValueError("prefix must include a snapshot and end within the recording")
            reference = dict(reference, frames=args.until_frame,
                snapshots={n: v for n, v in reference["snapshots"].items() if int(n) <= args.until_frame})
            manifest["evidence"] = dict(manifest["evidence"], frames=args.until_frame)
            report["comparison_scope"] = {"first_frame": 1, "last_frame": args.until_frame,
                                          "kind": "explicit-prefix"}
        if args.patch_at_frame is not None and not 1 <= args.patch_at_frame < reference["frames"] - 2:
            raise ValueError("late patch must precede the final capture/stop frames")
        if gl_experiment:
            if manifest["settings"].get(gl_key+"_GL") != "1":
                raise ValueError("GL diagnostics require a recording made with this game's GL renderer")
            overrides = {}
            if args.gl_queue_mb is not None:
                if not 16 <= args.gl_queue_mb <= 128:
                    raise ValueError("GL stream capacity must be 16..128 MiB")
                overrides["MIDV_GL_QUEUE_MB"] = str(args.gl_queue_mb)
            if args.gl_stall:
                stall_frame, stall_ms = map(int, args.gl_stall.split(":"))
                if not 0 <= stall_frame < reference["frames"] or not 0 < stall_ms <= 5000:
                    raise ValueError("GL stall must lie within the recording and last 1..5000 ms")
                overrides.update(MIDV_GL_STALL_FRAME=str(stall_frame), MIDV_GL_STALL_MS=str(stall_ms), MIDV_GL_LOG="1")
            if args.gl_capture:
                first, last = map(int, args.gl_capture.split(":"))
                if not 0 <= first < last <= reference["frames"]:
                    raise ValueError("GL interval must be within the recorded frames")
                overrides.update({gl_key+'_GL_'+k:v for k,v in dict(SNAP='redirect-at-launch',
                    SNAP_FIRST=str(first),SNAP_LAST=str(last),SNAP_EVERY=str(args.gl_every),SNAP_MAX=str(args.gl_max)).items()})
            if args.gl_log:
                overrides[gl_key+"_GL_LOG"] = "1"
            if args.gl_scale is not None:
                overrides[gl_key+"_GL_SCALE"] = str(args.gl_scale)
            if args.zeus_native:
                overrides['MIDZ_GL_NATIVE'] = '1'
            if args.zeus_stop_frame is not None:
                if not 0 <= args.zeus_stop_frame < reference['frames']:
                    raise ValueError('consumer stop must lie within the recording')
                overrides.update(MIDZ_GL_STOP_FRAME=str(args.zeus_stop_frame), MIDZ_GL_LOG='1')
            if args.no_crackfill:
                overrides["MIDV_GL_CRACKFILL"] = "0"
            if args.no_marginfill:
                overrides["MIDV_GL_MARGINFILL"] = "0"
            if args.no_ui_assets:
                overrides["MIDV_GL_UI_ASSETS"] = "0"
            if args.align_tjunctions:
                overrides["MIDV_GL_TJUNCTIONS"] = "1"
                overrides["MIDV_GL_LOG"] = "1"
            manifest["settings"].update(overrides)
            report["presentation_overrides"] = overrides
            report["presentation"] = "explicit-gl-experiment"
        if args.candidate:
            manifest["command"][0] = str(args.candidate.resolve())
        if args.scenery is not None:
            manifest["settings"].update(MIDV_SCENERY=args.scenery, MIDV_SCENERY_LOG="1")
            report["scenery_override"] = args.scenery
        if args.snapshot_mode:
            manifest["snapshot_mode"] = args.snapshot_mode
            report["snapshot_mode_override"] = args.snapshot_mode
        runtime = work / "run"
        command, env = prepare_run(case, manifest, runtime, playback=True, headless=args.headless)
        if args.small_window:
            command += ["-window", "-nomaximize"]
            report["window_override"] = "unmaximized; actual dimensions are recorded in captures.csv"
        if args.numeric_speed:
            env["MIDV_SPEED_NUMERIC"] = "1"
            report["numeric_speed_experiment"] = True
        if args.snapshot_mode or args.probe_script or args.patch_at_frame is not None or args.clock:
            shutil.copy2(ROOT / "lua" / "session.lua", runtime / "session.lua")
            report["diagnostic_script_sha256"] = sha256_file(runtime / "session.lua")
        if args.clock:
            env["SNAP_CLOCK_EVERY"] = "6"
            report["external_clock"] = {"flush_frames": 6, "position": args.clock_position,
                                        "time_source": "frames.csv emulated_seconds"}
        if args.probe_script:
            probe_file = runtime / "probe.lua"
            shutil.copy2(args.probe_script, probe_file)
            env["SNAP_PROBE_SCRIPT"] = str(probe_file)
            report["probe_script"] = {"source": str(args.probe_script.resolve()),
                                      "sha256": sha256_file(probe_file),
                # Literal CRUISN_* inputs used by our diagnostic probes. None
                # means the archived script's default, not an inherited value.
                "environment": {key: env.get(key) for key in sorted(set(re.findall(
                    r"os\.getenv\(\s*['\"](CRUISN_[A-Z0-9_]+)['\"]",
                    probe_file.read_text(encoding="utf-8"))))}}
        if args.video:
            command = set_option(command, "-video", args.video)
            report["video_override"] = args.video
        if args.native_renderer:
            for key in ("MIDV_GL", "MIDV_LIVE", "MIDZ_GL"):
                env.pop(key, None)
            report["presentation"] = "native-window-control"
            command += ["-keepaspect"]
        if args.capture_state:
            capture = runtime / "capture"
            capture.mkdir()
            env.update(MIDV_QUADLOG=str(capture / "quads.bin"),
                       MIDV_STATEDUMP_FRAME=str(args.until_frame - 2), MIDV_STATEDUMP_DIR=str(capture))
        if args.patch:
            patch_entries = read_patch(args.patch)
            patch_file = runtime / "experiment-patch.txt"
            shutil.copy2(args.patch, patch_file)
            if args.patch_at_frame is None:
                env["MIDV_PATCH"] = str(patch_file)
            else:
                probe_file = runtime / "late-patch.lua"
                probe_file.write_text(late_patch_lua(patch_entries, args.patch_at_frame), encoding="utf-8")
                env["SNAP_PROBE_SCRIPT"] = str(probe_file)
                report["late_patch"] = {"frame": args.patch_at_frame, "script_sha256": sha256_file(probe_file)}
            env["MIDV_GL_LOG"] = "1"
            if args.capture_state:
                env["MIDV_RAMDUMP_DIR"] = str(capture)
                env["MIDV_RAMDUMP_EVERY"] = str(args.until_frame - 2)
            report["game_patch_override"] = {"source": str(args.patch.resolve()),
                                              "sha256": sha256_file(patch_file)}
            report["kind"] = "game-patch-regression"
        clock = SessionClock(runtime, "Replay: " + manifest.get("title", manifest["rom"]), args.clock_position)
        if args.clock:
            clock.start()
        try:
            invocation = execute(command, runtime, env, args.timeout)
        finally:
            clock.close()
        # Recording uses the product launch log; normalize the replay's stdout
        # path so the same strict evidence validator serves both paths.
        if (runtime / "stdout.log").exists():
            (runtime / "launch.log").write_bytes((runtime / "stdout.log").read_bytes())
        if invocation["error"]:
            raise ValueError(invocation["error"])
        if args.patch_at_frame is not None:
            receipt = f"session.lua: game patch {len(patch_entries)} words at frame {args.patch_at_frame}"
            if receipt not in (runtime / "launch.log").read_text(encoding="utf-8", errors="replace"):
                raise ValueError("late game patch application receipt missing")
        convert_raw_snapshots(runtime)
        report["evidence"] = session_evidence(runtime, manifest["every"], invocation["returncode"],
            require_gl=not (args.headless or args.native_renderer) and bool(manifest["settings"].get(gl_key+"_GL_SNAP")))
        if args.gl_capture and report["evidence"].get("gl_captures", {}).get("completed_frames"):
            from gl_frames import read_completed_frames
            expected = [n for n in range(first, last + 1) if n % args.gl_every == 0]
            if len(expected) > args.gl_max:
                raise ValueError("GL capture budget cannot cover the requested interval")
            read_completed_frames(runtime / "gl-snap", expected)
        report["comparison"] = compare_evidence(case / "record", runtime, reference, report["evidence"])
        report["passed"] = report["comparison"]["passed"]
        if gl_key == 'MIDZ' and not (args.headless or args.native_renderer or args.zeus_native or manifest['settings'].get('MIDZ_GL_NATIVE') == '1'):
            report['native_image_scope'] = 'CPU polygon rasterization disabled by Zeus GL; native images cannot validate visible gameplay'
        if args.compare_gl:
            from gl_frames import compare_completed_frames
            report['gl_comparison'] = compare_completed_frames(case/'record'/'gl-snap',runtime/'gl-snap')
            report['passed'] = report['passed'] and report['gl_comparison']['passed']
        if args.capture_state:
            required_files(capture, ARTIFACTS)
            report["capture"] = {"directory": str(capture), "requested_dump_frame": args.until_frame - 2,
                                 "sha256": {n: sha256_file(capture / n) for n in ARTIFACTS}}
            if args.patch:
                program_ram = capture / f"ram_{args.until_frame - 2:06d}.bin"
                report["effective_patch"] = verify_patch_ram(program_ram, patch_entries)
                report["capture"]["sha256"][program_ram.name] = sha256_file(program_ram)
                report["passed"] = report["passed"] and report["effective_patch"]["passed"]
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        report["passed"] = False
        report["error"] = str(exc)
    write_json(work / "report.json", report)
    print(("PASS" if report["passed"] else "FAIL") + f": {work / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
