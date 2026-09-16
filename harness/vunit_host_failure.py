"""Explicit pre-submission fallback trials; degraded runs never qualify parity."""
import re
from pathlib import Path

KEYS = ('MIDV_HOST_FAILURE_POLICY', 'MIDV_HOST_FAILURE_FRAME')
GAMES = {'crusnusa': 'USA', 'crusnwld24': 'WORLD', 'crusnwld': 'WORLD',
         'offroadc': 'OFFROAD'}


def add_arguments(parser):
    parser.add_argument('--vunit-host-failure', choices=('strict', 'original'),
                        help='candidate-only preparation failure policy; original latches extra scenery off')
    parser.add_argument('--vunit-host-inject-failure-frame', type=int,
                        help='fail preparation at the first qualified scene at or after this frame')


def configure(args, rom, settings, frames):
    policy = getattr(args, 'vunit_host_failure', None)
    inject = getattr(args, 'vunit_host_inject_failure_frame', None)
    # Even an inherited strict policy requires explicit acknowledgment; never
    # replay a saved fault-injection environment as an ordinary regression run.
    if policy is None:
        if inject is not None or any(k in settings for k in KEYS):
            raise ValueError('host failure controls require explicit replay selection')
        return None
    prefix = 'MIDV_' + GAMES.get(rom, 'INVALID') + '_HOST_'
    if (policy not in ('strict', 'original') or rom not in GAMES
            or not getattr(args, 'candidate', None) or getattr(args, 'headless', False)
            or getattr(args, 'native_renderer', False) or settings.get('MIDV_GL') != '1'
            or settings.get('MIDV_FFB') != '0' or settings.get(prefix+'SCENERY') != '2'):
        raise ValueError('host failure trial requires candidate V-Unit scenery draw, live GL and FFB0')
    first, last = int(settings.get(prefix+'FIRST', '0')), int(settings.get(prefix+'LAST', '0'))
    if not 1 <= first <= last < frames - 1:
        raise ValueError('host failure trial requires a bounded scene interval before drain')
    if settings.get('MIDV_HOST_BOOTSTRAP') == '1':
        first = 1  # Preparation can fail before the former capture start.
    if inject is not None and (type(inject) is not int or not first <= inject <= last):
        raise ValueError('injected failure frame outside scene interval')
    settings[KEYS[0]] = '1' if policy == 'original' else '0'
    settings.pop(KEYS[1], None)
    if inject is not None:
        settings[KEYS[1]] = str(inject)
    return dict(policy=policy, inject=inject or 0, first=first, last=last)


def verify_receipt(trial, directory):
    texts = []
    for name in ('stdout.log', 'stderr.log'):
        path = Path(directory)/name
        if not path.is_file() or path.stat().st_size > 16*1024*1024:
            raise ValueError('missing or oversized host failure receipt stream')
        texts.append(path.read_text(encoding='utf-8', errors='replace'))
    lines = [line for text in texts for line in text.splitlines()
             if line.startswith(('VUNIT_HOST_FAILURE_POLICY', 'VUNIT_HOST_PREP_FAILURE'))]
    if trial is None:
        if lines:
            raise ValueError('unrequested host preparation failure receipt')
        return None
    acks, events = [], []
    for line in lines:
        ack = re.fullmatch(r'VUNIT_HOST_FAILURE_POLICY original=([01]) inject=(\d+)', line)
        event = re.fullmatch(r'VUNIT_HOST_PREP_FAILURE frame=(\d+) stage=([1-4]) fallback=([01])', line)
        if ack:
            acks.append(tuple(map(int, ack.groups())))
        elif event:
            events.append(tuple(map(int, event.groups())))
        else:
            raise ValueError('malformed host failure receipt')
    fallback = int(trial['policy'] == 'original')
    if acks != [(fallback, trial['inject'])] or len(events) > 1:
        raise ValueError('missing, duplicated or mismatched host failure acknowledgment')
    if trial['inject'] and not events:
        raise ValueError('requested host preparation failure was not exercised')
    result = dict(degraded=False, event=None)
    if events:
        frame, stage, applied = events[0]
        if (not trial['first'] <= frame <= trial['last'] or applied != fallback
                or (trial['inject'] and (stage != 4 or frame < trial['inject']))
                or (not trial['inject'] and stage == 4)):
            raise ValueError('host preparation failure differs from requested trial')
        result.update(degraded=True, event=dict(frame=frame, stage=stage, fallback=bool(applied)))
    return result
