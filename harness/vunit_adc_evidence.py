"""Verify V-Unit latched steering reads against recorded conversion commands.

The ADC0844 samples 40 us after the latest enabled command, not at the CPU read.
We observe bus transactions and reconstruct that pinned device contract. We do
not instrument the conversion callback or infer physical wheel angle/torque.
"""
import argparse
import bisect
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re

import steering_reconstruction as steering
from verification import sha256_file, write_json

NATIVE = '97cd738c6b89f59a7523c9494285c5ee625e9f5041622f542983d94173b37d7a'
GAMES = {'crusnusa': 24, 'crusnwld24': 16, 'offroadc': 16}
FIELDS = ['sequence', 'kind', 'frame', 'seconds', 'pc', 'data', 'mask']
DELAY = 40_000_000_000_000  # Attoseconds; ADC0844::write, native795fc.


def integer(value, low, high):
    n = int(value)
    if str(n) != str(value) or not low <= n <= high:
        raise ValueError('invalid ADC integer')
    return n


def hexword(text):
    if not re.fullmatch('[0-9a-f]{1,8}', text):
        raise ValueError('invalid ADC word')
    return int(text, 16)


def sample_interval(recording, low, high):
    points = [low, high]
    for index in range(bisect.bisect_right(recording.times, low),
                       bisect.bisect_right(recording.times, high)):
        points.extend((recording.times[index] - 1, recording.times[index]))
    values = {recording.sample(t) for t in points}
    if len(values) != 1:
        raise ValueError('ambiguous steering at conversion time')
    return values.pop()


def reconcile(rows, recording, rom, first, last):
    """Independent event fold. Unknown initial state is excluded, never assumed."""
    shift = GAMES[rom]
    control = known = 0
    pending = latch = None
    previous = Decimal('-1')
    previous_frame = first
    counts = Counter()
    consumers = Counter()
    steering_reads = []
    matched_conversions = set()
    for number, row in enumerate(rows, 1):
        if integer(row['sequence'], 1, 196608) != number:
            raise ValueError('ADC event sequence gap')
        frame = integer(row['frame'], first, last - 1)
        if frame < previous_frame:
            raise ValueError('ADC frames go backwards')
        previous_frame = frame
        low, high = steering.clock_interval(row['seconds'])
        seconds = Decimal(row['seconds'])
        if seconds < previous:
            raise ValueError('ADC clock goes backwards')
        previous = seconds
        # Permit only rounding uncertainty around the labeled frame boundary.
        if high < recording.times[frame] or low > recording.times[frame + 1]:
            raise ValueError('ADC event outside its input frame')
        data, mask = hexword(row['data']), hexword(row['mask'])
        hexword(row['pc'])
        kind = row['kind']
        if kind not in ('C', 'W', 'R'):
            raise ValueError('unknown ADC transaction')
        counts[kind] += 1
        if pending is not None:
            if low > pending['high']:
                counts['conversions_completed'] += 1
                latch = pending
                latch['value'] = (sample_interval(recording, pending['low'], pending['high'])
                                  if pending['channel'] == 4 else None)
                pending = None
            elif high >= pending['low'] and kind != 'C':
                raise ValueError('ambiguous ADC completion/event order')
            # Control writes only change access permission; they do not touch
            # the conversion timer or latch. Their order at the deadline is
            # immaterial. Defer the fold until a later, unambiguous transaction.
        if kind == 'C':
            control = ((control & ~mask) | (data & mask)) & 0xffff
            known |= mask & 0xffff
            continue
        if mask != 0xffffffff:
            raise ValueError('unsupported partial ADC access')
        flag = 0x20 if kind == 'W' else 0x40
        if not known & flag:
            counts['unknown_control_' + kind] += 1
            if kind == 'W':
                pending = latch = None
            continue
        if control & flag:
            counts['disabled_' + kind] += 1
            if kind == 'R' and data != 0xffffffff:
                raise ValueError('disabled ADC read must return all ones')
            continue
        if kind == 'W':
            channel = (data >> shift) & 15
            if channel not in (4, 5, 6, 7):
                raise ValueError('unsupported differential ADC command')
            if pending is not None:
                counts['superseded_commands'] += 1
            pending = dict(sequence=number, channel=channel, low=low + DELAY, high=high + DELAY,
                           sample_seconds=f'{seconds + Decimal("0.000040"):.12f}')
            counts['channel_' + str(channel) + '_commands'] += 1
            continue
        if latch is None:
            counts['unknown_initial_latch_reads'] += 1
            continue
        value = data >> shift
        if not 0 <= value <= 255 or data != value << shift:
            raise ValueError('invalid ADC result shift/range')
        if latch['value'] is None:
            # Non-steering first result is observed, not independently predicted.
            latch['value'] = value
        elif value != latch['value']:
            raise ValueError('latched ADC value differs from reconstructed conversion')
        if pending is not None:
            counts['reads_during_conversion'] += 1
        if latch['channel'] != 4:
            counts['nonsteering_latched_reads'] += 1
            continue
        counts['steering_reads'] += 1
        matched_conversions.add(latch['sequence'])
        consumers[row['pc']] += 1
        snapshot = recording.sample(recording.times[frame])
        steering_reads.append(dict(frame=frame, read_seconds=row['seconds'],
            sample_seconds=latch['sample_seconds'], command_sequence=latch['sequence'],
            value=value, preceding_frame_value=snapshot, frame_difference=value - snapshot))
    if not steering_reads:
        raise ValueError('no verified steering ADC reads')
    return dict(counts=dict(sorted(counts.items())), steering_conversions_read=len(matched_conversions),
                steering_consumer_pcs=dict(sorted(consumers.items())),
                pending_at_end=pending is not None,
                preceding_frame_differences=sum(r['frame_difference'] != 0 for r in steering_reads),
                maximum_frame_difference=max(abs(r['frame_difference']) for r in steering_reads),
                steering_reads=steering_reads)


def verify(run, rom):
    run = Path(run)
    if rom not in GAMES:
        raise ValueError('unsupported V-Unit game')
    inputs = steering.verify(run, rom)
    comparison = json.loads((run.parent / 'report.json').read_text()).get('comparison', {})
    if (comparison.get('passed') is not True
            or comparison.get('input_or_time_mismatches') != 0
            or comparison.get('pixel_mismatches') != 0):
        raise ValueError('requires accepted original input and native pixels')
    if inputs['executable_sha256'] != NATIVE:
        raise ValueError('ADC contract requires the pinned native795fc executable')
    probe = Path(__file__).parent / 'probes/vunit_adc.lua'
    # The first two accepted captures used the otherwise identical 131072-row
    # bound. Off Road exceeded that at frame 9008; retain those exact collectors
    # as valid predecessors, without accepting arbitrary probe substitutions.
    template = probe.read_bytes().replace(b'\r\n', b'\n')
    observed = (run / 'probe.lua').read_bytes().replace(b'\r\n', b'\n')
    limits = [limit for limit in (131072, 196608)
              if observed == template.replace(b'rows<=196608', f'rows<={limit}'.encode())]
    if len(limits) != 1:
        raise ValueError('ADC capture probe identity mismatch')
    receipt = json.loads((run / 'vunit-adc-receipt.json').read_text())
    if (receipt.get('schema') != 1 or receipt.get('game') != rom
            or receipt.get('complete') is not True or receipt.get('error') is not None
            or receipt.get('first') != 1 or receipt.get('last') != inputs['frames']):
        raise ValueError('incomplete or wrong ADC observation lifetime')
    rows = steering.csv_rows(run / 'vunit-adc.csv', FIELDS)
    if len(rows) > limits[0]:
        raise ValueError('ADC collector event budget exceeded')
    recording = steering.SteeringRecording((run / 'input/session.inp').read_bytes(), rom)
    for key, frame in (('first_seconds', 1), ('last_seconds', inputs['frames'])):
        low, high = steering.clock_interval(f'{receipt[key]:.12f}')
        if not low <= recording.times[frame] <= high:
            raise ValueError('ADC capture boundary does not join INP')
    result = reconcile(rows, recording, rom, 1, inputs['frames'])
    if (receipt['rows'] != len(rows) or any(receipt[name] != result['counts'].get(kind, 0)
            for name, kind in (('control', 'C'), ('writes', 'W'), ('reads', 'R')))):
        raise ValueError('ADC receipt count mismatch')
    return dict(schema=1, passed=True, rom=rom, input_verification=inputs, **result,
        collector_event_limit=limits[0],
        conversion_delay_microseconds=40, conversion_callback_observed=False,
        conversion_schedule_reconstructed=True, normalization_accepted=False,
        physical_angle_verified=False,
        scope='Observed ADC bus reads match INP at reconstructed conversion time. '
              'Non-steering channels only have latch-consistency checks. No host worker or wheel force validation.',
        evidence_sha256={name: sha256_file(run / name) for name in
                        ('vunit-adc.csv', 'vunit-adc-receipt.json', 'probe.lua')})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    ap.add_argument('--rom', choices=tuple(GAMES), required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        result = verify(args.run, args.rom)
    except (ValueError, KeyError, TypeError, OSError, IndexError) as exc:
        write_json(args.output / 'report.json', dict(passed=False, error=str(exc)))
        print(f'FAIL: {exc}')
        return 1
    write_json(args.output / 'report.json', result)
    print(f'PASS {args.rom}: {result["counts"]["steering_reads"]} steering reads; '
          'normalization remains unaccepted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
