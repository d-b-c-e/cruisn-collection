"""Acknowledged Zeus consumer stalls and host timing analysis.

An expected timeout is a successful fault test, not a passing gameplay replay.
Original route, resources and pixels require their separate replay comparisons.
"""
import argparse
import json
from pathlib import Path
import re

from verification import sha256_file, write_json

PHASES = ('readback', 'file', 'swap', 'stall')


def configure_stall(args, rom, settings, frames):
    explicit = bool(getattr(args, 'gl_stall', None)) and rom == 'crusnexo'
    if explicit and not getattr(args, 'candidate', None):
        raise ValueError('Zeus consumer stall requires an explicit candidate')
    values = [settings.get('MIDZ_GL_STALL_' + k) for k in ('FRAME', 'MS')]
    if values == [None, None]:
        return None
    if (rom != 'crusnexo' or settings.get('MIDZ_GL') != '1' or
            getattr(args, 'headless', False) or getattr(args, 'native_renderer', False) or
            getattr(args, 'zeus_stop_frame', None) is not None):
        raise ValueError('Zeus stall requires live Exotica and cannot combine consumer faults')
    if any(not isinstance(v, str) or not re.fullmatch(r'[0-9]+', v) for v in values):
        raise ValueError('Zeus stall needs both numeric frame and milliseconds')
    frame, milliseconds = map(int, values)
    if not 1 <= frame < min(frames, 1000001) or not 1 <= milliseconds <= 5000:
        raise ValueError('Zeus stall must precede the final frame and last 1..5000 milliseconds')
    settings['MIDZ_GL_LOG'] = '1'
    return dict(frame=frame, milliseconds=milliseconds, explicit=explicit)


def verify_stall(trial, text):
    if trial is None:
        return None
    ack = re.findall(r'^MIDZ_GL_STALL frame=(\d+) milliseconds=(\d+)$', text, re.M)
    applied = re.findall(r'^MIDZ_GL_STALL_APPLIED frame=(\d+) milliseconds=(\d+) elapsed_ms=(\d+)$', text, re.M)
    expected = (trial['frame'], trial['milliseconds'])
    if len(ack) != 1 or tuple(map(int, ack[0])) != expected:
        raise ValueError('missing or conflicting Zeus stall acknowledgment')
    if len(applied) != 1 or tuple(map(int, applied[0][:2])) != expected:
        raise ValueError('requested Zeus stall was not applied exactly once at its frame')
    return dict(frame=expected[0], milliseconds=expected[1], elapsed_ms=int(applied[0][2]))


def parse_timings(text):
    lines = [line for line in text.splitlines() if line.startswith('MIDZ_GL_TIMING ')]
    if len(lines) != len(PHASES):
        raise ValueError('missing or duplicate Zeus timing completion')
    result = {}
    for line in lines:
        match = re.fullmatch(r'MIDZ_GL_TIMING phase=(\w+) calls=(\d+) total_ms=(\d+) max_ms=(\d+)', line)
        if not match:
            raise ValueError('malformed Zeus timing completion')
        phase = match[1]
        calls, total, maximum = map(int, match.groups()[1:])
        if (phase not in PHASES or phase in result or maximum > total or
                (not calls and (total or maximum)) or (calls and total > calls * maximum)):
            raise ValueError('inconsistent Zeus phase counters')
        result[phase] = dict(calls=calls, total_ms=total, max_ms=maximum,
                             mean_ms=total / calls if calls else None)
    return result


def analyze(directory, expect_timeout=False):
    directory = Path(directory)
    stderr = (directory / 'stderr.log').read_text(encoding='utf-8', errors='replace')
    stdout = (directory / 'stdout.log').read_text(encoding='utf-8', errors='replace')
    consumer = (directory / 'midz_gl.log').read_text(encoding='utf-8', errors='replace')
    timings = parse_timings(stderr)
    timeout_lines = [line for line in stderr.splitlines() if 'render stream failed: consumer timeout' in line]
    if bool(timeout_lines) != expect_timeout or len(timeout_lines) > 1:
        raise ValueError('Zeus timeout outcome differs from the explicit expectation')
    if not expect_timeout and 'render stream failed:' in stderr:
        raise ValueError('Zeus stream failed outside the requested fault test')
    waits = []
    pattern = (r'MIDZ stream wait: presented=(\d+) type=(\d+) need=(\d+) queued=(\d+) '
               r'consumer_bytes=(\d+) wait_ms=(\d+) phase=(\w+) phase_ms=(\d+)')
    for row in re.findall(pattern, stdout):
        waits.append(dict(zip(('presented', 'type', 'need', 'queued', 'consumer_bytes',
                               'wait_ms', 'phase', 'phase_ms'),
                              [int(v) if i != 6 else v for i, v in enumerate(row)])))
    slow = []
    for frame, phase, duration in re.findall(r'slow phase: completed_frame=(\d+) phase=(\w+) elapsed_ms=(\d+)', consumer):
        if phase not in timings or not 50 <= int(duration) <= timings[phase]['max_ms']:
            raise ValueError('slow phase log disagrees with completion counters')
        slow.append(dict(frame=int(frame), phase=phase, elapsed_ms=int(duration)))
    invocation = json.loads((directory / 'invocation.json').read_text())
    if invocation['environment'].get('MIDZ_GL_LOG') != '1':
        raise ValueError('Zeus phase logging was not explicitly enabled')
    if expect_timeout:
        if not waits or not re.search(r'phase=(other|readback|file|swap|stall) phase_ms=\d+$', timeout_lines[0]):
            raise ValueError('timeout is missing measured consumer phase/backpressure evidence')
    return dict(passed=True, scope=__doc__.strip(), expected_timeout=expect_timeout,
                candidate_sha256=invocation['executable_sha256'], timings=timings,
                waits=waits, slow_phases=slow, timeout_lines=timeout_lines,
                sources={name:sha256_file(directory / name) for name in
                         ('invocation.json', 'stderr.log', 'stdout.log', 'midz_gl.log')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--expect-timeout', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = analyze(args.directory, args.expect_timeout)
    except (OSError, ValueError, KeyError) as error:
        result = dict(passed=False, error=str(error))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
