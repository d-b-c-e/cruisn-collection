"""Compare World camera state and actual ADC reads from world_motion_trace.lua.

Camera equality is a route check, not complete vehicle/physics equivalence.
Input playback equality alone does not establish that a changed game followed
the original route. Both traces must cover the same complete frame interval.
"""
import argparse
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys

from verification import sha256_file, write_json

CAMERA = ['frame', 'x', 'y', 'z', *[f'm{i}' for i in range(9)]]
ADC = ['frame', 'time', 'pc', 'value']


def read_trace(path, fields):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != fields:
            raise ValueError(f'{path}: unexpected trace columns')
        rows = list(reader)
    if not rows:
        raise ValueError(f'{path}: empty trace')
    result = []
    for row in rows:
        if None in row or any(row.get(key) is None for key in fields):
            raise ValueError(f'{path}: incomplete or extra fields')
        frame = int(row['frame'])
        if frame < 1:
            raise ValueError(f'{path}: invalid frame')
        values = [frame]
        for key in fields[1:]:
            value = Decimal(row[key]) if key == 'time' else int(row[key], 16)
            if key == 'time':
                if not value.is_finite() or value < 0:
                    raise ValueError(f'{path}: invalid time')
            elif not 0 <= value <= 0xffffffff:
                raise ValueError(f'{path}: word out of range')
            values.append(value)
        result.append(tuple(values))
    frames = [row[0] for row in result]
    if fields == CAMERA:
        if frames != list(range(frames[0], frames[-1] + 1)):
            raise ValueError(f'{path}: camera frames must be contiguous and unique')
    elif any(b[0] < a[0] or b[1] < a[1] for a, b in zip(result, result[1:])):
        raise ValueError(f'{path}: ADC events must be ordered')
    return result


def compare(reference, candidate):
    reference, candidate = Path(reference), Path(candidate)
    camera = [read_trace(p / 'world-camera.csv', CAMERA) for p in (reference, candidate)]
    adc = [read_trace(p / 'world-adc.csv', ADC) for p in (reference, candidate)]
    for poses, reads in zip(camera, adc):
        if not poses[0][0] <= reads[0][0] <= reads[-1][0] <= poses[-1][0]:
            raise ValueError('ADC events fall outside camera interval')
    camera_equal = camera[0] == camera[1]
    same_interval = (camera[0][0][0], camera[0][-1][0]) == (camera[1][0][0], camera[1][-1][0])
    differences = [a[0] for a, b in zip(*camera) if a != b]
    equal_intervals = []
    if same_interval:
        for a, b in zip(*camera):
            if a != b:
                continue
            if equal_intervals and equal_intervals[-1][1] + 1 == a[0]:
                equal_intervals[-1][1] = a[0]
            else:
                equal_intervals.append([a[0], a[0]])
    values = [[(r[0], r[2], r[3]) for r in rows] for rows in adc]
    times = [[r[1] for r in rows] for rows in adc]
    first_adc_difference = next((i for i, (a, b) in enumerate(zip(*values)) if a != b), None)
    return {
        'schema': 1, 'scope': __doc__.strip(),
        'passed': camera_equal and adc[0] == adc[1],
        'camera_equal': camera_equal, 'same_camera_interval': same_interval,
        'camera_samples': [len(rows) for rows in camera],
        'camera_intervals': [[rows[0][0], rows[-1][0]] for rows in camera],
        'first_camera_difference_frame': differences[0] if differences and same_interval else None,
        'camera_equal_frame_intervals': equal_intervals if same_interval else None,
        'camera_equal_frames': sum(last-first+1 for first,last in equal_intervals) if same_interval else None,
        'camera_match_scope': 'Camera words only; traffic, object state and rendering phase can still differ.',
        'actual_adc_reads': [len(rows) for rows in adc],
        'adc_frame_value_pc_equal': values[0] == values[1],
        'first_adc_frame_value_pc_difference': None if first_adc_difference is None else {
            'index': first_adc_difference,
            'reference': list(values[0][first_adc_difference]),
            'candidate': list(values[1][first_adc_difference]),
        },
        'adc_times_equal': times[0] == times[1],
        'first_adc_time_difference_index': next((i for i, (a, b) in enumerate(zip(*times)) if a != b), None),
        'sources': [{name: sha256_file(path / name) for name in ('world-camera.csv', 'world-adc.csv')}
                    for path in (reference, candidate)],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path, help='reference replay run directory')
    parser.add_argument('candidate', type=Path, help='candidate replay run directory')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = compare(args.reference, args.candidate)
    except (OSError, ValueError, InvalidOperation) as error:
        result = {'schema': 1, 'passed': False, 'error': str(error)}
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
