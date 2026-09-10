"""Explicit bounded Exotica live scene observation; no drawing or product defaults."""
import csv
from pathlib import Path
import re

KEYS = ('MIDZ_HOST_FIRST', 'MIDZ_HOST_LAST', 'MIDZ_HOST_MULTIPLIER', 'MIDZ_HOST_SNAPSHOTS')


def snapshots(text):
    if text is None:
        return []
    parts = text.split(',')
    if not 1 <= len(parts) <= 16 or any(not re.fullmatch(r'[0-9]+', p) for p in parts):
        raise ValueError('invalid Exotica host snapshot list')
    values = list(map(int, parts))
    if len(set(values)) != len(values):
        raise ValueError('duplicate Exotica host snapshot')
    return values


def add_arguments(parser):
    parser.add_argument('--exotica-host-scene', choices=('off', 'observe'),
                        help='observe a private future scene at original model submission; does not draw it')
    parser.add_argument('--exotica-host-first', type=int)
    parser.add_argument('--exotica-host-last', type=int)
    parser.add_argument('--exotica-host-multiplier', type=int, choices=(1, 2, 3))
    parser.add_argument('--exotica-host-snapshots', help='up to 16 native frames; raw local RAM/WaveRAM and generated geometry')


def configure(args, rom, settings):
    mode = getattr(args, 'exotica_host_scene', None)
    values = [getattr(args, 'exotica_host_'+name, None) for name in ('first', 'last', 'multiplier', 'snapshots')]
    explicit = mode is not None
    if explicit:
        if not getattr(args, 'candidate', None):
            raise ValueError('Exotica host observation requires an explicit candidate')
    else:
        if any(v is not None for v in values):
            raise ValueError('Exotica host bounds require an explicit mode')
        inherited = settings.get('MIDZ_HOST_SCENE')
        if inherited in (None, '0'):
            return None
        if inherited != '1':
            raise ValueError('invalid recorded Exotica host mode')
        mode = 'observe'
        values = [int(settings[k]) for k in KEYS[:3]]+[settings.get(KEYS[3])]
    if rom != 'crusnexo' or mode not in ('off', 'observe'):
        raise ValueError('Exotica host observation supports Exotica2.4 only')
    if mode == 'off':
        if any(v is not None for v in values):
            raise ValueError('Exotica host off does not take bounds')
        settings['MIDZ_HOST_SCENE'] = '0'
        for key in KEYS:
            settings.pop(key, None)
        return dict(mode=mode)
    first, last, multiplier, captured = values
    multiplier = 1 if multiplier is None else multiplier
    captured = snapshots(captured)
    if (first is None or last is None or not 1800 <= first <= last <= 16000 or
            last-first > 10000 or multiplier not in (1, 2, 3) or
            any(not first <= f <= last for f in captured)):
        raise ValueError('Exotica host frame/multiplier bounds')
    if settings.get('MIDZ_UPSTREAM_RENDER', '0') != '0':
        raise ValueError('Exotica host observation currently requires legacy render policy')
    settings.update(MIDZ_HOST_SCENE='1', MIDZ_HOST_FIRST=str(first), MIDZ_HOST_LAST=str(last),
                    MIDZ_HOST_MULTIPLIER=str(multiplier))
    if captured:
        settings['MIDZ_HOST_SNAPSHOTS'] = ','.join(map(str, captured))
    else:
        settings.pop('MIDZ_HOST_SNAPSHOTS', None)
    return dict(mode=mode, first=first, last=last, multiplier=multiplier, snapshots=captured, explicit=explicit)


def verify_receipt(trial, text, directory):
    if trial is None:
        return None
    if trial['mode'] == 'off':
        if 'MIDZ_HOST_SCENE=1' in text or 'MIDZ_HOST_SCENE_RESULT' in text:
            raise ValueError('disabled Exotica host observer ran')
        return dict(disabled=True)
    pattern = r'^MIDZ_HOST_SCENE=1 first=(\d+) last=(\d+) multiplier=(\d+) snapshots=(\d+)$'
    acknowledgments = re.findall(pattern, text, re.M)
    expected = (trial['first'], trial['last'], trial['multiplier'], len(trial['snapshots']))
    if len(acknowledgments) != 1 or tuple(map(int, acknowledgments[0])) != expected:
        raise ValueError('missing or mismatched Exotica host acknowledgment')
    finals = re.findall(r'^MIDZ_HOST_SCENE_RESULT complete=(\d+) prepared=(\d+) matched=(\d+) quads=(\d+) snapshots=(\d+) pending=(\d+) remaining=(\d+)$', text, re.M)
    if len(finals) != 1:
        raise ValueError('missing Exotica host completion')
    complete, prepared, matched, quads, saved, pending, remaining = map(int, finals[0])
    if not complete or not prepared or prepared != matched or pending or remaining or saved != len(trial['snapshots']):
        raise ValueError('incomplete Exotica host observation')
    path = Path(directory)/'exotica-host-scenes.csv'
    if path.stat().st_size > 8*1024*1024:
        raise ValueError('Exotica host scene log budget')
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != matched or len(rows) > 10002 or sum(int(r['quads']) for r in rows) != quads:
        raise ValueError('Exotica host scene counts disagree')
    previous = previous_scene = -1
    for row in rows:
        frame, cpu_frame = int(row['frame']), int(row['cpu_frame'])
        delay = float(row['device_time'])-float(row['cpu_time'])
        scene, scene_frame = int(row['scene']), int(row['scene_frame'])
        preparation = float(row['cpu_time'])-float(row['scene_time'])
        if (frame < previous or scene <= previous_scene or not trial['first'] <= scene_frame <= trial['last'] or
                cpu_frame-scene_frame not in (0, 1) or frame-cpu_frame not in (0, 1) or
                not 0 <= preparation < .0176 or
                not 0 <= delay < .0176 or int(row['guest_cycles']) != 0 or
                int(row['multiplier']) != trial['multiplier'] or int(row['viewport']) > int(row['quads'])):
            raise ValueError('Exotica host clock/frame/cycle contract')
        previous, previous_scene = frame, scene
    for frame in trial['snapshots']:
        prefix = Path(directory)/f'exotica-host-{frame}'
        for suffix, size in (('-ram.bin', 0x100000), ('-wave.bin', 0x1000000)):
            if Path(str(prefix)+suffix).stat().st_size != size:
                raise ValueError('incomplete Exotica host resource snapshot')
        for suffix in ('-context.bin', '-quads.bin', '-instances.bin'):
            if not Path(str(prefix)+suffix).is_file():
                raise ValueError('missing Exotica host geometry snapshot')
    return dict(passed=True, scenes=matched, quads=quads, snapshots=saved, guest_cycles_unchanged=True, game_scene_boundary=True,
                scope='Live source/geometry observation only; independent snapshot verification is separate.')
