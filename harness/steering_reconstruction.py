"""Reconstruct recorded steering, including MAME's sub-frame interpolation.

This reads post-curve INP state. It does not infer physical rim angle, change
input, or accept an FFB calibration. Supported racing PADDLE ports are 16..240
with center 128; actual recorded port values must independently match.
"""
import argparse
import bisect
import csv
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
import struct
import zlib

from synthesize_input import LAYOUTS, ANALOG_LAYOUTS, STEERING
from verification import sha256_file, write_json

SECOND = 10**18
MAX_FRAMES = 200_000
MAX_BYTES = 32 * 1024 * 1024


def trunc(numerator, denominator):
    """C++ signed integer division, including negative interpolation deltas."""
    return (1 if numerator >= 0 else -1) * (abs(numerator) // denominator)


def port_value(accum, sensitivity, reverse):
    # ioport.cpp: inverse-sensitivity bounds, lround sensitivity, then 24-bit
    # fixed-point scaling with signed half-unit rounding. No curve applied here.
    bound = 65536 * 100 // sensitivity
    value = max(-bound, min(bound, accum))
    value = (1 if value >= 0 else -1) * ((abs(value) * sensitivity + 50) // 100)
    if reverse:
        value = -value
    adjust = 1 << 23 if value >= 0 else -(1 << 23)
    return trunc(value * 28672 + adjust, 1 << 24) + 128


def clock_interval(text):
    """12-place CSV time plus a conservative double/formatting uncertainty.

    Keep INP's exact attoseconds. Never silently choose whichever side of a
    rounded CSV timestamp happens to match a measured byte.
    """
    try:
        value = Decimal(text)
        if not value.is_finite() or not 0 <= value <= 86400 or value.as_tuple().exponent != -12:
            raise ValueError('requires finite, 12-place emulated seconds')
    except InvalidOperation as exc:
        raise ValueError('invalid emulated time') from exc
    center = int(value * SECOND)
    error = 1_000_000 + math.ceil(2 * math.ulp(float(value)) * SECOND)
    return center - error, center + error


class SteeringRecording:
    def __init__(self, data, rom):
        if (rom not in LAYOUTS or len(data) > MAX_BYTES or len(data) < 64
                or data[:8] != b'MAMEINP\0' or data[16:18] != b'\x03\x00'
                or data[20:32].split(b'\0')[0] != rom.encode('ascii')):
            raise ValueError('unsupported INP identity/version/size')
        offset = 16
        self.steering = STEERING[rom]
        for tag in LAYOUTS[rom]:
            offset += 8
            if tag in ANALOG_LAYOUTS[rom]:
                if tag == self.steering:
                    steering_offset = offset
                offset += 13
        decoder = zlib.decompressobj()
        try:
            payload = decoder.decompress(data[64:], MAX_BYTES + 1)
        except zlib.error as exc:
            raise ValueError('invalid INP compression') from exc
        if (len(payload) > MAX_BYTES or not decoder.eof or decoder.unused_data
                or decoder.unconsumed_tail or len(payload) % offset):
            raise ValueError('incomplete, oversized or trailing INP payload')
        count = len(payload) // offset
        if not 2 <= count <= MAX_FRAMES + 1:
            raise ValueError('unsupported INP frame count')
        self.states = []
        for at in range(0, len(payload), offset):
            sec, attos, _ = struct.unpack_from('<iqI', payload, at)
            default, digital = struct.unpack_from('<II', payload, at + steering_offset - 8)
            accum, previous, sensitivity, reverse = struct.unpack_from('<iiiB', payload, at + steering_offset)
            if (not 0 <= sec <= 86400 or not 0 <= attos < SECOND or default != 128
                    or digital != 0 or not 1 <= sensitivity <= 1000 or reverse not in (0, 1)):
                raise ValueError('unsupported steering state or clock')
            self.states.append((sec * SECOND + attos, accum, previous, sensitivity, reverse))
        self.times = [row[0] for row in self.states]
        if self.times[0] != 0 or any(b - a < 10**9 for a, b in zip(self.times, self.times[1:])):
            raise ValueError('nonmonotonic or sub-nanosecond input frames')

    def sample(self, time):
        if not self.times[0] <= time <= self.times[-1]:
            raise ValueError('sample outside captured input lifetime')
        index = bisect.bisect_right(self.times, time) - 1
        start, accum, previous, sensitivity, reverse = self.states[index]
        if index:
            delta_ns = (start - self.times[index - 1]) // 10**9
            elapsed_ns = (time - start) // 10**9
            accum = previous + trunc((accum - previous) * elapsed_ns, delta_ns)
        return port_value(accum, sensitivity, reverse)

    def sample_csv(self, text):
        low, high = clock_interval(text)
        if low < self.times[0] or high > self.times[-1]:
            raise ValueError('rounded clock crosses captured input lifetime')
        points = [low, high]
        # A tiny uncertainty interval can cross an INP update/discontinuity.
        for index in range(bisect.bisect_right(self.times, low), bisect.bisect_right(self.times, high)):
            points.extend((self.times[index] - 1, self.times[index]))
        values = {self.sample(t) for t in points}
        if len(values) != 1:
            raise ValueError('rounded clock gives ambiguous steering')
        return values.pop()


def csv_rows(path, fields=None):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('CSV exceeds size limit')
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if (not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames)
                or (fields is not None and reader.fieldnames != fields)):
            raise ValueError('invalid CSV columns')
        rows = []
        for row in reader:
            if len(rows) >= MAX_FRAMES or None in row or any(v is None or v == '' for v in row.values()):
                raise ValueError('malformed or oversized CSV')
            rows.append(row)
    if not rows:
        raise ValueError('empty CSV')
    return rows


def verify(directory, rom, exotica_adc=False):
    directory = Path(directory)
    invocation = json.loads((directory / 'invocation.json').read_text())
    replay = json.loads((directory.parent / 'report.json').read_text())
    if (replay.get('passed') is not True or invocation['command'][1] != rom
            or invocation['environment'].get('MIDV_FFB') != '0'
            or not re.fullmatch('[0-9a-f]{64}', invocation.get('executable_sha256', ''))):
        raise ValueError('requires accepted replay of requested game with physical force off')
    inp = directory / 'input/session.inp'
    if inp.stat().st_size > MAX_BYTES:
        raise ValueError('INP exceeds size limit')
    recording = SteeringRecording(inp.read_bytes(), rom)
    frames = csv_rows(directory / 'frames.csv')
    if len(frames) + 1 != len(recording.states):
        raise ValueError('frame/INP coverage mismatch')
    for number, row in enumerate(frames, 1):
        if int(row['frame']) != number:
            raise ValueError('nonconsecutive input evidence')
        low, high = clock_interval(row['emulated_seconds'])
        exact_time = recording.times[number]
        if not low <= exact_time <= high or int(row[recording.steering]) != recording.sample(exact_time):
            raise ValueError(f'frame {number}: exact input clock/port mismatch')
    inputs = ['invocation.json', 'frames.csv', 'input/session.inp']
    result = dict(passed=True, rom=rom, frames=len(frames), inp_frames=len(recording.states),
                  executable_sha256=invocation['executable_sha256'],
                  recorded_sensitivity=sorted({s[3] for s in recording.states}),
                  recorded_reverse=sorted({s[4] for s in recording.states}),
                  physical_angle_verified=False, normalization_accepted=False,
                  scope='Post-curve recorded input and interpolation; no game physics, host worker or device simulation.')
    if exotica_adc:
        if rom != 'crusnexo' or invocation['environment'].get('MIDZ_WHEEL_INVERT', '0') != '0':
            raise ValueError('ADC comparison requires unmirrored Exotica steering')
        adc = csv_rows(directory / 'exotica-adc.csv', ['frame', 'time', 'pc', 'address', 'value'])
        selected, differences = [], []
        previous_time = Decimal('-1')
        for row in adc:
            time = Decimal(row['time'])
            clock_interval(row['time'])
            if time <= previous_time:
                raise ValueError('ADC clock is not strictly ordered')
            previous_time = time
            if row['address'] not in ('9c000b', '9c000a', '9c0009'):
                raise ValueError('unexpected ADC channel')
            if row['address'] != '9c000b':
                continue
            frame = int(row['frame'])
            if not 1 <= frame < len(frames) or row['pc'] != '856c':
                raise ValueError('unsupported ADC frame/consumer')
            lo, hi = clock_interval(row['time'])
            if not recording.times[frame] < lo < hi < recording.times[frame + 1]:
                raise ValueError('ADC sample does not join its input interval')
            value = int(row['value'], 16)
            if value != recording.sample_csv(row['time']):
                raise ValueError('actual steering ADC differs from INP reconstruction')
            if selected and frame != selected[-1] + 1:
                raise ValueError('missing or duplicate steering ADC frame')
            selected.append(frame)
            differences.append(abs(value - int(frames[frame - 1][recording.steering])))
        if not selected:
            raise ValueError('no actual steering ADC samples')
        result['actual_adc'] = dict(steering_reads=len(selected), first_frame=selected[0], last_frame=selected[-1],
                                    all_matched=True, frame_snapshot_differences=sum(d != 0 for d in differences),
                                    max_frame_snapshot_difference=max(differences),
                                    coverage='Captured contiguous interval only; this does not assert full-drive ADC coverage.')
        inputs.append('exotica-adc.csv')
    result['inputs'] = {name: sha256_file(directory / name) for name in inputs}
    result['inputs']['replay-report.json'] = sha256_file(directory.parent / 'report.json')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--rom', choices=tuple(LAYOUTS), required=True)
    parser.add_argument('--exotica-adc', action='store_true')
    parser.add_argument('--output', type=Path, required=True, help='new evidence directory')
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        report = verify(args.run, args.rom, args.exotica_adc)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = dict(passed=False, normalization_accepted=False, error=str(exc))
    write_json(args.output / 'report.json', report)
    print(('PASS' if report['passed'] else 'FAIL') + f': {args.output / "report.json"}')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
