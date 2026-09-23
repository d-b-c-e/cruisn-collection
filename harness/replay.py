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

from diagnostic_runtime import execute, execution_failure, new_run, ROOT
from raw_snapshots import convert_raw_snapshots
from game_patch import read_patch, verify_patch_ram, late_patch_lua
from run_capture import ARTIFACTS
from session_case import compare_evidence, prepare_run, session_evidence, tree_hashes, set_option
from verification import sha256_file, write_json, required_files
from session_clock import SessionClock, position
from gl_frames import requested_frames, read_completed_frames, IncompleteCaptureError, completion_drain_target
import world_distance
import usa_distance
import exotica_visibility
import exotica_scene_options
import exotica_lifetimes
import exotica_shutdown
import exotica_runtime
import exotica_waiting
import exotica_handover
import exotica_model_endpoint
import ffb_worker
import zeus_render_policy
import zeus_palette
import zeus_margin_clear
import zeus_sky_options
import zeus_depth_mirror
import zeus_stream
import offroad_distance
import world_host_options
import vunit_original_mirror
import vunit_host_failure
import vunit_bootstrap
import vunit_runtime
import exotica_host_failure
import exotica_journals
import exotica_timing
import exotica_bootstrap
import exotica_reset
import binary_provenance
import usa_host_options
import offroad_host_options
import scenery_presets
from display_target import parse_size


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    exotica_timing.add_arguments(ap)
    ap.add_argument("case", type=Path)
    ap.add_argument("--output", help="new evidence directory (must not exist)")
    ap.add_argument('--prepare-only',action='store_true',
        help='validate dependencies/options and save an isolated launch plan; do not start MAME or report a replay pass')
    ap.add_argument('--no-inherited-gl-captures',action='store_true',
        help='clear the recorded GL screenshot schedule; explicit --gl-capture still applies')
    ap.add_argument("--headless", action="store_true", help="native snapshots, no GL presentation")
    ap.add_argument("--small-window", action="store_true", help="disable window maximization for cheaper dense GL captures")
    ap.add_argument('--display-size',type=parse_size,help='select an actual WIDTH:HEIGHT display and maximize; captured client pixels may exclude borders')
    ap.add_argument('--display-watch',action='store_true',
                    help='opt-in monitor-topology polling during replay; fail if it changes or cannot be observed')
    ap.add_argument('--zeus-merged-panel',action='store_true',
                    help='explicit Exotica diagnostic: center the requested panel within an exact triple-wide merged display')
    ap.add_argument("--clock", action="store_true", help="show external emulation time and frame; uses current diagnostic script")
    ap.add_argument("--clock-position", type=position, default=(12, 12), help="X:Y in screen pixels")
    ap.add_argument("--candidate", type=Path, help="explicit candidate executable for regression experiments")
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--gl-capture", help="capture live V-Unit GL backbuffers over FIRST:LAST stream frames")
    ap.add_argument("--gl-every", type=int, default=150, help="present interval between GL captures")
    ap.add_argument("--gl-max", type=int, default=120, help="maximum GL BMPs retained")
    ap.add_argument("--gl-log", action="store_true", help="enable live renderer diagnostic log")
    ap.add_argument("--gl-stall", help="explicit consumer stall FRAME:MILLISECONDS, for recovery tests")
    ap.add_argument("--gl-capture-pacing", action="store_true", help="explicit offline wait for bounded screenshot storage; requires candidate and capture range")
    ap.add_argument("--gl-queue-mb", type=int, help="explicit stream capacity experiment, 16..128 MiB")
    ap.add_argument("--zeus-queue-mb", type=int, choices=(128,),
                    help="Exotica diagnostic: use a 128 MiB graphics ring instead of the default 64 MiB")
    ap.add_argument("--gl-scale", type=int, help="explicit internal-scale experiment, 1..6")
    ap.add_argument("--gl-crt", choices=('on','off'), help="explicit CRT override for completed-frame testing")
    ap.add_argument("--gl-height", type=int, choices=(400,401), help="explicit V-Unit native-height override; preserve old recordings")
    ap.add_argument("--no-crackfill", action="store_true", help="explicit experiment with crack filling disabled")
    ap.add_argument("--no-marginfill", action="store_true", help="disable backdrop suppression and boundary-column extension")
    ap.add_argument("--no-ui-assets", action="store_true", help="control experiment without enhanced World transmission atlas retention")
    ap.add_argument("--no-vram-batching", action="store_true", help="V-Unit control: upload each CPU framebuffer span immediately")
    ap.add_argument("--align-tjunctions", action="store_true", help="explicit quality-only geometry join experiment")
    ap.add_argument("--compare-gl", action="store_true", help="require identical completed GL pixels against the recorded case")
    ap.add_argument("--zeus-native", action="store_true", help="explicit Zeus diagnostic: also rasterize native CPU frames")
    ap.add_argument('--zeus-capture-frame',type=int,help='capture Zeus submission/resource records around one emulated frame')
    ap.add_argument('--zeus-capture-models',action='store_true',help='also capture bounded original Zeus model operands/state; raw data stays local')
    ap.add_argument("--zeus-stop-frame", type=int, help="diagnostic Zeus consumer failure at this completed frame")
    ap.add_argument("--video", choices=("gdi", "d3d", "bgfx"), help="explicit underlying MAME video-backend experiment")
    ap.add_argument("--native-renderer", action="store_true", help="windowed control with replacement GL disabled")
    ap.add_argument("--snapshot-mode", choices=("png", "raw"), help="explicit capture experiment; raw defers PNG encoding until exit")
    ap.add_argument("--until-frame", type=int, help="explicit prefix replay ending at this frame")
    ap.add_argument("--capture-state", action="store_true", help="capture quads/RAM two frames before --until-frame")
    ap.add_argument("--patch", type=Path, help="explicit game-code patch experiment; replaces the recorded patch")
    ap.add_argument("--probe-script", type=Path, help="explicit Lua frame callback for a bounded diagnostic experiment")
    ap.add_argument("--numeric-speed", action="store_true", help="explicit USA numeric HUD telemetry experiment")
    ap.add_argument("--telemetry-loopback", action="store_true", help="capture actual Forza/JSON packets on private localhost ports; no external outputs")
    ap.add_argument("--no-arcade-rpm", action="store_true", help="control: disable the estimated RPM scale while retaining game gear")
    ap.add_argument("--scenery", choices=("off", "mountains", "trees", "all"),
                    help="explicit native World 2.4 scenery-distance candidate; logs admissions/projection")
    ap.add_argument('--scenery-lead', type=int, choices=range(9),
                    help='native background activation lead in track sections; 0 disables earlier activation')
    ap.add_argument("--patch-at-frame", type=int, help="apply the checked patch late, preserving earlier game history")
    world_distance.add_arguments(ap)
    usa_distance.add_arguments(ap)
    exotica_visibility.add_arguments(ap)
    exotica_scene_options.add_arguments(ap)
    exotica_lifetimes.add_arguments(ap)
    exotica_waiting.add_arguments(ap)
    exotica_handover.add_arguments(ap)
    exotica_model_endpoint.add_arguments(ap)
    ffb_worker.add_arguments(ap)
    zeus_render_policy.add_arguments(ap)
    zeus_palette.add_arguments(ap)
    zeus_margin_clear.add_arguments(ap)
    zeus_sky_options.add_arguments(ap)
    zeus_depth_mirror.add_arguments(ap)
    offroad_distance.add_arguments(ap)
    world_host_options.add_arguments(ap)
    vunit_original_mirror.add_arguments(ap)
    vunit_host_failure.add_arguments(ap)
    vunit_bootstrap.add_arguments(ap)
    vunit_runtime.add_arguments(ap)
    exotica_host_failure.add_arguments(ap)
    exotica_journals.add_arguments(ap)
    exotica_bootstrap.add_arguments(ap)
    exotica_shutdown.add_arguments(ap)
    exotica_runtime.add_arguments(ap)
    usa_host_options.add_arguments(ap)
    offroad_host_options.add_arguments(ap)
    scenery_presets.add_arguments(ap)
    args = ap.parse_args(argv)
    preset_trial = None
    if args.scenery_preset:
        if not args.candidate or args.headless or args.native_renderer:
            ap.error('scenery preset requires an explicit live-GL candidate')
        try:
            preset_manifest=json.loads((args.case/'case.json').read_text(encoding='utf-8'))
            expanded,preset_trial=scenery_presets.expand(list(sys.argv[1:] if argv is None else argv),preset_manifest['rom'])
            args=ap.parse_args(expanded)
        except (OSError,ValueError,KeyError) as exc:
            ap.error(str(exc))
    if args.zeus_capture_models and args.zeus_capture_frame is None:
        ap.error('--zeus-capture-models requires --zeus-capture-frame')
    if args.timeout <= 0:
        ap.error("timeout must be positive")
    if args.headless and args.small_window:
        ap.error("--small-window requires visible replay")
    if args.display_size and (args.headless or args.small_window or args.compare_gl):
        ap.error('--display-size requires visible replay without --small-window or --compare-gl')
    if args.gl_every < 1 or args.gl_max < 1 or (args.gl_scale is not None and not 1 <= args.gl_scale <= 6):
        ap.error("GL intervals/budget must be positive and scale must be 1..6")
    gl_experiment = args.gl_capture or args.gl_log or args.gl_scale is not None or args.gl_crt is not None or args.gl_height is not None or args.no_crackfill or args.no_marginfill or args.no_ui_assets or args.no_vram_batching or args.align_tjunctions or args.gl_stall or args.gl_queue_mb or args.zeus_queue_mb or args.zeus_native or args.zeus_stop_frame is not None
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
    if preset_trial:report['scenery_preset']=preset_trial
    print(f"replay evidence: {work}")
    try:
        case = args.case.resolve()
        manifest = json.loads((case / "case.json").read_text(encoding="utf-8"))
        gl_key = "MIDZ" if manifest.get('rom') == 'crusnexo' else 'MIDV'
        if args.gl_capture_pacing and (not args.candidate or not args.gl_capture or args.headless or args.native_renderer):
            raise ValueError('screenshot pacing requires a candidate, live GL and explicit capture range')
        if gl_key == 'MIDZ' and (args.gl_queue_mb or args.no_crackfill or args.no_marginfill or args.no_ui_assets or args.align_tjunctions):
            raise ValueError('requested renderer experiment is V-Unit-only')
        if args.zeus_merged_panel and (gl_key != 'MIDZ' or not args.display_size or not args.candidate):
            raise ValueError('merged Zeus panel requires Exotica, an explicit display size and candidate')
        if args.zeus_queue_mb and gl_key != 'MIDZ':
            raise ValueError('Zeus queue capacity experiment requires Exotica')
        if (args.zeus_native or args.zeus_stop_frame is not None) and gl_key != 'MIDZ':
            raise ValueError('Zeus diagnostics require Exotica')
        if args.capture_state and gl_key=='MIDZ':
            raise ValueError('V-Unit state capture does not cover Zeus; use --zeus-capture-frame')
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
        if args.no_inherited_gl_captures:
            removed={k:v for k,v in manifest['settings'].items()
                     if k.startswith(('MIDV_GL_SNAP','MIDZ_GL_SNAP'))}
            for key in removed:del manifest['settings'][key]
            report['removed_inherited_gl_captures']=removed
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
        if args.zeus_capture_frame is not None and (gl_key!='MIDZ' or not 2<=args.zeus_capture_frame<reference['frames']-1):
            raise ValueError('Zeus capture requires Exotica and a frame before the replay drain interval')
        if gl_experiment:
            if manifest["settings"].get(gl_key+"_GL") != "1":
                raise ValueError("GL diagnostics require a recording made with this game's GL renderer")
            overrides = {}
            if args.gl_queue_mb is not None:
                if not 16 <= args.gl_queue_mb <= 128:
                    raise ValueError("GL stream capacity must be 16..128 MiB")
                overrides["MIDV_GL_QUEUE_MB"] = str(args.gl_queue_mb)
            if args.zeus_queue_mb:
                overrides['MIDZ_GL_QUEUE_MB'] = str(args.zeus_queue_mb)
                overrides['MIDZ_GL_LOG'] = '1'
                report['zeus_queue_mb'] = args.zeus_queue_mb
            if args.gl_stall:
                stall_frame, stall_ms = map(int, args.gl_stall.split(":"))
                if not 0 <= stall_frame < reference["frames"] or not 0 < stall_ms <= 5000:
                    raise ValueError("GL stall must lie within the recording and last 1..5000 ms")
                overrides.update({gl_key+'_GL_STALL_FRAME':str(stall_frame),
                                  gl_key+'_GL_STALL_MS':str(stall_ms), gl_key+'_GL_LOG':'1'})
            if args.gl_capture:
                first, last = map(int, args.gl_capture.split(":"))
                if not 0 <= first <= last <= reference["frames"]:
                    raise ValueError("GL interval must be within the recorded frames")
                expected_gl = requested_frames(first, last, args.gl_every, args.gl_max,
                    stop_frame=reference['frames'] if gl_key=='MIDZ' else None)
                overrides.update({gl_key+'_GL_'+k:v for k,v in dict(SNAP='redirect-at-launch',
                    SNAP_FIRST=str(first),SNAP_LAST=str(last),SNAP_EVERY=str(args.gl_every),SNAP_MAX=str(args.gl_max)).items()})
                if args.gl_capture_pacing:
                    overrides[gl_key+'_CAPTURE_PACE'] = '1'
            if args.gl_log:
                overrides[gl_key+"_GL_LOG"] = "1"
            if args.gl_scale is not None:
                overrides[gl_key+"_GL_SCALE"] = str(args.gl_scale)
            if args.gl_crt is not None:
                overrides[gl_key+'_GL_CRT'] = '1' if args.gl_crt == 'on' else '0'
            if args.gl_height is not None:
                if gl_key != 'MIDV':raise ValueError('native-height override applies to V-Unit only')
                overrides['MIDV_GL_HEIGHT'] = str(args.gl_height)
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
            if args.no_vram_batching:
                if manifest['rom'] == 'crusnexo':
                    raise ValueError('CPU VRAM batching control applies to V-Unit, not Zeus')
                overrides['MIDV_GL_BATCH_VRAM'] = '0'
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
        if args.scenery_lead is not None:
            manifest['settings'].update(MIDV_SCENERY_LEAD=str(args.scenery_lead), MIDV_SCENERY_LOG='1')
            report['scenery_activation_lead'] = args.scenery_lead
        if args.snapshot_mode:
            manifest["snapshot_mode"] = args.snapshot_mode
            report["snapshot_mode_override"] = args.snapshot_mode
        # Option gates must see the same disabled physical force that prepare_run
        # enforces for playback, including recordings made with attended FFB.
        manifest['settings']['MIDV_FFB'] = '0'
        trial = world_distance.configure(args, manifest['rom'], manifest['settings'])
        if trial:
            report['world_distance'] = trial
        usa_trial = usa_distance.configure(args, manifest['rom'], manifest['settings'])
        if usa_trial:
            report['usa_distance'] = usa_trial
        exo_trial = exotica_visibility.configure(args, manifest['rom'], manifest['settings'])
        if exo_trial:
            report['exotica_visibility'] = exo_trial
        zeus_trial=zeus_render_policy.configure(args,manifest['rom'],manifest['settings'])
        if zeus_trial:report['zeus_upstream']=zeus_trial
        palette_trial=zeus_palette.configure(args,manifest['rom'],manifest['settings'])
        if palette_trial:report['zeus_palette']=palette_trial
        margin_trial=zeus_margin_clear.configure(args,manifest['rom'],manifest['settings'])
        if margin_trial:report['zeus_margin_clear']=margin_trial
        sky_trial=zeus_sky_options.configure(args,manifest['rom'],manifest['settings'])
        if sky_trial:report['zeus_sky']=sky_trial
        scene_trial=exotica_scene_options.configure(args,manifest['rom'],manifest['settings'])
        if scene_trial:report['exotica_host_scene']=scene_trial
        timing_trial=exotica_timing.configure(args,manifest['rom'],manifest['settings'],reference['frames'])
        if timing_trial:report['exotica_timing']=timing_trial
        lifetime_trial=exotica_lifetimes.configure(args,manifest['rom'],manifest['settings'])
        if lifetime_trial:report['exotica_lifetimes']=lifetime_trial
        depth_trial=zeus_depth_mirror.configure(args,manifest['rom'],manifest['settings'],reference['frames'])
        if depth_trial:report['zeus_depth_mirror']=depth_trial
        exotica_scene_options.validate_runtime(scene_trial,args,manifest['settings'])
        waiting_trial=exotica_waiting.configure(args,manifest['rom'],manifest['settings'],scene_trial,lifetime_trial)
        if waiting_trial:report['exotica_waiting']=waiting_trial
        handover_trial=exotica_handover.configure(args,manifest['rom'],manifest['settings'],scene_trial,waiting_trial)
        if handover_trial:report['exotica_handover']=handover_trial
        endpoint_trial=exotica_model_endpoint.configure(args,manifest['rom'],manifest['settings'],lifetime_trial,scene_trial)
        if endpoint_trial:report['exotica_model_endpoint']=endpoint_trial
        if endpoint_trial and endpoint_trial.get('early')=='endpoint':
            scene_trial['early_visibility']={k:endpoint_trial[k] for k in ('first','last')}
            handover_trial['early_visibility']=dict(scene_trial['early_visibility'])
        if scene_trial and scene_trial.get('future_present'):
            report['presentation']='explicit-extended-target'
        stall_trial=zeus_stream.configure_stall(args,manifest['rom'],manifest['settings'],reference['frames'])
        if stall_trial:report['zeus_stall']=stall_trial
        offroad_trial=offroad_distance.configure(args,manifest['rom'],manifest['settings'])
        if offroad_trial:
            report['offroad_distance']=offroad_trial
        host_trial=world_host_options.configure(args,manifest['rom'],manifest['settings'])
        if host_trial:report['world_host_scenery']=host_trial
        usa_host_trial=usa_host_options.configure(args,manifest['rom'],manifest['settings'])
        if usa_host_trial:report['usa_host_scenery']=usa_host_trial
        offroad_host_trial=offroad_host_options.configure(args,manifest['rom'],manifest['settings'])
        if offroad_host_trial:report['offroad_host_scenery']=offroad_host_trial
        vunit_bootstrap_trial=vunit_bootstrap.configure(args,manifest['rom'],manifest['settings'],reference['frames'])
        if vunit_bootstrap_trial:report['vunit_bootstrap']=vunit_bootstrap_trial
        vunit_runtime_trial=vunit_runtime.configure(args,manifest['rom'],manifest['settings'],reference['frames'],vunit_bootstrap_trial)
        if vunit_runtime_trial:report['vunit_runtime']=vunit_runtime_trial
        mirror_trial=vunit_original_mirror.configure(args,manifest['rom'],manifest['settings'],reference['frames'])
        if mirror_trial:report['vunit_original_mirror']=mirror_trial
        host_failure_trial=vunit_host_failure.configure(args,manifest['rom'],manifest['settings'],reference['frames'])
        if host_failure_trial:report['vunit_host_failure']=host_failure_trial
        exotica_failure_trial=exotica_host_failure.configure(args,manifest['rom'],manifest['settings'],reference['frames'])
        if exotica_failure_trial:report['exotica_host_failure']=exotica_failure_trial
        journal_trial=exotica_journals.configure(args,manifest['rom'],manifest['settings'])
        if journal_trial:report['exotica_journals']=journal_trial
        bootstrap_trial=exotica_bootstrap.configure(args,manifest['rom'],manifest['settings'],reference['frames'])
        if bootstrap_trial:report['exotica_bootstrap']=bootstrap_trial
        shutdown_trial=exotica_shutdown.configure(args,manifest['rom'],manifest['settings'])
        if shutdown_trial:report['exotica_shutdown']=shutdown_trial
        runtime_trial=exotica_runtime.configure(args,manifest['rom'],manifest['settings'])
        if runtime_trial:
            report['exotica_runtime']=runtime_trial
            journal_trial['continuous']=True
        worker_trial=ffb_worker.configure(args,manifest['rom'],manifest['settings'])
        if worker_trial and worker_trial.get('stop_frame') is not None:
            if not worker_trial['stop_frame'] < reference['frames']-30:
                raise ValueError('force stop needs at least 30 later replay frames')
        if worker_trial:report['ffb_worker']=worker_trial
        # A screenshot can finish before later private scenes/materials. Drain
        # through the last completed Zeus frame, including runs without captures.
        # Older binaries may ignore this; strict receipt validation still applies.
        drain = completion_drain_target(gl_key, reference['frames'], expected_gl if args.gl_capture else (),
            depth_observation=bool(depth_trial and depth_trial.get('enabled')))
        if mirror_trial and mirror_trial.get('fade_metadata'):
            drain = reference['frames'] - 1
        if drain is not None:
            manifest['settings'][gl_key+'_GL_DRAIN_FRAME'] = str(drain)
            report['completion_drain_frame'] = drain
        ffb_worker.prepare(worker_trial,work)
        runtime = work / "run"
        command, env = prepare_run(case, manifest, runtime, playback=True, headless=args.headless)
        if args.display_size:
            from display_target import choose_size,monitors,apply_window_target
            zeus_overlay=gl_key=='MIDZ' and env.get('MIDZ_GL')=='1' and not args.native_renderer
            target=choose_size(args.display_size,monitors(),
                               allow_merged_triple=zeus_overlay and args.zeus_merged_panel)
            if args.zeus_merged_panel and not target['merged_center_panel']:
                raise ValueError('requested merged Zeus panel is not present')
            if target['merged_center_panel'] and (not args.candidate or
                    b'MIDZ_GL_PRESENT_SIZE' not in args.candidate.read_bytes()):
                raise ValueError('Merged triple display requires a Zeus candidate with explicit single-panel presentation')
            command=apply_window_target(command,target,zeus_overlay=zeus_overlay)
            if zeus_overlay:
                # Keep one completed-frame size if Windows merges/splits three
                # panels after preflight. Native selects the center third only
                # when the actual monitor is exactly three panels wide.
                env['MIDZ_GL_PRESENT_SIZE']=f'{args.display_size[0]}:{args.display_size[1]}'
            report['display_target']=target
            report['display_owner_policy']='native-size owner, fixed-size Zeus panel overlay' if zeus_overlay else 'maximized presentation window'
        if args.zeus_capture_frame is not None:
            zeus_capture_directory=runtime/'zeus-capture';zeus_capture_directory.mkdir()
            env.update(MIDZ_CAPTURE=str(zeus_capture_directory),MIDZ_CAPTURE_FRAME=str(args.zeus_capture_frame),MIDZ_CAPTURE_MINQUADS='0')
            env['MIDZ_CAPTURE_MODELS']='1' if args.zeus_capture_models else '0'
        if args.compare_gl and gl_key == 'MIDZ':
            # Zeus covers its owner's monitor. MAME's automatic monitor choice
            # can land on a secondary 1080p display despite a 4K reference.
            from display_target import choose, monitors
            target=choose(read_completed_frames(case/'record/gl-snap'),monitors())
            command=set_option(command,'-screen',target['selected']['device'])
            report['display_target']=target
        if args.small_window:
            command += ["-window", "-nomaximize"]
            report["window_override"] = "unmaximized; actual dimensions are recorded in captures.csv"
        if args.numeric_speed:
            env["MIDV_SPEED_NUMERIC"] = "1"
            report["numeric_speed_experiment"] = True
        if args.no_arcade_rpm:
            env['MIDV_TELEM_ARCADE_RPM']='0'
            report['arcade_rpm_disabled']=True
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
        if trial:
            patch_file = world_distance.compose(env.get('MIDV_PATCH'), runtime/'global-distance-patch.txt', trial['far'])
            env['MIDV_PATCH'] = str(patch_file)
            patch_entries = read_patch(patch_file)
            report['world_distance']['patch_sha256'] = sha256_file(patch_file)
            if args.capture_state:
                env.update(MIDV_RAMDUMP_DIR=str(capture), MIDV_RAMDUMP_EVERY=str(args.until_frame - 2))
        if usa_trial:
            patch_file = usa_distance.compose(env.get('MIDV_PATCH'), runtime/'usa-distance-patch.txt', usa_trial['far'])
            env['MIDV_PATCH'] = str(patch_file)
            patch_entries = read_patch(patch_file)
            report['usa_distance']['patch_sha256'] = sha256_file(patch_file)
            if args.capture_state:
                env.update(MIDV_RAMDUMP_DIR=str(capture), MIDV_RAMDUMP_EVERY=str(args.until_frame - 2))
        executable_digest=sha256_file(command[0])
        report['emulator_source']=binary_provenance.read(command[0],executable_digest)
        if args.display_watch and not args.display_size:
            raise ValueError('--display-watch requires an explicit --display-size')
        if args.prepare_only:
            if args.telemetry_loopback:
                raise ValueError('prepare-only does not allocate telemetry loopback sockets')
            plan=dict(schema=1,prepared=True,executed=False,physical_force=False,
                command=[str(x) for x in command],cwd=str(runtime),
                environment={k:v for k,v in env.items() if k.startswith(('MIDV_','MIDZ_','SNAP_','CRUISN_'))},
                executable_sha256=executable_digest,runtime_hashes=tree_hashes(runtime),
                candidate_dependencies={name:sha256_file(Path(command[0]).parent/name)
                    for name in ('SDL2.dll','force-profiles.ini','force-profiles.user.ini',Path(command[0]).name+'.build.json')
                    if (Path(command[0]).parent/name).is_file()},
                case=str(case),case_sha256=sha256_file(case/'case.json'),
                scope='Validated launch preparation only; no emulator execution, renderer acceptance or replay completion.')
            write_json(work/'launch-plan.json',plan)
            report.update(prepared_only=True,executed=False,launch_plan_sha256=sha256_file(work/'launch-plan.json'))
            write_json(work/'report.json',report)
            print(f"PREPARED (not executed): {work / 'launch-plan.json'}")
            return 0
        clock = SessionClock(runtime, "Replay: " + manifest.get("title", manifest["rom"]), args.clock_position)
        if args.clock:
            clock.start()
        telemetry = None
        if args.telemetry_loopback:
            from telemetry_loopback import TelemetryLoopback
            telemetry = TelemetryLoopback(runtime)
            telemetry.start(env)
        display_watch = None
        try:
            if args.display_watch:
                from display_watch import DisplayWatch
                display_watch = DisplayWatch()
                display_watch.start()
            invocation = execute(command, runtime, env, args.timeout)
        finally:
            if display_watch:
                report['display_watch'] = display_watch.close()
            clock.close()
            if telemetry:
                report['telemetry_loopback']=telemetry.close()
        # Recording uses the product launch log; normalize the replay's stdout
        # path so the same strict evidence validator serves both paths.
        if (runtime / "stdout.log").exists():
            (runtime / "launch.log").write_bytes((runtime / "stdout.log").read_bytes())
        stderr_path=runtime/'stderr.log'
        failure=execution_failure(invocation,stderr_path.read_text(encoding='utf-8',errors='replace') if stderr_path.exists() else '')
        if failure:
            raise ValueError(failure)
        if env.get(gl_key+'_CAPTURE_PACE') == '1':
            from capture_writer import verify as verify_writer
            verify_writer((runtime/'stderr.log').read_text(encoding='utf-8', errors='replace'), require_pacing=True)
        zeus_render_policy.verify_receipt(zeus_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'))
        palette_result=zeus_palette.verify_receipt(palette_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'))
        if palette_result:report['zeus_palette']['result']=palette_result
        margin_result=zeus_margin_clear.verify_receipt(margin_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'))
        if margin_result:report['zeus_margin_clear']['result']=margin_result
        sky_result=zeus_sky_options.verify_receipt(sky_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'))
        if sky_result:report['zeus_sky']['result']=sky_result
        shutdown_result=exotica_shutdown.verify(shutdown_trial,runtime)
        if shutdown_result:
            report['exotica_shutdown']['result']=shutdown_result
            if shutdown_result['classification']=='failed':raise ValueError('Exotica shutdown observed renderer or writer failure')
        exotica_failure_result=exotica_host_failure.verify_receipt(exotica_failure_trial,runtime)
        if exotica_failure_result:report['exotica_host_failure']['result']=exotica_failure_result
        bootstrap_result=exotica_bootstrap.verify(bootstrap_trial,runtime)
        if bootstrap_result:report['exotica_bootstrap']['result']=bootstrap_result
        lifetime_trial=exotica_bootstrap.lifetime_trial(bootstrap_trial,bootstrap_result,lifetime_trial)
        if lifetime_trial:
            report['exotica_lifetimes']=lifetime_trial
            if waiting_trial and waiting_trial.get('mode')=='observe':
                waiting_trial['lifetime']=dict(lifetime_trial)
        exotica_bootstrap.resolve_scenes(bootstrap_trial,bootstrap_result,scene_trial,waiting_trial,handover_trial,endpoint_trial)
        runtime_result=exotica_runtime.verify(runtime_trial,runtime,shutdown_result)
        if runtime_result:report['exotica_runtime']['result']=runtime_result
        reset_result=exotica_reset.verify(runtime_trial,runtime,reference['frames'])
        if reset_result:report['exotica_reset']=reset_result
        journal_error=None
        try:journal_result=exotica_journals.verify(journal_trial,runtime,runtime_result=runtime_result)
        except ValueError as exc:
            # A startup retirement can contain no endpoint workload. Keep the
            # strict failure, but still check original inputs and captured pixels.
            journal_result=None;journal_error=str(exc)
            report.setdefault('exotica_journals',{})['verification_error']=journal_error
        if journal_result:report['exotica_journals']['result']=journal_result
        if not journal_trial or journal_trial['mode']!='quiet':
            scene_result=exotica_scene_options.verify_receipt(scene_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'),runtime)
            if scene_result:report['exotica_host_scene']['result']=scene_result
            lifetime_result=exotica_lifetimes.verify_receipt(lifetime_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'),runtime)
            if lifetime_result:report['exotica_lifetimes']['result']=lifetime_result
            waiting_result=exotica_waiting.verify_receipt(waiting_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'),runtime)
            if waiting_result:report['exotica_waiting']['result']=waiting_result
            handover_result=exotica_handover.verify_receipt(handover_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'),runtime)
            if handover_result:report['exotica_handover']['result']=handover_result
            endpoint_result=exotica_model_endpoint.verify_receipt(endpoint_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'),runtime)
            if endpoint_result:report['exotica_model_endpoint']['result']=endpoint_result
            depth_result=zeus_depth_mirror.verify_receipt(depth_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'),runtime)
            if depth_result:report['zeus_depth_mirror']['result']=depth_result
        mirror_result=vunit_original_mirror.verify(mirror_trial,runtime)
        if mirror_result:report['vunit_original_mirror']['result']=mirror_result
        stall_result=zeus_stream.verify_stall(stall_trial,(runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'))
        if stall_result:report['zeus_stall']['result']=stall_result
        if args.patch_at_frame is not None:
            receipt = f"session.lua: game patch {len(patch_entries)} words at frame {args.patch_at_frame}"
            if receipt not in (runtime / "launch.log").read_text(encoding="utf-8", errors="replace"):
                raise ValueError("late game patch application receipt missing")
        worker_result=ffb_worker.verify_receipt(worker_trial,runtime)
        timing_result=exotica_timing.verify(timing_trial,runtime)
        if timing_result:report['exotica_timing']['result']=timing_result
        if worker_result:report['ffb_worker']['result']=worker_result
        # Preserve independent teardown evidence even when an intentionally
        # interrupted replay subsequently fails its full-input comparison.
        vunit_bootstrap_result=vunit_bootstrap.verify(vunit_bootstrap_trial,runtime)
        if vunit_bootstrap_result:report['vunit_bootstrap']['result']=vunit_bootstrap_result
        vunit_runtime_result=vunit_runtime.verify(vunit_runtime_trial,runtime,vunit_bootstrap_result)
        if vunit_runtime_result:report['vunit_runtime']['result']=vunit_runtime_result
        host_failure_result=vunit_host_failure.verify_receipt(host_failure_trial,runtime)
        if host_failure_result:report['vunit_host_failure']['result']=host_failure_result
        convert_raw_snapshots(runtime)
        report["evidence"] = session_evidence(runtime, manifest["every"], invocation["returncode"],
            require_gl=not (args.headless or args.native_renderer) and bool(manifest["settings"].get(gl_key+"_GL_SNAP")))
        report["comparison"] = compare_evidence(case / "record", runtime, reference, report["evidence"])
        if args.gl_capture:
            # A legacy receipt cannot validate a requested completed-frame range.
            # Preserve the independent input/native comparison even if GL is incomplete.
            read_completed_frames(runtime / "gl-snap", expected_gl)
        if args.display_size and gl_key=='MIDZ' and report['evidence'].get('gl_captures'):
            # A selected monitor can change size after launch. Zeus covers that
            # monitor exactly; unlike V-Unit there is no caption/client inset.
            from display_target import verify_completed_size
            report['display_target']['completed']=verify_completed_size(
                args.display_size,report['evidence']['gl_captures']['files'])
        report["passed"] = report["comparison"]["passed"]
        if display_watch and not report['display_watch']['passed']:
            report['passed'] = False
            report['error'] = 'display topology changed or could not be observed during replay'
        if journal_error:
            report['passed']=False
            report['error']=journal_error
        if telemetry and not report['telemetry_loopback']['passed']:
            # Keep independent input/image evidence when a telemetry producer
            # fails; a silent UDP stream must not prevent snapshot validation.
            report['passed']=False
            report['error']='telemetry loopback capture failed'
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
            if args.patch or trial or usa_trial:
                program_ram = capture / f"ram_{args.until_frame - 2:06d}.bin"
                report["effective_patch"] = verify_patch_ram(program_ram, patch_entries)
                report["capture"]["sha256"][program_ram.name] = sha256_file(program_ram)
                report["passed"] = report["passed"] and report["effective_patch"]["passed"]
        if args.zeus_capture_frame is not None:
            from zeus_capture import validate as validate_zeus_capture
            if f'MIDZ capture complete in {zeus_capture_directory}' not in (runtime/'stderr.log').read_text(encoding='utf-8',errors='replace'):
                raise ValueError('Zeus capture completion receipt missing')
            report['zeus_capture']=validate_zeus_capture(zeus_capture_directory,args.zeus_capture_frame)
            if args.zeus_capture_models:
                from zeus_models import validate as validate_zeus_models
                report['zeus_models']=validate_zeus_models(zeus_capture_directory,args.zeus_capture_frame,
                    sum(report['zeus_capture']['quad_frames'].values()))
                if report['zeus_models']['render_policy']!=(zeus_trial['mask'] if zeus_trial else 0):
                    raise ValueError('Zeus model capture policy differs from the requested rendering semantics')
        if exotica_failure_result:
            if exotica_failure_result['degraded']:
                report['passed']=False
                report['error']='Exotica future assembly failed; retired output does not qualify parity'
        if host_failure_result:
            if host_failure_result['degraded']:
                report['passed']=False
                report['error']='host scenery preparation failed; degraded output does not qualify parity'
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        report["passed"] = False
        report["error"] = str(exc)
        if isinstance(exc, IncompleteCaptureError):
            report['capture_diagnostics'] = exc.capture_diagnostics
    write_json(work / "report.json", report)
    print(("PASS" if report["passed"] else "FAIL") + f": {work / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
