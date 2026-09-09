"""Check bounded USA allocation evidence; raw source operands must stay local."""
import argparse
import json
from pathlib import Path

from usa_sections import check_record
from verification import sha256_file, write_json


def check(run):
    path = run/'usa-sections.jsonl'
    receipt = json.loads((run/'usa-section-capture.json').read_text())
    records = [json.loads(line) for line in path.read_text().splitlines()]
    if (receipt.get('schema') != 1 or receipt.get('complete') is not True or not records
            or len(records) != receipt['objects']
            or [r['serial'] for r in records] != list(range(1, len(records)+1))
            or any(not receipt['first'] <= r['frame'] <= receipt['last'] for r in records)):
        raise ValueError('empty, incomplete or unbounded USA section capture')
    failures = []
    eligible = custom = palettes = 0
    for row in records:
        checks = check_record(row)
        if checks is None:
            custom += 1
            continue
        eligible += 1
        palettes += int('palette' in checks)
        if not all(checks.values()):
            failures.append(dict(serial=row['serial'], frame=row['frame'], checks=checks))
    return dict(schema=1, passed=eligible > 0 and not failures, objects=len(records), eligible=eligible,
                custom=custom, palettes=palettes, sections=len({r['section_pointer'] for r in records}),
                headings=len({r['heading'] for r in records}),
                offsets=sum(bool(r['section_flags'] & 8) for r in records), failures=failures,
                sources={p.name: sha256_file(p) for p in (path, run/'usa-section-capture.json')},
                scope='ordinary placement, membership, ready/final render fields and direct palette binding; '
                      'custom handlers, future descriptors/material lifetime and GPU visibility unproven')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path); ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        result = check(args.run)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = dict(schema=1, passed=False, error=str(error))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
