"""Explicit USA 4.5 projection/residency trials; disabled unless requested."""
from pathlib import Path
from game_patch import read_patch, combine_patches
from world_distance import FAR_VALUES

CLAMPS = {0xd0: 0x04e30000, 0xd1: 0x54e30000,
          0x157: 0x04f20000, 0x158: 0x55720000, 0x1b1: 0x04f20000, 0x1b2: 0x55720000,
          0x23b: 0x04f20000, 0x23c: 0x55720000, 0x277: 0x04e00000, 0x278: 0x55600000}


def add_arguments(parser):
    parser.add_argument('--usa-far', type=int, choices=FAR_VALUES,
                        help='USA 4.5 global distance trial; 80000 is the original limit')
    parser.add_argument('--usa-residency', type=int, choices=(0, 1),
                        help='extend active/pending depth windows (default 1); 0 is projection-only control')


def configure(args, rom, settings):
    if args.usa_far is None:
        if args.usa_residency is not None:
            raise ValueError('USA residency requires --usa-far')
        return None
    if rom != 'crusnusa':
        raise ValueError('USA global distance requires USA 4.5')
    if getattr(args, 'world_far', None) is not None or settings.get('MIDV_WORLD_FAR'):
        raise ValueError('USA and World distance adapters cannot combine')
    if getattr(args, 'patch_at_frame', None) is not None:
        raise ValueError('USA global distance cannot use a late game patch')
    trial = dict(far=args.usa_far, residency=1 if args.usa_residency is None else args.usa_residency)
    if trial['far'] not in FAR_VALUES or trial['residency'] not in (0, 1):
        raise ValueError('unsupported USA distance configuration')
    settings.update(MIDV_USA_FAR=str(trial['far']), MIDV_USA_RESIDENCY=str(trial['residency']))
    return trial


def compose(base, destination, far):
    if far not in FAR_VALUES:
        raise ValueError('unsupported USA distance')
    maximum = 4999 if far == 80000 else far // 16
    entries = {0x55: (80000, far), **{a: (v | 4999, v | maximum) for a, v in CLAMPS.items()}}
    destination = Path(destination)
    delta = destination.with_name(destination.stem + '-limits.txt')
    if destination.exists() or delta.exists():
        raise FileExistsError('USA distance patch evidence already exists')
    delta.write_text('# USA 4.5 global distance; guarded native virtual reciprocal tail required.\n' +
                     ''.join(f'{a:05X} {old:08X} {new:08X}\n' for a, (old, new) in sorted(entries.items())), encoding='utf-8')
    combine_patches(([base] if base else []) + [delta], destination)
    read_patch(destination)
    return destination
