"""Explicit World 2.4 global-distance experiments; no launcher defaults.

Compose a checked patch with the recording's existing widescreen/terrain patch.
Keep CPU clock and pending admission independent from projection distance.
"""
from pathlib import Path
from game_patch import read_patch, combine_patches

FAR_VALUES = (80000, 100000, 160000)
CLAMPS = {0xae: 0x04e30000, 0xaf: 0x54e30000,
          0x13a: 0x04f20000, 0x13b: 0x55720000, 0x14d: 0x04f20000, 0x14e: 0x55720000,
          0x199: 0x04f20000, 0x19a: 0x55720000, 0x677: 0x04f20000, 0x678: 0x55720000}


def add_arguments(parser):
    parser.add_argument('--world-far', type=int, choices=FAR_VALUES,
                        help='explicit World 2.4 global distance trial; 80000 is the original limit')
    parser.add_argument('--world-lead', type=int, choices=range(9),
                        help='shared pending-section lookahead addition, 0..8; requires --world-far')
    parser.add_argument('--world-cpu', type=int, choices=(100, 125, 150, 200),
                        help='emulated CPU clock percent, diagnostic only; requires --world-far')


def configure(args, rom, settings):
    if args.world_far is None:
        if args.world_lead is not None or args.world_cpu is not None:
            raise ValueError('global lead/CPU experiments require --world-far')
        return None
    if rom != 'crusnwld24':
        raise ValueError('global distance experiment requires World 2.4')
    if getattr(args, 'scenery', None) not in (None, 'off') or getattr(args, 'scenery_lead', None) not in (None, 0):
        raise ValueError('global experiment cannot combine with selective scenery')
    if getattr(args, 'patch_at_frame', None) is not None:
        raise ValueError('global distance experiment cannot use a late game patch')
    trial = dict(far=args.world_far, lead=args.world_lead or 0, cpu=args.world_cpu or 100)
    settings.update(MIDV_WORLD_FAR=str(trial['far']), MIDV_WORLD_LEAD=str(trial['lead']),
                    MIDV_WORLD_CPU_PERCENT=str(trial['cpu']), MIDV_SCENERY='off', MIDV_SCENERY_LEAD='0')
    return trial


def compose(base, destination, far):
    if far not in FAR_VALUES:
        raise ValueError('unsupported global distance')
    maximum = 4999 if far == 80000 else far // 16
    entries = {0x40: (80000, far), **{a: (v | 4999, v | maximum) for a, v in CLAMPS.items()}}
    destination = Path(destination)
    delta = destination.with_name(destination.stem + '-limits.txt')
    if destination.exists() or delta.exists():
        raise FileExistsError('global distance patch evidence already exists')
    delta.write_text('# World 2.4 global distance trial; native virtual reciprocals required.\n' +
                     ''.join(f'{a:05X} {old:08X} {new:08X}\n' for a, (old, new) in sorted(entries.items())), encoding='utf-8')
    paths = ([base] if base else []) + [delta]
    combine_patches(paths, destination)
    read_patch(destination)
    return destination
