"""Boot/replay every fresh seed and check persisted free play, with physical force off.

    Neutral inputs do not establish no-coin race start or physical control acceptance.
"""
import argparse
from pathlib import Path
import sys

from check_release_package import FREEPLAY
from cmos_settings import offroad_checksum
from diagnostic_runtime import ROOT, new_run
from release_identity import source_identity
import run_replay_smoke
from verification import sha256_file, write_json


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args(argv)
    out = new_run('fresh-boots', args.output)
    report = {'passed':False, 'physical_force':False, 'scope':__doc__,
              'candidate_sha256':sha256_file(args.candidate),
              'source_identity':source_identity(ROOT)['sha256'], 'cases':[]}
    for rom, (filename, addresses) in FREEPLAY.items():
        work = out/rom
        code = run_replay_smoke.main(['--mame',str(args.candidate),'--rom',rom,
            '--frames','1800','--every','300','--timeout','180','--output',str(work)])
        row = {'rom':rom, 'passed':False, 'replay_exit':code, 'persisted':[]}
        try:
            for stage in ('case/record','replay/run'):
                path = work/stage/'nvram'/rom/filename
                data = path.read_bytes()
                values = [data[a] for a in addresses]
                valid = all(value == 1 for value in values)
                if rom == 'offroadc':
                    expected,stored = offroad_checksum(data)
                    valid = valid and expected == stored
                row['persisted'].append({'path':str(path.relative_to(out)),
                    'sha256':sha256_file(path), 'freeplay_bytes':values, 'passed':valid})
            row['passed'] = code == 0 and all(item['passed'] for item in row['persisted'])
        except (OSError,ValueError,IndexError) as error:
            row['error'] = str(error)
        report['cases'].append(row)
        write_json(out/'report.json',report)
    report['passed'] = all(row['passed'] for row in report['cases'])
    write_json(out/'report.json',report)
    print(f"Fresh boot persistence {'PASS' if report['passed'] else 'FAIL'}: {out/'report.json'}")
    return 0 if report['passed'] else 1


if __name__ == '__main__': sys.exit(main())
