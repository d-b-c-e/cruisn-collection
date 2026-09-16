"""Explicit USA scene-boundary activation; finite capture completion is retained."""
import hashlib
import re
from pathlib import Path

KEY = 'MIDV_HOST_BOOTSTRAP'


def add_arguments(parser):
    parser.add_argument('--vunit-bootstrap', choices=('scenes',),
                        help='candidate USA activation at the first guarded actual scene')


def configure(args, rom, settings, frames):
    mode = getattr(args, 'vunit_bootstrap', None)
    if mode is None:
        if KEY in settings:
            raise ValueError('V-Unit bootstrap requires explicit replay selection')
        return None
    prefix = 'MIDV_USA_HOST_'
    if (mode != 'scenes' or rom != 'crusnusa' or not getattr(args, 'candidate', None)
            or getattr(args, 'usa_host_scenery', None) != 'draw'
            or getattr(args, 'headless', False) or getattr(args, 'native_renderer', False)
            or settings.get('MIDV_GL') != '1' or settings.get('MIDV_FFB') != '0'
            or settings.get(prefix+'SCENERY') != '2' or settings.get(prefix+'FUTURE') != '1'
            or settings.get(prefix+'LAYER') != '3'):
        raise ValueError('V-Unit bootstrap requires explicit candidate USA future draw, both layers, live GL and FFB0')
    first, last = int(settings[prefix+'FIRST']), int(settings[prefix+'LAST'])
    if not 1 <= first <= last < frames - 1:
        raise ValueError('V-Unit bootstrap requires finite scene bounds before drain')
    settings[KEY] = '1'
    return dict(mode=mode, capture_reference_first=first, last=last)


def verify(trial, directory):
    directory = Path(directory)
    lines = []
    for name in ('stdout.log', 'stderr.log'):
        path = directory/name
        if not path.is_file() or path.stat().st_size > 16*1024*1024:
            raise ValueError('missing or oversized V-Unit bootstrap receipt stream')
        lines.extend(line for line in path.read_text(encoding='utf-8', errors='replace').splitlines()
                     if line.startswith('VUNIT_BOOTSTRAP'))
    paths = [directory/('vunit-bootstrap-'+name+'.bin') for name in ('ram', 'fast')]
    if trial is None:
        if lines or any(p.exists() for p in paths):
            raise ValueError('unrequested V-Unit bootstrap evidence')
        return None
    ack = f"VUNIT_BOOTSTRAP scenes=1 first=actual last={trial['last']}"
    events = [re.fullmatch(r'VUNIT_BOOTSTRAP_READY frame=(\d+) pc=81 address=40', line)
              for line in lines if line != ack]
    if lines.count(ack) != 1 or len(events) != 1 or events[0] is None:
        raise ValueError('missing or mismatched V-Unit bootstrap activation')
    frame = int(events[0][1])
    if not 1 <= frame <= trial['last']:
        raise ValueError('V-Unit bootstrap activation outside finite capture')
    snapshots = {}
    for path, size in zip(paths, (0x80000, 0x2000)):
        if not path.is_file() or path.stat().st_size != size:
            raise ValueError('missing or truncated V-Unit bootstrap operands')
        snapshots[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    from analyze_usa_host import evidence
    scenes, _, summary = evidence(directory, retain_geometry=False)
    if not scenes or int(scenes[0]['frame']) != frame or any(
            not frame <= int(s['frame']) <= trial['last'] or s['future_enabled'] != '1'
            or s['mode'] != '2' for s in scenes):
        raise ValueError('V-Unit bootstrap does not match prepared scene coverage')
    return dict(verified=True, first=frame, last_prepared=int(scenes[-1]['frame']),
                scenes=len(scenes), snapshots=snapshots)
