"""Verify an imported Infinite Time cheat through real MAME on/off commands.

Uses an immutable driving recording and a separate runtime. Physical outputs off.
Only the named timer cheat is tested; catalog loading is not other-cheat acceptance.
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


def inspect(directory, rom):
    with (Path(directory)/'cheat-probe.csv').open() as source:
        rows = list(csv.DictReader(source))
    if [int(r['frame']) for r in rows] != list(range(2500,3301)):
        raise ValueError('incomplete timer observations')
    enabled = [r for r in rows if 2700 <= int(r['frame']) < 3000]
    disabled = [r for r in rows if int(r['frame']) >= 3000]
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('case',type=Path); ap.add_argument('archive',type=Path)
    ap.add_argument('--candidate',type=Path,required=True); ap.add_argument('--output')
    args = ap.parse_args(argv)
    work = new_run('cheat-check',args.output)
    report = {'passed':False,'physical_force':False,'candidate_sha256':sha256_file(args.candidate),
              'archive_sha256':sha256_file(args.archive),
              'probe_sha256':sha256_file(ROOT/'lua/cheat_probe.lua')}
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
        result = execute(command,runtime,env,180)
        logs = ''.join((runtime/name).read_text(errors='replace') for name in ('stdout.log','stderr.log'))
        if result['returncode'] != 0 or 'CHEAT PROBE COMPLETE' not in logs or any(s in logs for s in ('[LUA ERROR]','cheat_probe: failed:')):
            raise ValueError('native cheat probe did not complete cleanly')
        report.update(rom=manifest['rom'],xml_sha256=cat['sha256'],timer=inspect(runtime,manifest['rom']),passed=True)
    except (OSError,ValueError,KeyError) as error:
        report['error'] = str(error)
    write_json(work/'report.json',report)
    print('PASS' if report['passed'] else 'FAIL',work,report.get('error',''),flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__': sys.exit(main())
