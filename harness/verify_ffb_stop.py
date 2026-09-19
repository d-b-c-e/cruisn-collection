"""Verify a device-free native stop across constant, condition and rumble sinks.

This supplements the independent force-worker conditioning verifier. It proves
software cancellation and continued-write rejection, not physical wheel behavior.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from ffb_worker import bounded_sources
from verification import sha256_file

FIELDS = 'sequence,host_seconds,family,channel,value,user_stopped'.split(',')
LIMIT = 64 * 1024 * 1024


def read_outputs(path):
    if not 0 < path.stat().st_size <= LIMIT:
        raise ValueError('output byte bound')
    result = []
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError('output columns')
        for row in reader:
            if len(result) >= 131072 or None in row or any(v is None for v in row.values()):
                raise ValueError('output record shape/bound')
            value = {key: (row[key] if key == 'family' else float(row[key])
                          if key in ('host_seconds', 'value') else int(row[key])) for key in FIELDS}
            if (value['sequence'] != len(result) + 1 or value['user_stopped'] not in (0, 1)
                    or not all(math.isfinite(value[k]) for k in ('host_seconds', 'value'))
                    or value['host_seconds'] < 0
                    or result and value['host_seconds'] < result[-1]['host_seconds']):
                raise ValueError('output clock/range/sequence')
            family, channel, amount = value['family'], value['channel'], value['value']
            if (family not in ('constant', 'condition', 'rumble', 'stop_all', 'latch', 'ack')
                    or channel not in ((0, 1, 2) if family == 'condition' else (0,))
                    or family == 'constant' and (not amount.is_integer() or abs(amount) > 32767)
                    or family == 'condition' and amount not in (0, 1)
                    or family == 'rumble' and not 0 <= amount <= 1
                    or family in ('stop_all', 'ack') and amount != 0
                    or family == 'latch' and amount != 1):
                raise ValueError('output family/range')
            result.append(value)
    return result


def verify(directory):
    root = Path(directory).resolve()
    invocation = json.loads((root/'invocation.json').read_text(encoding='utf-8'))
    env = invocation['environment']
    if (env.get('MIDV_FFB') != '0' or env.get('MIDV_FFB_OBSERVE_WORKER') != '1'
            or 'MIDV_FFB_TEST' in env or invocation.get('returncode') != 0 or invocation.get('error')):
        raise ValueError('completed device-free invocation required')
    marker = Path(env['MIDV_FFB_STOP_FILE']).resolve()
    if not marker.is_relative_to(root) or not marker.is_file():
        raise ValueError('private persisted stop marker required')
    receipt_path = root/'ffb-worker-receipt.json'
    if receipt_path.stat().st_size > 8192:
        raise ValueError('receipt bound')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if (receipt.get('complete') is not True or receipt.get('device_free') is not True
            or receipt.get('physical_output') is not False or receipt.get('user_stopped') is not True
            or any(receipt.get(k) != 0 for k in ('sink_final_level', 'sink_final_conditions', 'sink_final_rumble'))):
        raise ValueError('completed zero-output receipt required')
    names = ('ffb-worker-outputs.csv', 'ffb-worker-sources.csv', 'ffb-worker-ticks.csv')
    for name, field in zip(names, ('output_bytes', 'source_bytes', 'tick_bytes')):
        if not 0 < (root/name).stat().st_size <= LIMIT or (root/name).stat().st_size != receipt[field]:
            raise ValueError('journal extent mismatch')
    rows = read_outputs(root/names[0])
    if len(rows) != receipt['outputs']:
        raise ValueError('output count mismatch')
    latch = [r for r in rows if r['family'] == 'latch']
    ack = [r for r in rows if r['family'] == 'ack']
    if len(latch) != 1 or len(ack) != 1:
        raise ValueError('one accepted stop and acknowledgment required')
    latch, ack = latch[0], ack[0]
    if not latch['sequence'] < ack['sequence'] or not latch['host_seconds'] <= receipt['user_stop_ack_seconds'] <= ack['host_seconds']:
        raise ValueError('stop acknowledgment order')
    before = rows[:latch['sequence']-1]
    after = rows[latch['sequence']:]
    if (any(r['user_stopped'] for r in before) or not latch['user_stopped']
            or any(not r['user_stopped'] or r['value'] != 0 for r in after)
            or not any(r['family'] == 'stop_all' and r['sequence'] < ack['sequence'] for r in after)):
        raise ValueError('output restarted after stop or missing stop-all')
    for family in ('constant', 'rumble'):
        if not any(r['family'] == family and r['value'] != 0 for r in before):
            raise ValueError('missing positive '+family+' coverage')
    if {r['channel'] for r in before if r['family'] == 'condition' and r['value'] == 1} != {0, 1, 2}:
        raise ValueError('missing positive condition coverage')
    constant, conditions, rumble, rumble_at = 0, set(), 0., -1.
    for row in before:
        family = row['family']
        if family == 'constant':
            constant = row['value']
        elif family == 'condition':
            if row['value']:
                conditions.add(row['channel'])
            else:
                conditions.discard(row['channel'])
        elif family == 'rumble':
            rumble, rumble_at = row['value'], row['host_seconds']
        elif family == 'stop_all':
            constant, conditions, rumble = 0, set(), 0.
    if constant == 0 or conditions != {0, 1, 2} or rumble <= 0 or latch['host_seconds']-rumble_at >= .120:
        raise ValueError('stop must interrupt active constant, conditions and an unexpired rumble request')
    sources = bounded_sources(root/names[1])
    if len(sources) != receipt['sources']:
        raise ValueError('source count mismatch')
    later = [r for r in sources if r['host_seconds'] > ack['host_seconds'] and r['raw'] != 0]
    if not later:
        raise ValueError('no nonzero game requests after stop')
    with (root/names[2]).open(encoding='utf-8', newline='') as stream:
        ticks = []
        for row in csv.DictReader(stream):
            if len(ticks) >= 131072 or None in row or any(v is None for v in row.values()):
                raise ValueError('tick shape/bound')
            host = float(row['host_seconds'])
            if (not math.isfinite(host) or host < 0 or int(row['sequence']) != len(ticks)+1
                    or ticks and host < float(ticks[-1]['host_seconds'])):
                raise ValueError('tick clock/sequence')
            ticks.append(row)
    if len(ticks) != receipt['ticks']:
        raise ValueError('tick count mismatch')
    post = [r for r in ticks if float(r['host_seconds']) > ack['host_seconds']]
    if len(post) < 10 or float(post[-1]['host_seconds']) - ack['host_seconds'] < .1:
        raise ValueError('insufficient continued worker coverage')
    for row in post:
        if row['cancel'] != '1' or any(float(row[k]) != 0 for k in
                ('active', 'before', 'candidate', 'event', 'shaped', 'mixed', 'out', 'rumble_request')):
            raise ValueError('worker retained or regenerated force after stop')
    return dict(passed=True, physical_acceptance=False, output_requests=len(rows),
                stop_host_seconds=latch['host_seconds'], ack_host_seconds=ack['host_seconds'],
                software_ack_ms=1000*(ack['host_seconds']-latch['host_seconds']),
                nonzero_source_writes_after_stop=len(later), stopped_ticks=len(post),
                conditions=['damper', 'friction', 'spring'],
                active_constant_at_stop=constant, active_rumble_at_stop=rumble,
                hashes={name: sha256_file(root/name) for name in (*names, 'ffb-worker-receipt.json', 'invocation.json')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('refusing to replace prior evidence')
    try:
        result = verify(args.directory)
    except (OSError, ValueError, KeyError) as exc:
        result = dict(passed=False, error=str(exc), physical_acceptance=False)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
