"""Verify an imported Infinite Time cheat through real MAME on/off commands.

Uses an immutable driving recording and a separate runtime. Physical outputs off.
Optional live-action checks also verify Finish Race Now and instruction restoration.
Catalog loading is not acceptance of untested cheats.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

import cheats
from diagnostic_runtime import ROOT, execute, new_run
from session_case import prepare_run, set_option, tree_hashes
from verification import sha256_file, write_json


def inspect(directory, rom, finish=False):
    with (Path(directory)/'cheat-probe.csv').open() as source:
        rows = list(csv.DictReader(source))
    if [int(r['frame']) for r in rows] != list(range(2500,3301)):
        raise ValueError('incomplete timer observations')
    enabled = [r for r in rows if 2700 <= int(r['frame']) < 3000]
    disabled = [r for r in rows if 3000 <= int(r['frame']) < (3200 if finish else 3301)]
    expected = (0,0) if rom == 'offroadc' else (99,0)
    values = lambda records: {(int(r['timer']),int(r['timer_high'])) for r in records}
    # The game can decrement/increment once before the cheat's next callback.
    # Require correction on the following frame, never a sustained countdown.
    transient = (1,0) if rom == 'offroadc' else (98,0)
    samples = [(int(r['timer']),int(r['timer_high'])) for r in enabled]
    by_frame = {int(r['frame']):(int(r['timer']),int(r['timer_high'])) for r in rows}
    if rom == 'offroadc':
        # Off Road resets seconds/hundredths each frame. At frame_done the
        # guest has already advanced 1-2 hundredths, never a whole second.
        corrected = all(seconds == 0 and 0 <= hundredths <= 2 for seconds,hundredths in samples)
    else:
        corrected = samples.count(expected) >= .95*len(samples) and all(
            v == expected or (v == transient and by_frame[int(enabled[i]['frame'])+1] == expected)
            for i,v in enumerate(samples))
    if not corrected or {r['state'] for r in enabled} != {'On'}:
        raise ValueError('enabled timer did not hold the expected game value')
    if len(values(disabled)) < 2 or {r['state'] for r in disabled} != {'Off'}:
        raise ValueError('timer did not resume after disabling the cheat')
    return {'on_samples':len(enabled),'target_value':expected,'on_values':sorted(values(enabled)),
            'one_frame_ticks':samples.count(transient),'off_samples':len(disabled),
            'off_values':sorted(values(disabled)), 'csv_sha256':sha256_file(Path(directory)/'cheat-probe.csv')}


def inspect_restoration(directory, rom, finish):
    with (Path(directory)/'cheat-code-probe.csv').open() as source:
        rows=list(csv.DictReader(source))
    addresses={int(row['address'],16) for row in rows}
    results=[]
    for address in sorted(addresses):
        samples={int(row['frame']):int(row['value'],16) for row in rows if int(row['address'],16)==address}
        expected={int(row['expected'],16) for row in rows if int(row['address'],16)==address}
        if set(samples)!={2699,2710,2799,2800,2801,3100} or len(expected)!=1:
            raise ValueError('incomplete instruction restoration observations')
        active=expected.pop(); original=samples[2699]
        if original==active or any(samples[f]!=active for f in (2710,2799)) or any(samples[f]!=original for f in (2800,2801,3100)):
            raise ValueError('Drive Anywhere did not patch and restore the original instruction')
        results.append({'address':address,'original':original,'active':active})
    if bool(results)!=(rom!='crusnwld24'):
        raise ValueError('instruction-restoration coverage does not match this revision')
    if finish:
        with (Path(directory)/'cheat-probe.csv').open() as source:
            timers={int(row['frame']):int(row['timer']) for row in csv.DictReader(source)}
        if timers[3199]==0 or timers[3200]!=0:
            raise ValueError('Finish Race Now did not zero the running timer at activation')
    return {'instructions':results,'finish_timer_zero':finish,
            'csv_sha256':sha256_file(Path(directory)/'cheat-code-probe.csv')}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('case',type=Path); ap.add_argument('archive',type=Path)
    ap.add_argument('--candidate',type=Path,required=True); ap.add_argument('--output')
    ap.add_argument('--live-actions',action='store_true',help='exercise the current live loader/action journal with a read-only timer observer')
    ap.add_argument('--restore-and-finish',action='store_true',help='also exercise available Drive Anywhere on/off and Finish Race Now actions; requires --live-actions')
    args = ap.parse_args(argv)
    if args.restore_and_finish and not args.live_actions: ap.error('--restore-and-finish requires --live-actions')
    work = new_run('cheat-check',args.output)
    report = {'passed':False,'physical_force':False,'candidate_sha256':sha256_file(args.candidate),
              'archive_sha256':sha256_file(args.archive),
              'probe_sha256':sha256_file(ROOT/('lua/cheat_watch.lua' if args.live_actions else 'lua/cheat_probe.lua')),
              'live_actions':args.live_actions}
    try:
        case = args.case.resolve(); manifest = json.loads((case/'case.json').read_text())
        if manifest['status'] != 'recorded' or manifest['evidence']['frames'] < 3300:
            raise ValueError('completed driving recording of at least 3300 frames required')
        if tree_hashes(case/'initial') != manifest['initial_hashes'] or sha256_file(case/'record/input/session.inp') != manifest['inp_sha256']:
            raise ValueError('original recording changed')
        runtime = work/'run'; command,env = prepare_run(case,manifest,runtime,playback=True,headless=True)
        env.pop('MIDV_CHEATS',None)
        cheats.import_files(args.archive,work/'import')
        cat = cheats.catalog(work/'import',manifest['rom'])
        if not cat['entries'] or cat['entries'][0]['description'] != 'Infinite Time':
            raise ValueError('expected exact-revision timer cheat not found')
        command[0] = str(args.candidate.resolve())
        command = [arg for arg in command if arg != '-nocheat'] + ['-cheat']
        command = set_option(command,'-cheatpath',work/'import/cheats')
        command = set_option(command,'-autoboot_script',ROOT/'lua/cheat_probe.lua')
        if args.live_actions:
            bundle=cheats.prepare(ROOT,work/'import',manifest['rom'])
            actions=[(2600,1,1,0),(3000,1,0,0)]
            finish=False
            if args.restore_and_finish:
                entries={entry['description']:entry['index'] for entry in cat['entries']}
                if 'Drive Anywhere' in entries:
                    actions.extend([(2700,entries['Drive Anywhere'],1,0),(2800,entries['Drive Anywhere'],0,0)])
                finish='Finish this Race Now!' in entries
                if finish: actions.append((3200,entries['Finish this Race Now!'],0,1))
                env['CHEAT_PROBE_RESTORE']='1'
            (bundle/'replay-actions.csv').write_text('frame,index,steps,activate\n'+''.join(','.join(map(str,row))+'\n' for row in sorted(actions)),encoding='utf-8')
            command=set_option(command,'-cheatpath',bundle)
            command=set_option(command,'-autoboot_script',ROOT/'lua/session.lua')
            env.update(MIDV_CHEATS=str(bundle),SNAP_STOP='3300',SNAP_PROBE_SCRIPT=str(ROOT/'lua/cheat_watch.lua'))
            report['loader_sha256']=sha256_file(ROOT/'lua/cheats.lua')
        result = execute(command,runtime,env,180)
        logs = ''.join((runtime/name).read_text(errors='replace') for name in ('stdout.log','stderr.log'))
        if result['returncode'] != 0 or 'CHEAT PROBE COMPLETE' not in logs or any(s in logs for s in ('[LUA ERROR]','cheat_probe: failed:')):
            raise ValueError('native cheat probe did not complete cleanly')
        report.update(rom=manifest['rom'],xml_sha256=cat['sha256'],timer=inspect(runtime,manifest['rom'],args.restore_and_finish and finish),passed=True)
        if args.restore_and_finish:
            report['restoration']=inspect_restoration(runtime,manifest['rom'],finish)
        if args.live_actions:
            selection=json.loads((bundle/'selection.json').read_text(encoding='utf-8'))
            observed=cheats.read_actions(bundle/'actions.csv',selection,3300)
            expected=cheats.read_actions(bundle/'replay-actions.csv',selection,3300)
            if observed != expected: raise ValueError('actual live cheat actions differ from the requested frames')
            report.update(actions=observed,actions_sha256=sha256_file(bundle/'actions.csv'))
    except (OSError,ValueError,KeyError) as error:
        report.update(passed=False,error=str(error))
    write_json(work/'report.json',report)
    print('PASS' if report['passed'] else 'FAIL',work,report.get('error',''),flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__': sys.exit(main())
