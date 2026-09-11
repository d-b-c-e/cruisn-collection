"""Verify bounded World 2.4 speed-producer evidence for offline force analysis.

This does not change runtime telemetry. The companion read-only probe covers
Germany frames 1000..9269; its observed MPH branch is required explicitly.
"""
import argparse
import bisect
import json
import math
from pathlib import Path
import re

from force_segments import integer, nanoseconds, ordered, parse_run, read_csv
from verification import sha256_file, write_json

PROBE = Path(__file__).parent / 'probes/world24_speed.lua'
WRITE = 'sequence,seconds,native_frame,frame,pc,mask,state,flags,player,actor,raw,display'.split(',')
HUD = 'sequence,seconds,native_frame,frame,pc,state,player,display'.split(',')
FRAME = 'frame,seconds,state,flags,player,raw,display'.split(',')
MPH_FACTOR = 0.489990234375  # Exact C31 short-float operand in the observed MPYF.


def word(value):
    if not re.fullmatch('[0-9a-f]{1,8}', value):
        raise ValueError('invalid hexadecimal word')
    return int(value, 16)


def speed_word(value):
    raw = word(value)
    exponent = raw >> 24
    if exponent >= 128:
        exponent -= 256
    result = 0.0 if raw == 0x80000000 else math.ldexp(
        (-2 if raw & 0x800000 else 1) + (raw & 0x7fffff) / 8388608, exponent)
    if not math.isfinite(result) or not 0 <= result <= 400:
        raise ValueError('speed outside verified bounded domain')
    return result


def verify_rows(writes, reads, snapshots, inputs):
    """Check actual producer arithmetic, consumer holds and clock/lifetime joins."""
    if not writes or not reads or not snapshots:
        raise ValueError('missing speed evidence')
    parsed = []
    for sequence, row in enumerate(writes, 1):
        if integer(row['sequence'], 1, 20000) != sequence:
            raise ValueError('noncontiguous producer sequence')
        if word(row['pc']) != 0x1901 or word(row['mask']) != 0xffffffff:
            raise ValueError('unmapped speed producer or partial write')
        player = word(row['player'])
        if not 0x1000 <= player < 0x20000 - 0x42 or word(row['actor']) != player:
            raise ValueError('speed producer owner mismatch')
        if integer(row['state'], 0, 255) != 4:
            raise ValueError('unverified producer lifetime state')
        word(row['flags'])
        display = integer(row['display'], 0, 400)
        if math.trunc(speed_word(row['raw']) * MPH_FACTOR) != display:
            raise ValueError('producer speed conversion mismatch')
        frame = integer(row['frame'], 1, len(inputs)-1)
        t = nanoseconds(row['seconds'])
        if not inputs[frame-1]['t'] <= t < inputs[frame]['t']:
            raise ValueError('producer timestamp outside callback interval')
        parsed.append(dict(t=t, player=player, display=display,
                           native_frame=integer(row['native_frame'], 0, len(inputs))))
    ordered(parsed, strict=True)
    if any(a['native_frame'] > b['native_frame'] for a, b in zip(parsed, parsed[1:])):
        raise ValueError('producer native frames go backwards')
    clocks = [row['t'] for row in parsed]
    matched = prewindow = 0
    previous = -1
    for sequence, row in enumerate(reads, 1):
        if integer(row['sequence'], 1, 20000) != sequence or word(row['pc']) != 0x9a5d:
            raise ValueError('requires contiguous observed MPH HUD reads')
        if integer(row['state'], 0, 255) not in (4, 5):
            raise ValueError('unverified HUD lifetime state')
        frame = integer(row['frame'], 1, len(inputs)-1)
        integer(row['native_frame'], 0, len(inputs))
        t = nanoseconds(row['seconds'])
        if t <= previous or not inputs[frame-1]['t'] <= t < inputs[frame]['t']:
            raise ValueError('HUD timestamp outside callback interval/order')
        previous = t
        player, display = word(row['player']), integer(row['display'], 0, 400)
        index = bisect.bisect_right(clocks, t)-1
        if index < 0:
            prewindow += 1
            continue  # No captured writer; never invent a preceding sample.
        source = parsed[index]
        if source['player'] != player or source['display'] != display:
            raise ValueError('HUD does not consume latest observed player speed')
        matched += 1
    if not matched:
        raise ValueError('no HUD read joins an observed producer')

    by_frame = {}
    previous = None
    for row in snapshots:
        frame = integer(row['frame'], 1, len(inputs))
        if previous is not None and frame != previous+1:
            raise ValueError('noncontiguous speed snapshots')
        previous = frame
        t = nanoseconds(row['seconds'])
        if abs(t-inputs[frame-1]['t']) > 1:
            raise ValueError('speed snapshot does not join input time')
        speed_word(row['raw'])
        by_frame[frame] = dict(t=t, state=integer(row['state'], 0, 255),
                              flags=word(row['flags']), player=word(row['player']),
                              display=integer(row['display'], 0, 400))
    samples = []
    available = 0
    last_inactive = -1
    for frame, entry in enumerate(inputs, 1):
        t = entry['t']
        sample = dict(t=t, sample=0, value=0.0, source=0, quality=0)
        snap = by_frame.get(frame)
        index = bisect.bisect_right(clocks, t)-1
        active = snap and snap['state'] == 4 and snap['flags'] & 4
        if not active:
            last_inactive = t
        if snap and index >= 0:
            source = parsed[index]
            if active and source['t'] > last_inactive and snap['player'] == source['player']:
                if snap['display'] != source['display']:
                    raise ValueError('snapshot speed differs from latest observed producer')
                sample.update(sample=source['t'], value=source['display']*.44704, source=3, quality=1)
                available += 1
        samples.append(sample)
    return samples, dict(producer_events=len(parsed), hud_reads=len(reads),
                         matched_hud_reads=matched, uncaptured_writer_reads=prewindow,
                         snapshot_samples=len(snapshots), available_speed_samples=available)


def analyze(directory):
    directory = Path(directory)
    _, inputs, _, identity = parse_run(directory, 'world')
    replay = json.loads((directory.parent/'report.json').read_text())
    probe_hash = sha256_file(PROBE)
    if sha256_file(directory/'probe.lua') != probe_hash or replay.get('probe_script', {}).get('sha256') != probe_hash:
        raise ValueError('speed probe does not match the guarded canonical collector')
    receipt = json.loads((directory/'world-speed-receipt.json').read_text())
    if (receipt.get('schema') != 1 or receipt.get('game') != 'crusnwld24' or
            receipt.get('complete') is not True or receipt.get('error') is not None or
            receipt.get('first') != 1000 or receipt.get('last') != 9269 or len(inputs) != 9269):
        raise ValueError('incomplete bounded World 2.4 speed capture')
    writes = read_csv(directory/'world-speed-writes.csv', WRITE)
    reads = read_csv(directory/'world-speed-hud.csv', HUD)
    snapshots = read_csv(directory/'world-speed-frames.csv', FRAME)
    if ([len(writes), len(reads), len(snapshots)] != [receipt.get(k) for k in ('writes','reads','samples')]
            or len(snapshots) != 8270 or snapshots[0]['frame'] != '1000' or snapshots[-1]['frame'] != '9269'):
        raise ValueError('speed capture counts/bounds mismatch')
    samples, coverage = verify_rows(writes, reads, snapshots, inputs)
    files = ['probe.lua','world-speed-receipt.json','world-speed-writes.csv','world-speed-hud.csv','world-speed-frames.csv']
    return samples, dict(schema=1, passed=True, kind='world24-speed-producer-evidence',
                         normalization_accepted=False, physical_force=False, **coverage,
                         executable_sha256=identity['executable_sha256'],
                         inputs={**identity['inputs'], **{name:sha256_file(directory/name) for name in files}},
                         mph_factor=MPH_FACTOR,
                         scope='Observed producer and MPH HUD branch; analysis-only memory speed samples at input boundaries. '
                               'Retains actual producer age, excludes unknown writers and non-driving states. '
                               'No runtime telemetry, force tuning, physical speed or World 2.5 acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', type=Path, required=True, help='new evidence directory')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        samples, report = analyze(args.run)
        write_json(args.output/'samples.json', {'clock':'emulated_nanoseconds','samples':samples})
        report['samples_sha256'] = sha256_file(args.output/'samples.json')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = dict(passed=False, error=str(exc), normalization_accepted=False)
    write_json(args.output/'report.json', report)
    print(('PASS' if report['passed'] else 'FAIL')+f': {args.output}')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
