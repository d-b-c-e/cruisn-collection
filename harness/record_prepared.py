"""Record live inputs using a validated continuous-scenery launch plan.

Uses a new private case, the plan's archived initial wheel/configuration state
and its exact candidate. Physical FFB remains off. This is an attended recorder,
not a replay or a release launcher; --prepare-only never starts gameplay.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys

from diagnostic_runtime import diagnostic_env, execute, new_run
from session_case import Recording, set_option, tree_hashes
from session_clock import SessionClock, position
from verification import sha256_file, write_json


def load_plan(directory):
    directory=Path(directory).resolve()
    report=json.loads((directory/'report.json').read_text(encoding='utf-8'))
    plan=json.loads((directory/'launch-plan.json').read_text(encoding='utf-8'))
    if (report.get('prepared_only') is not True or report.get('executed') is not False
            or report.get('passed') is not False or report.get('error')
            or report.get('launch_plan_sha256')!=sha256_file(directory/'launch-plan.json')
            or plan.get('schema')!=1 or plan.get('prepared') is not True
            or plan.get('executed') is not False or plan.get('physical_force') is not False
            or report.get('scenery_preset',{}).get('name')!='continuous-3x'):
        raise ValueError('recording requires an unexecuted validated continuous scenery plan')
    runtime=directory/'run'
    if Path(plan['cwd']).resolve()!=runtime or tree_hashes(runtime)!=plan['runtime_hashes']:
        raise ValueError('prepared initial state has changed or been executed')
    case=Path(plan['case'])
    if sha256_file(case/'case.json')!=plan['case_sha256']:
        raise ValueError('parent case identity changed')
    if sha256_file(plan['command'][0])!=plan['executable_sha256']:
        raise ValueError('prepared candidate changed')
    dependencies={name:sha256_file(Path(plan['command'][0]).parent/name)
        for name in ('SDL2.dll','force-profiles.ini','force-profiles.user.ini')
        if (Path(plan['command'][0]).parent/name).is_file()}
    if dependencies!=plan['candidate_dependencies']:
        raise ValueError('prepared candidate dependencies changed')
    env=plan['environment']
    if env.get('MIDV_FFB')!='0' or any(k in env for k in ('MIDV_FFB_TEST','MIDV_TELEM_UDP','MIDV_TELEM_FORZA','MIDZ_TELEM_UDP')):
        raise ValueError('prepared recording must disable physical force and external telemetry')
    if any(k.endswith(('_HOST_FAILURE_FRAME','_GL_STOP_FRAME')) or '_GL_STALL_' in k for k in env):
        raise ValueError('live recording cannot inherit failure injection or consumer stalls')
    if ('SNAP_PROBE_SCRIPT' in env or any(k.endswith(('_GL_SNAP','_CAPTURE','_STATEDUMP_DIR','_RAMDUMP_DIR','_QUADLOG')) for k in env)
            or any(env.get(k) for k in ('MIDZ_HOST_SNAPSHOTS','MIDZ_DEPTH_SNAPSHOTS'))
            or env.get('MIDZ_MODEL_ENDPOINT_SNAPSHOT','0')!='0'):
        raise ValueError('live recording requires a quiet plan without scheduled captures or probes')
    manifest=json.loads((case/'case.json').read_text(encoding='utf-8'))
    for path,digest in manifest.get('rom_containers',{}).items():
        if sha256_file(path)!=digest:raise ValueError('prepared ROM container changed: '+path)
    if plan['command'][1]!=manifest['rom'] or report['scenery_preset']['rom']!=manifest['rom']:
        raise ValueError('prepared ROM differs from its parent and preset')
    return plan,report,manifest


def live_command(command):
    """Remove replay/finite-stop options without changing input bindings."""
    result=[];i=0
    valued={'-playback','-record','-seconds_to_run','-frames_to_run'}
    while i<len(command):
        word=str(command[i])
        if word in valued:
            if i+1==len(command) or str(command[i+1]).startswith('-'):
                raise ValueError('incomplete replay command option '+word)
            i+=2;continue
        if word not in ('-exit_after_playback',):result.append(word)
        i+=1
    if any(x in result for x in ('-nojoystick','-nomouse','-nolightgun')):
        raise ValueError('live recording cannot inherit disabled input devices')
    return set_option(result,'-seconds_to_run',0)


def renderer_receipts(report, runtime, frames):
    """Use actual recording extent; never infer complete playback or visual quality."""
    report=copy.deepcopy(report)
    if 'exotica_runtime' in report:
        import exotica_bootstrap,exotica_shutdown,exotica_runtime,exotica_journals,exotica_host_failure
        report['exotica_bootstrap']['frames']=frames
        bootstrap=exotica_bootstrap.verify(report['exotica_bootstrap'],runtime)
        shutdown=exotica_shutdown.verify(report['exotica_shutdown'],runtime)
        continuous=exotica_runtime.verify(report['exotica_runtime'],runtime,shutdown)
        journals=exotica_journals.verify(report['exotica_journals'],runtime,runtime_result=continuous)
        trial=report.get('exotica_host_failure')
        if trial and trial.get('continuous'):trial['last']=frames-1
        failure=exotica_host_failure.verify_receipt(trial,runtime)
        if failure and failure['degraded']:raise ValueError('recording used retired original-only fallback')
        return dict(bootstrap=bootstrap,shutdown=shutdown,runtime=continuous,journals=journals,failure=failure)
    import vunit_bootstrap,vunit_runtime,vunit_host_failure
    report['vunit_bootstrap']['runtime_last']=frames-1
    report['vunit_runtime']['verification_last']=frames-1
    report['vunit_host_failure']['last']=frames-1
    bootstrap=vunit_bootstrap.verify(report['vunit_bootstrap'],runtime)
    continuous=vunit_runtime.verify(report['vunit_runtime'],runtime,bootstrap)
    failure=vunit_host_failure.verify_receipt(report['vunit_host_failure'],runtime)
    if failure['degraded']:raise ValueError('recording used degraded original-only fallback')
    return dict(bootstrap=bootstrap,runtime=continuous,failure=failure)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('plan',type=Path,help='directory created by replay.py --prepare-only --scenery-preset continuous-3x')
    ap.add_argument('--output',required=True,help='new private recording directory')
    ap.add_argument('--title',required=True)
    ap.add_argument('--prepare-only',action='store_true',help='freeze the new live case but do not start gameplay')
    ap.add_argument('--no-clock',action='store_true')
    ap.add_argument('--clock-position',type=position,default=(12,12))
    ap.add_argument('--timeout',type=float,default=1800,help='hard recording timeout; physical FFB is always off')
    args=ap.parse_args(argv)
    if not 0<args.timeout<=7200:ap.error('timeout must be in (0,7200] seconds')
    try:
        plan,prepared,parent=load_plan(args.plan)
        command=live_command(plan['command'])
    except (OSError,ValueError,KeyError) as exc:ap.error(str(exc))
    work=new_run('prepared-recording',args.output)
    result=dict(prepared=False,executed=False,recorded=False,renderer_qualified=False,
        physical_force=False,plan_sha256=sha256_file(args.plan/'launch-plan.json'),
        scope='Live input recording and native runtime receipts; deterministic replay, visual acceptance and physical wheel acceptance remain separate.')
    try:
        settings={k:v for k,v in plan['environment'].items()
                  if k.startswith(('MIDV_','MIDZ_')) and not k.endswith('_GL_DRAIN_FRAME')}
        recording=Recording(work/'case',every=parent['every'],stop_frame=0,clock=not args.no_clock)
        command,env,runtime=recording.prepare(command,diagnostic_env(settings),Path(plan['cwd']))
        if any(x in command for x in ('-playback','-exit_after_playback')):
            raise ValueError('live recording unexpectedly retained playback')
        recording.manifest.update(title=args.title,prepared_scenery=prepared['scenery_preset'],
            prepared_plan_sha256=result['plan_sha256'],input_configuration_source=plan['case'])
        write_json(recording.path/'case.json',recording.manifest)
        result['prepared']=True
        write_json(work/'live-launch.json',dict(command=command,cwd=str(runtime),
            environment={k:v for k,v in env.items() if k.startswith(('MIDV_','MIDZ_','SNAP_'))},
            executable_sha256=sha256_file(command[0])))
        if not args.prepare_only:
            print('Live candidate recording: physical FFB OFF. F12 ends the game; wait for recording validation.',flush=True)
            clock=SessionClock(runtime,args.title,args.clock_position)
            if not args.no_clock:clock.start()
            try:invocation=execute(command,runtime,env,args.timeout)
            finally:clock.close()
            result['executed']=True
            if (runtime/'stdout.log').exists():shutil.copy2(runtime/'stdout.log',runtime/'launch.log')
            recording.finish(invocation['returncode'])
            result['recorded']=recording.manifest['status']=='recorded'
            if invocation['error'] or not result['recorded']:
                raise ValueError(invocation['error'] or recording.manifest.get('error'))
            result['renderer']=renderer_receipts(prepared,runtime,recording.manifest['evidence']['frames'])
            result['renderer_qualified']=True
    except (OSError,ValueError,KeyError) as exc:result['error']=str(exc)
    write_json(work/'report.json',result)
    print(('PREPARED (not executed)' if args.prepare_only and result['prepared'] and 'error' not in result else
           'RECORDED' if result['recorded'] and result['renderer_qualified'] else 'FAIL')+': '+str(work/'report.json'))
    return 0 if 'error' not in result and (result['prepared'] if args.prepare_only else result['recorded'] and result['renderer_qualified']) else 1


if __name__=='__main__':sys.exit(main())
