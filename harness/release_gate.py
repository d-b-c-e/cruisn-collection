"""Report release readiness without launching games, actuating a wheel or publishing.

Runs isolated configuration tests and checks a complete local regression report.
An attended ledger records checks separately from explicit maintainer waivers.
Waivers never bypass automated gates or turn unperformed checks into passes.
"""
import argparse
import io
import json
from pathlib import Path
import sys
import unittest

from diagnostic_runtime import ROOT
from release_identity import source_identity
from verification import sha256_file, write_json
from check_release_package import FREEPLAY
from local_checks import validate_report as validate_local_checks


def requirements(plan):
    return {**{f'{rom}/{key}':desc for rom in plan['games'] for key,desc in plan['per_game'].items()},
            **{f'shared/{key}':desc for key,desc in plan['shared'].items()}}


def regression_check(report, candidate_hash, source_hash, suite, suite_hash):
    expected={c['id'] for c in suite['cases']}
    ids=[c['id'] for c in report.get('cases',[])]
    return (report.get('passed') is True and report.get('physical_force') is False
        and report.get('candidate_sha256')==candidate_hash and report.get('source_identity')==source_hash
        and report.get('suite_sha256')==suite_hash and report.get('subset') is None
        and set(ids)==expected and len(ids)==len(expected)
        and all(c.get('passed') is True for c in report['cases']))


def acceptance_check(ledger, expected, candidate_hash, source_hash, base):
    if ledger.get('candidate_sha256')!=candidate_hash or ledger.get('source_identity')!=source_hash:
        return {'passed':False,'error':'attended evidence belongs to a different build/source','pending':list(expected)}
    pending=[]; errors=[]; waived=[]
    def validate_evidence(row, label):
        if not all(isinstance(row.get(k),str) and row[k].strip() for k in ('reviewer','date','notes')):
            errors.append(f'{label}: requires reviewer, date and observation/acceptance notes')
        evidence=row.get('evidence',[])
        if not isinstance(evidence,list) or not evidence:
            errors.append(f'{label}: requires hashed evidence files')
            return
        for item in evidence:
            try:
                if sha256_file(Path(base)/item['path'])!=item['sha256']:
                    errors.append(f'{label}: evidence hash changed')
            except (OSError,KeyError,TypeError): errors.append(f'{label}: missing/invalid evidence')
    for key in expected:
        row=ledger.get('checks',{}).get(key,{})
        if row.get('status')=='waived':
            waived.append(key)
            if not isinstance(row.get('notes'),str) or not row['notes'].strip():
                errors.append(f'{key}: waiver requires a reason and remaining coverage limits')
            continue
        if row.get('status')!='pass': pending.append(key); continue
        validate_evidence(row,key)
    if waived:
        approval=ledger.get('maintainer_approval',{})
        if approval.get('decision')!='release-current-state':
            errors.append('waivers require explicit maintainer release-current-state approval')
        approved=approval.get('waived_checks',[])
        if (not isinstance(approved,list) or not all(isinstance(k,str) for k in approved)
                or sorted(approved)!=sorted(waived)):
            errors.append('maintainer approval must enumerate exactly the waived checks')
        validate_evidence(approval,'maintainer approval')
    return {'passed':not pending and not errors,'all_checks_passed':not pending and not errors and not waived,
            'pending':pending,'waived':waived,'errors':errors}


def fresh_boot_check(report, candidate_hash, source_hash):
    rows = report.get('cases', [])
    return (report.get('passed') is True and report.get('physical_force') is False
        and report.get('candidate_sha256') == candidate_hash
        and report.get('source_identity') == source_hash
        and len(rows) == len(FREEPLAY) and {row['rom'] for row in rows} == set(FREEPLAY)
        and all(row.get('passed') is True and row.get('replay_exit') == 0
                and len(row.get('persisted', [])) == 2
                and all(item.get('passed') is True for item in row['persisted']) for row in rows))


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--checks',type=Path,help='complete current Windows local_checks.py report')
    ap.add_argument('--regressions',type=Path)
    ap.add_argument('--fresh-boots',type=Path,help='complete current check_fresh_boots.py report')
    ap.add_argument('--attended',type=Path)
    ap.add_argument('--init-attended',type=Path,help='write a new pending ledger, never replace one')
    ap.add_argument('--report',required=True,type=Path)
    args=ap.parse_args(argv)
    identity=source_identity(ROOT)
    candidate=sha256_file(args.candidate)
    plan=json.loads((ROOT/'fixtures/release/checklist.json').read_text())
    expected=requirements(plan)
    if args.init_attended:
        ledger={'schema':1,'candidate_sha256':candidate,'source_identity':identity['sha256'],
                'checks':{key:{'requirement':desc,'status':'pending','reviewer':'','date':'','notes':'','evidence':[]}
                          for key,desc in expected.items()}}
        with args.init_attended.open('x',encoding='utf-8') as out: json.dump(ledger,out,indent=2)
    report={'schema':1,'ready_for_release':False,'candidate_sha256':candidate,
            'source_identity':identity['sha256'],'physical_force':False}
    report['local_checks']={'passed':False,'error':'complete current Windows local check report required'}
    if args.checks:
        try:
            value=json.loads(args.checks.read_text())
            passed=validate_local_checks(value,identity['sha256'],args.checks.parent)
            report['local_checks']={'passed':passed,'path':str(args.checks),'sha256':sha256_file(args.checks),
                                   'error':None if passed else 'failed, partial, stale or damaged local check evidence'}
        except (OSError,ValueError,KeyError,TypeError) as error: report['local_checks']['error']=str(error)
    stream=io.StringIO()
    tests=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_release_contract.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(tests)
    report['configuration']={'passed':result.wasSuccessful() and not result.skipped,
                             'tests':result.testsRun,'skipped':len(result.skipped),'details':stream.getvalue()}
    suite_path=ROOT/'fixtures/regressions/collection.json'
    report['regressions']={'passed':False,'error':'complete current regression report required'}
    if args.regressions:
        try:
            value=json.loads(args.regressions.read_text())
            passed=regression_check(value,candidate,identity['sha256'],json.loads(suite_path.read_text()),sha256_file(suite_path))
            report['regressions']={'passed':passed,'path':str(args.regressions),'sha256':sha256_file(args.regressions),
                                   'error':None if passed else 'failed, incomplete or stale regression evidence'}
        except (OSError,ValueError,KeyError,TypeError) as error: report['regressions']['error']=str(error)
    report['attended']={'passed':False,'pending':list(expected)}
    report['fresh_boots']={'passed':False,'error':'complete current fresh-seed boot/persistence report required'}
    if args.fresh_boots:
        try:
            value=json.loads(args.fresh_boots.read_text())
            passed=fresh_boot_check(value,candidate,identity['sha256'])
            report['fresh_boots']={'passed':passed,'path':str(args.fresh_boots),'sha256':sha256_file(args.fresh_boots),
                                 'error':None if passed else 'failed, incomplete or stale fresh-boot evidence'}
        except (OSError,ValueError,KeyError,TypeError) as error: report['fresh_boots']['error']=str(error)
    if args.attended:
        try:
            report['attended']=acceptance_check(json.loads(args.attended.read_text()),expected,candidate,identity['sha256'],args.attended.parent)
        except (OSError,ValueError,KeyError,TypeError) as error: report['attended']['error']=str(error)
    report['automated_configuration_and_replays_pass']=report['configuration']['passed'] and report['regressions']['passed']
    report['automated_pass']=(report['automated_configuration_and_replays_pass']
                              and report['fresh_boots']['passed'] and report['local_checks']['passed'])
    report['ready_for_release']=report['automated_pass'] and report['attended']['passed']
    write_json(args.report,report)
    print(f"Release {'READY' if report['ready_for_release'] else 'NOT READY'}: {args.report}")
    print(f"Local checks={report['local_checks']['passed']}; configuration={report['configuration']['passed']}; full replay suite={report['regressions']['passed']}; "
          f"fresh boots={report['fresh_boots']['passed']}; attended checks pending={len(report['attended'].get('pending',[]))}; "
          f"maintainer waivers={len(report['attended'].get('waived',[]))}")
    return 0 if report['ready_for_release'] else 1


if __name__=='__main__':sys.exit(main())
