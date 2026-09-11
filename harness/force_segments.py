"""Time-weighted force-source coverage, before shaper/worker/device delivery.

Compare game-input conditions, not rim torque or confirmed contact-free driving.
Unknown starts/ends and stale samples are excluded instead of extrapolated.
"""
import argparse
import bisect
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import math
from pathlib import Path
import re

from verification import sha256_file, write_json

NS = 1_000_000_000
GAMES = {'usa': 'crusnusa', 'world': 'crusnwld24', 'offroad': 'offroadc', 'exotica': 'crusnexo'}
SOURCE = ['seconds', 'frame', 'raw', 'adapted']
GATE = ['seconds', 'frame', 'enabled', 'raw', 'requested_level', 'game_invert', 'device_invert']
SIGNAL = ['seconds', 'frame', 'source', 'quality', 'sample_seconds', 'sample_frame', 'value']
MAX_ROWS = 200_000


def nanoseconds(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or not 0 <= number <= 86400:
            raise ValueError('invalid emulated clock')
        return int((number * NS).to_integral_value(rounding=ROUND_HALF_UP))
    except InvalidOperation as exc:
        raise ValueError('invalid emulated clock') from exc


def integer(value, low, high):
    number = int(value)
    if str(number) != str(value) or not low <= number <= high:
        raise ValueError('invalid integer field')
    return number


def read_csv(path, fields=None, metadata=None):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('trace exceeds 64 MiB')
    with path.open(encoding='utf-8', newline='') as stream:
        comments = []

        def lines():
            for line in stream:
                if line.startswith('#'):
                    comments.append(line.strip())
                else:
                    yield line

        reader = csv.DictReader(lines())
        if fields is not None and reader.fieldnames != fields:
            raise ValueError(f'{path.name}: unexpected columns')
        if len(reader.fieldnames or []) != len(set(reader.fieldnames or [])):
            raise ValueError('duplicate columns')
        result = []
        for row in reader:
            if None in row or any(value is None or value == '' for value in row.values()):
                raise ValueError('malformed trace row')
            result.append(row)
            if len(result) > MAX_ROWS:
                raise ValueError('trace row budget exceeded')
    if not result or (metadata is not None and comments != [metadata]):
        raise ValueError(f'{path.name}: missing rows or wrong clock/provenance')
    return result


def ordered(rows, strict=False):
    if any(a['t'] > b['t'] or (strict and a['t'] == b['t']) for a, b in zip(rows, rows[1:])):
        raise ValueError('nonmonotonic trace clock')
    return rows


def parse_run(directory, game):
    directory = Path(directory)
    rom = GAMES[game]
    invocation = json.loads((directory / 'invocation.json').read_text())
    replay = json.loads((directory.parent / 'report.json').read_text())
    if (invocation['command'][1] != rom or invocation['environment'].get('MIDV_FFB') != '0'
            or replay.get('passed') is not True):
        raise ValueError('requires an accepted replay of the requested ROM with physical FFB off')
    if not re.fullmatch('[0-9a-f]{64}', invocation.get('executable_sha256', '')):
        raise ValueError('missing native executable identity')
    raw = read_csv(directory / 'force-source.csv', SOURCE,
                   f'# schema=1 game={rom} units=signed_motor_byte clock=emulated')
    gates = read_csv(directory / 'force-gate.csv', GATE)
    if len(raw) != len(gates):
        raise ValueError('source/gate length mismatch')
    force = []
    for row, gate in zip(raw, gates):
        if any(row[k] != gate[k] for k in ('seconds', 'frame', 'raw')):
            raise ValueError('source/gate event mismatch')
        adapted = integer(row['adapted'], -127, 127)
        original = integer(row['raw'], -128, 127)
        enabled = integer(gate['enabled'], 0, 1)
        invert = integer(gate['game_invert'], 0, 1) ^ integer(gate['device_invert'], 0, 1)
        magnitude = math.floor(min(1, abs(adapted) / 126) * 32767 + .5)
        expected = (-magnitude if ((adapted > 0) != bool(invert)) else magnitude) if enabled else 0
        request = integer(gate['requested_level'], -32767, 32767)
        if request != expected or (original == -128 and adapted != 0):
            raise ValueError('force adapter/polarity/neutral mismatch')
        force.append(dict(t=nanoseconds(row['seconds']), frame=integer(row['frame'], 0, MAX_ROWS),
                          raw=original, adapted=adapted, enabled=enabled, request=request / 32767))
    ordered(force)
    if any(a['frame'] > b['frame'] for a, b in zip(force, force[1:])):
        raise ValueError('source frames go backwards')

    frames = []
    key = ':ANALOG3' if game == 'exotica' else ':WHEEL'
    for n, row in enumerate(read_csv(directory / 'frames.csv'), 1):
        if integer(row['frame'], 1, MAX_ROWS) != n:
            raise ValueError('input frames must be contiguous')
        frames.append(dict(t=nanoseconds(row['emulated_seconds']), frame=n,
                           steer=(integer(row[key], 16, 240) - 128) / 112))
    ordered(frames, strict=True)
    for n, row in enumerate(frames):
        row['velocity'] = None if n == 0 else ((row['steer'] - frames[n-1]['steer']) * NS /
                                                (row['t'] - frames[n-1]['t']))

    speeds = []
    for row in read_csv(directory / 'signals.csv', SIGNAL,
                        '# schema=1 clock=emulated signal=speed unit=metres_per_second'):
        t, sample = nanoseconds(row['seconds']), nanoseconds(row['sample_seconds'])
        value = float(row['value'])
        frame = integer(row['frame'], 0, MAX_ROWS)
        sample_frame = integer(row['sample_frame'], 0, MAX_ROWS)
        if not math.isfinite(value) or not 0 <= value <= 200 or sample > t or sample_frame > frame:
            raise ValueError('invalid speed sample')
        if frame >= len(frames) or abs(frames[frame]['t'] - t) > 2:
            raise ValueError('speed sample does not join its completed input frame')
        speeds.append(dict(t=t, sample=sample, value=value,
                           source=integer(row['source'], 0, 4), quality=integer(row['quality'], 0, 2)))
    ordered(speeds, strict=True)
    if len(speeds) != len(frames) or force[-1]['frame'] >= len(frames) or force[-1]['t'] > frames[-1]['t']:
        raise ValueError('incomplete input/speed/source coverage')
    files = ['invocation.json', 'force-source.csv', 'force-gate.csv', 'signals.csv', 'frames.csv']
    identity = {name: sha256_file(directory / name) for name in files}
    identity['replay-report.json'] = sha256_file(directory.parent / 'report.json')
    env = invocation['environment']
    settings = {k: v for k, v in env.items() if ('FFB' in k or 'STEER' in k) and 'TRACE' not in k}
    return force, frames, speeds, {'inputs': identity, 'executable_sha256': invocation['executable_sha256'],
                                  'rom': rom, 'recorded_settings': settings}


def condition(speed, steer, velocity):
    speed_band = next((f'{a}-{b}' for a, b in ((10, 20), (20, 30), (30, 40), (40, 60), (60, 90))
                       if a <= speed < b), None)
    if speed_band is None:
        return None
    angle = 'center' if abs(steer) < .05 else (
        ('negative' if steer < 0 else 'positive') + '-' +
        ('small' if abs(steer) < .2 else 'medium' if abs(steer) < .5 else 'large'))
    motion = ('steady' if abs(velocity) <= .25 else 'slow' if abs(velocity) <= 1
              else 'fast' if abs(velocity) <= 4 else 'rapid')
    return f'{speed_band}mps/{angle}/{motion}'


def segments(force, frames, speeds, allow_ocr=False, max_motor_age=.5, max_speed_age=.1):
    """Intersect held source commands and recorded input/speed intervals.

    Age caps are evidence-selection limits in emulated time, NOT a simulation
    of the host worker's watchdog. No sample is held beyond its captured end.
    """
    motor_age, speed_age = nanoseconds(max_motor_age), nanoseconds(max_speed_age)
    start = max(force[0]['t'], frames[0]['t'], speeds[0]['t'])
    end = min(force[-1]['t'], frames[-1]['t'], speeds[-1]['t'])
    if end <= start:
        raise ValueError('no common clock coverage')
    points = {start, end}
    for rows, age_key, age in ((force, 't', motor_age), (speeds, 'sample', speed_age), (frames, 't', 0)):
        for row in rows:
            points.update(t for t in (row['t'], row[age_key] + age) if start < t < end)
    points = sorted(points)
    clocks = [[r['t'] for r in rows] for rows in (force, frames, speeds)]
    accepted, excluded = [], {}
    for a, b in zip(points, points[1:]):
        motor, wheel, speed = [rows[bisect.bisect_right(times, a) - 1]
                               for rows, times in zip((force, frames, speeds), clocks)]
        reason = None
        if a - motor['t'] >= motor_age:
            reason = 'motor_age_exceeds_selection_limit'
        elif not motor['enabled']:
            reason = 'gate_disabled_at_last_motor_write'
        elif speed['source'] == 0 or speed['quality'] == 0:
            reason = 'speed_unavailable'
        elif speed['source'] not in ((1, 2, 3) if allow_ocr else (2, 3)):
            reason = 'speed_provenance_excluded'
        elif a - speed['sample'] >= speed_age:
            reason = 'speed_stale'
        elif wheel['velocity'] is None:
            reason = 'steering_velocity_unavailable'
        bucket = None if reason else condition(speed['value'], wheel['steer'], wheel['velocity'])
        if not reason and bucket is None:
            reason = 'outside_driving_speed_bands'
        if reason:
            excluded[reason] = excluded.get(reason, 0) + b - a
        else:
            accepted.append(dict(start_ns=a, end_ns=b, frame=wheel['frame'], bin=bucket,
                                 raw=motor['raw'], adapted=motor['adapted'], request=motor['request'],
                                 speed_mps=speed['value'], steer=wheel['steer'], velocity=wheel['velocity'],
                                 speed_source=speed['source']))
    if sum(row['end_ns']-row['start_ns'] for row in accepted) + sum(excluded.values()) != end-start:
        raise ValueError('coverage partition mismatch')
    return accepted, {'start_seconds': start/NS, 'end_seconds': end/NS,
                      'seconds': (end-start)/NS,
                      'excluded_seconds': {k: v/NS for k, v in sorted(excluded.items())}}


def metrics(rows):
    """Exact interval weights; duplicate writes do not increase a sample's weight."""
    total = sum(r['end_ns'] - r['start_ns'] for r in rows)
    if total <= 0:
        return {'seconds': 0}
    distribution = {}
    squared = 0
    ceiling = 0
    ceiling_run = longest_ceiling = 0
    longest = run = 0
    previous_end = None
    for row in rows:
        dt = row['end_ns'] - row['start_ns']
        value = abs(row['request'])
        distribution[value] = distribution.get(value, 0) + dt
        squared += dt * value * value
        if abs(row['adapted']) >= 126:
            ceiling += dt
            ceiling_run = ceiling_run + dt if previous_end == row['start_ns'] else dt
            longest_ceiling = max(longest_ceiling, ceiling_run)
        else:
            ceiling_run = 0
        run = run + dt if previous_end == row['start_ns'] else dt
        longest = max(longest, run)
        previous_end = row['end_ns']

    def quantile(fraction):
        cumulative = 0
        for value, weight in sorted(distribution.items()):
            cumulative += weight
            if cumulative >= total * fraction:
                return value

    return {'seconds': total/NS, 'longest_contiguous_seconds': longest/NS,
            'requested_abs_p50': quantile(.5), 'requested_abs_p90': quantile(.9),
            'requested_rms': math.sqrt(squared/total),
            'adapter_ceiling_fraction': ceiling/total,
            'adapter_longest_ceiling_seconds': longest_ceiling/NS,
            'raw_rms_byte': math.sqrt(sum((0 if r['raw']==-128 else r['raw'])**2 *
                                         (r['end_ns']-r['start_ns']) for r in rows)/total)}


def compare(runs, allow_ocr=False, minimum_seconds=2.0, world_speed_probe=False):
    if set(runs) != set(GAMES) or not math.isfinite(minimum_seconds) or minimum_seconds <= 0:
        raise ValueError('four games and a positive minimum coverage are required')
    output = {'schema': 1, 'kind': 'force-source-condition-coverage', 'passed': False,
              'normalization_accepted': False, 'physical_force': False, 'contacts_reviewed': False,
              'scope': 'Unshaped requests at motor writes; emulated-time held source and recorded game-input bins. '
                       'No host worker, asynchronous gate transitions, physical angle, shaper or device simulation.',
              'selection': {'allow_ocr': allow_ocr, 'world_speed_probe': world_speed_probe,
                            'motor_max_age_seconds': .5, 'speed_max_age_seconds': .1,
                            'minimum_seconds_per_game_per_bin': minimum_seconds}, 'games': {}}
    builds = set()
    for game, directory in runs.items():
        force, frames, speeds, identity = parse_run(directory, game)
        if game == 'world' and world_speed_probe:
            from world_speed_evidence import analyze
            speeds, identity['world_memory_speed_evidence'] = analyze(directory)
        builds.add(identity['executable_sha256'])
        rows, coverage = segments(force, frames, speeds, allow_ocr)
        groups = {}
        for row in rows:
            groups.setdefault(row['bin'], []).append(row)
        output['games'][game] = {**identity, 'coverage': coverage, 'selected': metrics(rows),
                                  'bins': {k: metrics(v) for k, v in sorted(groups.items())},
                                  'intervals': rows}
    if len(builds) != 1:
        raise ValueError('force sources must use the same native executable')
    shared = set.intersection(*(set(item['bins']) for item in output['games'].values()))
    output['common_bins'] = {key: {game: item['bins'][key] for game, item in output['games'].items()}
                             for key in sorted(shared) if all(item['bins'][key]['seconds'] >= minimum_seconds
                                                               for item in output['games'].values())}
    output['shared_condition_coverage'] = bool(output['common_bins'])
    output['calibration_blockers'] = [
        'Contacts and contact-free windows have not been reviewed.',
        'Recorded game-port steering is not verified physical rim angle; steering gain/curves differ.',
        'Post-shaper output, host timing, asynchronous gate changes and device effects remain unmeasured.',
        'Attended force acceptance remains outstanding.',
    ]
    if not output['common_bins']:
        output['calibration_blockers'].append('No four-game condition bin has the minimum selected duration.')
    if allow_ocr:
        output['calibration_blockers'].append('Exploratory report permits OCR speed; this is not independent speed verification.')
    output['passed'] = True  # The analysis ran; this is not a normalization gate.
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for game in GAMES:
        parser.add_argument('--'+game, type=Path, required=True, help='accepted replay run directory')
    parser.add_argument('--output', type=Path, required=True, help='new report directory')
    parser.add_argument('--allow-ocr', action='store_true', help='exploratory only; retain OCR provenance')
    parser.add_argument('--world-speed-probe', action='store_true',
                        help='require verified World 2.4 producer/HUD capture for analysis-only memory speed')
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        report = compare({game: getattr(args, game) for game in GAMES}, args.allow_ocr,
                         world_speed_probe=args.world_speed_probe)
        for game, item in report['games'].items():
            path = args.output / (game+'-intervals.json')
            write_json(path, {'clock': 'emulated_nanoseconds', 'intervals': item.pop('intervals')})
            item['intervals_sha256'] = sha256_file(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {'passed': False, 'normalization_accepted': False, 'error': str(exc)}
    write_json(args.output/'report.json', report)
    print(('PASS' if report['passed'] else 'FAIL') + f': {args.output / "report.json"}')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
