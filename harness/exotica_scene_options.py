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
    parser.add_argument('--exotica-host-bounds', choices=('off', 'on'),
                        help='cache conservative model bounds before private polygon projection')
    parser.add_argument('--exotica-host-materials', choices=('off', 'observe'),
                        help='verify private GPU texture/palette uploads without extra drawing')
    parser.add_argument('--exotica-host-material-pages', choices=('scan', 'written', 'verify'),
                        help='full scan, actual write notifications, or exact comparison of both material updates')
    parser.add_argument('--exotica-host-early-depth', choices=('off', 'on', 'verify'),
                        help='skip distant full transforms, or verify every depth against full preparation')
    parser.add_argument('--exotica-host-source-cache', choices=('off', 'on', 'verify'),
                        help='checked immutable-ROM sources, or exact comparison against a fresh rebuild')
    parser.add_argument('--exotica-host-fence', choices=('off', 'observe'),
                        help='verify the exact original command-ring completion point; no extra drawing')


def configure(args, rom, settings):
    mode = getattr(args, 'exotica_host_scene', None)
    bounds_option = getattr(args, 'exotica_host_bounds', None)
    material_option = getattr(args, 'exotica_host_materials', None)
    page_option = getattr(args, 'exotica_host_material_pages', None)
    cache_option = getattr(args, 'exotica_host_source_cache', None)
    depth_option = getattr(args, 'exotica_host_early_depth', None)
    fence_option = getattr(args, 'exotica_host_fence', None)
    values = [getattr(args, 'exotica_host_'+name, None) for name in ('first', 'last', 'multiplier', 'snapshots')]
    explicit = mode is not None
    if explicit:
        if not getattr(args, 'candidate', None):
            raise ValueError('Exotica host observation requires an explicit candidate')
    else:
        if any(v is not None for v in values) or any(v is not None for v in (bounds_option, material_option, page_option, cache_option, depth_option, fence_option)):
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
        if any(v is not None for v in values) or any(v is not None for v in (bounds_option, material_option, page_option, cache_option, depth_option, fence_option)):
            raise ValueError('Exotica host off does not take bounds')
        settings['MIDZ_HOST_SCENE'] = '0'
        for key in KEYS:
            settings.pop(key, None)
        settings.pop('MIDZ_HOST_BOUNDS', None)
        settings.pop('MIDZ_HOST_MATERIALS', None)
        settings.pop('MIDZ_HOST_MATERIAL_PAGES', None)
        settings.pop('MIDZ_HOST_SOURCE_CACHE', None)
        settings.pop('MIDZ_HOST_EARLY_DEPTH', None)
        settings.pop('MIDZ_HOST_FENCE', None)
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
    bound_setting = settings.get('MIDZ_HOST_BOUNDS', '0') if bounds_option is None else str(int(bounds_option == 'on'))
    if bound_setting not in ('0', '1'):
        raise ValueError('invalid recorded Exotica host bounds mode')
    if bounds_option is not None:
        settings['MIDZ_HOST_BOUNDS'] = bound_setting
    material_setting = settings.get('MIDZ_HOST_MATERIALS', '0') if material_option is None else str(int(material_option == 'observe'))
    if material_setting not in ('0', '1'):
        raise ValueError('invalid recorded Exotica host materials mode')
    if material_option is not None:
        settings['MIDZ_HOST_MATERIALS'] = material_setting
    page_setting = settings.get('MIDZ_HOST_MATERIAL_PAGES', '0') if page_option is None else str(('scan', 'written', 'verify').index(page_option))
    if page_setting not in ('0', '1', '2') or (page_setting != '0' and material_setting != '1'):
        raise ValueError('Exotica written pages require private material observation')
    if page_option is not None:
        settings['MIDZ_HOST_MATERIAL_PAGES'] = page_setting
    cache_setting = settings.get('MIDZ_HOST_SOURCE_CACHE', '0') if cache_option is None else str(('off', 'on', 'verify').index(cache_option))
    if cache_setting not in ('0', '1', '2'):
        raise ValueError('invalid recorded Exotica source cache mode')
    if cache_option is not None:
        settings['MIDZ_HOST_SOURCE_CACHE'] = cache_setting
    depth_setting = settings.get('MIDZ_HOST_EARLY_DEPTH', '0') if depth_option is None else str(('off', 'on', 'verify').index(depth_option))
    if depth_setting not in ('0', '1', '2'):
        raise ValueError('invalid recorded Exotica early depth mode')
    if depth_option is not None:
        settings['MIDZ_HOST_EARLY_DEPTH'] = depth_setting
    fence_setting = settings.get('MIDZ_HOST_FENCE', '0') if fence_option is None else str(int(fence_option == 'observe'))
    if fence_setting not in ('0', '1'):
        raise ValueError('invalid recorded Exotica command fence mode')
    if fence_option is not None:
        settings['MIDZ_HOST_FENCE'] = fence_setting
    settings.update(MIDZ_HOST_SCENE='1', MIDZ_HOST_FIRST=str(first), MIDZ_HOST_LAST=str(last),
                    MIDZ_HOST_MULTIPLIER=str(multiplier))
    if captured:
        settings['MIDZ_HOST_SNAPSHOTS'] = ','.join(map(str, captured))
    else:
        settings.pop('MIDZ_HOST_SNAPSHOTS', None)
    return dict(mode=mode, first=first, last=last, multiplier=multiplier, snapshots=captured,
                bounds=bound_setting == '1', materials=material_setting == '1', material_pages=int(page_setting),
                source_cache=int(cache_setting), early_depth=int(depth_setting), fence=fence_setting == '1', explicit=explicit)


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
    bounds = trial.get('bounds', False)
    if re.findall(r'^MIDZ_HOST_BOUNDS=(\d+)$', text, re.M) != (['1'] if bounds else []):
        raise ValueError('missing or mismatched Exotica bounds acknowledgment')
    materials = trial.get('materials', False)
    if re.findall(r'^MIDZ_HOST_MATERIALS=(\d+)$', text, re.M) != (['1'] if materials else []):
        raise ValueError('missing or mismatched Exotica material acknowledgment')
    pages = trial.get('material_pages', 0)
    if re.findall(r'^MIDZ_HOST_MATERIAL_PAGES=(\d+)$', text, re.M) != ([str(pages)] if pages else []):
        raise ValueError('missing or mismatched Exotica material page acknowledgment')
    depth = trial.get('early_depth', 0)
    if re.findall(r'^MIDZ_HOST_EARLY_DEPTH=(\d+)$', text, re.M) != ([str(depth)] if depth else []):
        raise ValueError('missing or mismatched Exotica early depth acknowledgment')
    cache = trial.get('source_cache', 0)
    if re.findall(r'^MIDZ_HOST_SOURCE_CACHE=(\d+)$', text, re.M) != ([str(cache)] if cache else []):
        raise ValueError('missing or mismatched Exotica source cache acknowledgment')
    finals = re.findall(r'^MIDZ_HOST_SCENE_RESULT complete=(\d+) prepared=(\d+) matched=(\d+) quads=(\d+) snapshots=(\d+) pending=(\d+) remaining=(\d+)$', text, re.M)
    if len(finals) != 1:
        raise ValueError('missing Exotica host completion')
    complete, prepared, matched, quads, saved, pending, remaining = map(int, finals[0])
    if not complete or not prepared or prepared != matched or pending or remaining or saved != len(trial['snapshots']):
        raise ValueError('incomplete Exotica host observation')
    page_result = re.findall(r'^MIDZ_HOST_MATERIAL_PAGES_RESULT mode=(\d+) verified=(\d+)$', text, re.M)
    expected_pages = [(str(pages), str(matched if pages == 2 else 0))] if pages else []
    if page_result != expected_pages:
        raise ValueError('incomplete Exotica material page comparison')
    cache_result = re.findall(r'^MIDZ_HOST_SOURCE_CACHE_RESULT mode=(\d+) verified=(\d+) hits=(\d+) misses=(\d+)$', text, re.M)
    if cache:
        if len(cache_result) != 1:
            raise ValueError('missing Exotica source cache completion')
        actual, verified, hits, misses = map(int, cache_result[0])
        if actual != cache or verified != (matched if cache == 2 else 0) or hits+misses != matched:
            raise ValueError('incomplete Exotica source cache comparison')
    elif cache_result:
        raise ValueError('disabled Exotica source cache ran')
    depth_result = re.findall(r'^MIDZ_HOST_EARLY_DEPTH_RESULT mode=(\d+) tested=(\d+) verified=(\d+) skipped=(\d+)$', text, re.M)
    if depth:
        if len(depth_result) != 1:
            raise ValueError('missing Exotica early depth completion')
        actual, tested, verified, skipped = map(int, depth_result[0])
        if (actual != depth or verified != (tested if depth == 2 else 0) or
                not 0 <= skipped <= tested or (depth == 2 and skipped)):
            raise ValueError('incomplete Exotica early depth comparison')
    elif depth_result:
        raise ValueError('disabled Exotica early depth ran')
    path = Path(directory)/'exotica-host-scenes.csv'
    if path.stat().st_size > 8*1024*1024:
        raise ValueError('Exotica host scene log budget')
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != matched or len(rows) > 10002 or sum(int(r['quads']) for r in rows) != quads:
        raise ValueError('Exotica host scene counts disagree')
    if depth:
        totals = tuple(sum(int(r[k]) for r in rows) for k in ('depth_tests', 'depth_verified', 'depth_skipped'))
        if totals != (tested, verified, skipped):
            raise ValueError('Exotica early depth totals disagree')
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
                int(row.get('bounds', '0')) != int(bounds) or
                int(row.get('source_cache', '0')) != cache or int(row.get('depth_mode', '0')) != depth or
                (bounds and not 0 <= int(row['culled_bounds']) <= 32768) or
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
    if materials:
        from zeus_host_materials import verify_live
        verify_live(directory, rows, trial['snapshots'], text)
    from exotica_fence import verify as verify_fence
    fence_result = verify_fence(directory, rows, text, trial.get('fence', False))
    return dict(passed=True, scenes=matched, quads=quads, snapshots=saved, guest_cycles_unchanged=True, game_scene_boundary=True,
                command_fence=fence_result,
                scope='Live source/geometry observation only; independent snapshot verification is separate.')
